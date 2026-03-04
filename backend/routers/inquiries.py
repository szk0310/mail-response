import os
from typing import Optional

from anthropic import Anthropic
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from db.firestore import (
    delete_inquiry,
    get_inquiry,
    list_inquiries,
    save_inquiry,
    update_inquiry_status,
)
from schemas.inquiry import (
    InquiryCreate,
    InquiryResponse,
    InquiryStatus,
    InquiryStatusUpdate,
    InquiryType,
)
from services.claude_agent import classify_inquiry, generate_reply
from services.gmail_client import (
    apply_processed_label,
    create_draft_reply,
    fetch_unprocessed_emails,
    get_gmail_service,
)
from services.knowledge_base import get_knowledge_base

router = APIRouter(prefix="/api")


def _process_emails_background(gmail_address: str, processed_label: str, anthropic_key: str) -> None:
    """バックグラウンドでメールを処理する（同期関数）"""
    import asyncio

    service = get_gmail_service()
    client = Anthropic(api_key=anthropic_key)
    knowledge_base = get_knowledge_base()

    emails = fetch_unprocessed_emails(service, gmail_address, processed_label)
    if not emails:
        print("[agent] 新しい問い合わせメールはありませんでした")
        return

    saved: list[str] = []
    for email_data in emails:
        try:
            inquiry_type = classify_inquiry(client, email_data["email_body"], email_data["email_subject"])
            reply_text = generate_reply(
                client,
                email_sender=email_data["email_sender"],
                email_subject=email_data["email_subject"],
                email_body=email_data["email_body"],
                inquiry_type=inquiry_type,
                knowledge_base_text=knowledge_base,
            )
            draft_id = create_draft_reply(
                service,
                original_message_id=email_data["gmail_message_id"],
                reply_text=reply_text,
                to_address=email_data["email_sender"],
                subject=email_data["email_subject"],
            )
            apply_processed_label(service, email_data["gmail_message_id"], processed_label)

            asyncio.run(save_inquiry(
                InquiryCreate(
                    email_sender=email_data["email_sender"],
                    email_subject=email_data["email_subject"],
                    email_body=email_data["email_body"],
                    email_date=email_data["email_date"],
                    gmail_message_id=email_data["gmail_message_id"],
                    inquiry_type=inquiry_type,
                    reply_draft=reply_text,
                    gmail_draft_id=draft_id,
                )
            ))
            saved.append(email_data["gmail_message_id"])
            print(f"[agent] 処理完了: {email_data['email_subject']}")
        except Exception as e:
            print(f"[agent] メール処理エラー ({email_data.get('gmail_message_id')}): {e}")

    print(f"[agent] 完了: {len(saved)} 件処理しました")


@router.post("/run", summary="Gmailスキャン・下書き作成・Firestore保存")
async def run_agent(background_tasks: BackgroundTasks) -> dict:
    gmail_address = os.getenv("GMAIL_ADDRESS", "")
    processed_label = os.getenv("PROCESSED_LABEL_NAME", "AI-Draft-Created")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not anthropic_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY が設定されていません")
    if not gmail_address:
        raise HTTPException(status_code=500, detail="GMAIL_ADDRESS が設定されていません")

    background_tasks.add_task(_process_emails_background, gmail_address, processed_label, anthropic_key)
    return {"message": "エージェントをバックグラウンドで起動しました", "processed": -1}


@router.get("/inquiries", response_model=list[InquiryResponse], summary="問い合わせ一覧")
async def get_inquiries(
    status: Optional[str] = Query(None, description="フィルター: draft / sent / rejected"),
    inquiry_type: Optional[str] = Query(None, description="フィルター: service_pricing / quote_request / existing_client"),
    limit: int = Query(50, ge=1, le=200),
) -> list[InquiryResponse]:
    try:
        return await list_inquiries(status=status, inquiry_type=inquiry_type, limit=limit)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Firestore エラー: {type(e).__name__}: {e}")


@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse, summary="問い合わせ詳細")
async def get_inquiry_detail(inquiry_id: str) -> InquiryResponse:
    record = await get_inquiry(inquiry_id)
    if not record:
        raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
    return record


@router.patch("/inquiries/{inquiry_id}/status", response_model=InquiryResponse, summary="ステータス更新")
async def update_status(inquiry_id: str, body: InquiryStatusUpdate) -> InquiryResponse:
    record = await update_inquiry_status(inquiry_id, body.status)
    if not record:
        raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
    return record


@router.delete("/inquiries/{inquiry_id}", status_code=204, summary="問い合わせ削除")
async def delete_inquiry_record(inquiry_id: str) -> None:
    deleted = await delete_inquiry(inquiry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="問い合わせが見つかりません")
