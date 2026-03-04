import base64
import email
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    import json as _json

    token_path = os.getenv("GMAIL_TOKEN_PATH", "../credentials/token.json")
    token_json_str = os.getenv("GMAIL_TOKEN_JSON", "")

    creds: Optional[Credentials] = None

    # 1. 環境変数からトークンを読み込む（Render環境）
    if token_json_str:
        try:
            creds = Credentials.from_authorized_user_info(_json.loads(token_json_str), SCOPES)
            print("[gmail] GMAIL_TOKEN_JSON 環境変数からトークンを読み込みました")
        except Exception as e:
            print(f"[gmail] GMAIL_TOKEN_JSON パース失敗: {e}")

    # 2. ファイルからトークンを読み込む（ローカル開発）
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        print(f"[gmail] ファイルからトークンを読み込みました: {token_path}")

    if not creds:
        raise RuntimeError("Gmail トークンが見つかりません。GMAIL_TOKEN_JSON 環境変数または token.json を設定してください。")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("[gmail] トークンをリフレッシュしました")
            # ローカル環境のみファイルに保存
            if not token_json_str:
                try:
                    with open(token_path, "w") as f:
                        f.write(creds.to_json())
                except OSError:
                    pass
        else:
            raise RuntimeError("Gmail トークンが無効です。token.json を再生成してください。")

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def fetch_unprocessed_emails(service, gmail_address: str, processed_label: str) -> list[dict]:
    """Fetch unread emails in INBOX that don't have the processed label."""
    try:
        # Ensure processed label exists
        label_id = _get_or_create_label(service, processed_label)

        # 本日0時 JST のUnixタイムスタンプ
        jst = timezone(timedelta(hours=9))
        today_midnight_jst = datetime.now(jst).replace(hour=0, minute=0, second=0, microsecond=0)
        after_ts = int(today_midnight_jst.timestamp())

        # Search for unread inbox messages without processed label, received today
        query = f"to:{gmail_address} is:unread in:inbox -label:{processed_label} after:{after_ts}"
        result = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
        messages = result.get("messages", [])
    except HttpError as e:
        raise RuntimeError(f"Gmail API エラー: {e}")

    emails: list[dict] = []
    for msg_meta in messages:
        msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        sender = _get_header(headers, "From")
        subject = _get_header(headers, "Subject")
        date_str = _get_header(headers, "Date")
        body = _decode_body(payload)

        try:
            email_date = email.utils.parsedate_to_datetime(date_str)
            if email_date.tzinfo is None:
                email_date = email_date.replace(tzinfo=timezone.utc)
        except Exception:
            email_date = datetime.now(timezone.utc)

        emails.append({
            "gmail_message_id": msg_meta["id"],
            "email_sender": sender,
            "email_subject": subject,
            "email_body": body,
            "email_date": email_date,
        })

    return emails


def _get_or_create_label(service, label_name: str) -> str:
    labels_result = service.users().labels().list(userId="me").execute()
    for label in labels_result.get("labels", []):
        if label["name"] == label_name:
            return label["id"]

    new_label = service.users().labels().create(
        userId="me",
        body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
    ).execute()
    return new_label["id"]


def apply_processed_label(service, message_id: str, processed_label: str) -> None:
    """Apply the processed label and mark as read."""
    label_id = _get_or_create_label(service, processed_label)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id], "removeLabelIds": ["UNREAD"]},
    ).execute()


def create_draft_reply(service, original_message_id: str, reply_text: str, to_address: str, subject: str) -> str:
    """Create a Gmail draft reply and return the draft ID."""
    raw_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    message_body = (
        f"To: {to_address}\r\n"
        f"Subject: {raw_subject}\r\n"
        f"In-Reply-To: {original_message_id}\r\n"
        f"References: {original_message_id}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"{reply_text}"
    )

    encoded = base64.urlsafe_b64encode(message_body.encode("utf-8")).decode("utf-8")

    draft = service.users().drafts().create(
        userId="me",
        body={
            "message": {
                "raw": encoded,
                "threadId": _get_thread_id(service, original_message_id),
            }
        },
    ).execute()

    return draft["id"]


def _get_thread_id(service, message_id: str) -> str:
    msg = service.users().messages().get(userId="me", id=message_id, format="minimal").execute()
    return msg.get("threadId", "")
