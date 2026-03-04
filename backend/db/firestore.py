import json
import os
from datetime import datetime, timezone
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client

from schemas.inquiry import InquiryCreate, InquiryResponse, InquiryStatus, InquiryType

_client: Optional[Client] = None


def _build_credentials() -> credentials.Base:
    # 1. Raw JSON文字列（Render環境変数: FIREBASE_SERVICE_ACCOUNT_JSON）
    sa_json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    if sa_json_str:
        try:
            sa_dict = json.loads(sa_json_str)
            print("[firestore] JSON環境変数でサービスアカウント認証します")
            return credentials.Certificate(sa_dict)
        except Exception as e:
            print(f"[firestore] JSON環境変数のパース失敗: {e}")

    # 2. サービスアカウントJSONファイル（ローカル開発・Secret Files）
    sa_path = os.getenv("SERVICE_ACCOUNT_PATH", "")
    if sa_path and os.path.exists(sa_path):
        print(f"[firestore] ファイルでサービスアカウント認証します: {sa_path}")
        return credentials.Certificate(sa_path)

    print("[firestore] ADCにフォールバックします")
    return credentials.ApplicationDefault()


def get_firestore_client() -> Client:
    global _client
    if _client is not None:
        return _client

    project_id = os.getenv("FIREBASE_PROJECT_ID", "shiro-k")

    if not firebase_admin._apps:
        cred = _build_credentials()
        firebase_admin.initialize_app(cred, {"projectId": project_id})

    _client = firestore.client()
    return _client


def _doc_to_response(doc_id: str, data: dict) -> InquiryResponse:
    return InquiryResponse(
        id=doc_id,
        email_sender=data["email_sender"],
        email_subject=data["email_subject"],
        email_body=data["email_body"],
        email_date=data["email_date"],
        gmail_message_id=data["gmail_message_id"],
        inquiry_type=InquiryType(data["inquiry_type"]),
        reply_draft=data["reply_draft"],
        gmail_draft_id=data["gmail_draft_id"],
        status=InquiryStatus(data["status"]),
        created_at=data["created_at"],
    )


async def save_inquiry(data: InquiryCreate) -> InquiryResponse:
    db = get_firestore_client()
    now = datetime.now(timezone.utc)
    doc_data = {
        **data.model_dump(),
        "email_date": data.email_date,
        "status": InquiryStatus.draft.value,
        "created_at": now,
    }
    doc_ref = db.collection("inquiries").document()
    doc_ref.set(doc_data)
    return _doc_to_response(doc_ref.id, {**doc_data})


async def list_inquiries(
    status: Optional[str] = None,
    inquiry_type: Optional[str] = None,
    limit: int = 50,
) -> list[InquiryResponse]:
    db = get_firestore_client()
    query = db.collection("inquiries").order_by("created_at", direction=firestore.Query.DESCENDING)

    if status:
        query = query.where("status", "==", status)
    if inquiry_type:
        query = query.where("inquiry_type", "==", inquiry_type)

    query = query.limit(limit)
    docs = query.stream()
    return [_doc_to_response(doc.id, doc.to_dict()) for doc in docs]


async def get_inquiry(inquiry_id: str) -> Optional[InquiryResponse]:
    db = get_firestore_client()
    doc = db.collection("inquiries").document(inquiry_id).get()
    if not doc.exists:
        return None
    return _doc_to_response(doc.id, doc.to_dict())


async def delete_inquiry(inquiry_id: str) -> bool:
    db = get_firestore_client()
    doc_ref = db.collection("inquiries").document(inquiry_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


async def update_inquiry_status(inquiry_id: str, status: InquiryStatus) -> Optional[InquiryResponse]:
    db = get_firestore_client()
    doc_ref = db.collection("inquiries").document(inquiry_id)
    doc = doc_ref.get()
    if not doc.exists:
        return None
    doc_ref.update({"status": status.value})
    updated = doc.to_dict()
    updated["status"] = status.value
    return _doc_to_response(doc.id, updated)
