from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class InquiryType(str, Enum):
    service_pricing = "service_pricing"
    quote_request = "quote_request"
    existing_client = "existing_client"


class InquiryStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    rejected = "rejected"


class InquiryCreate(BaseModel):
    email_sender: str
    email_subject: str
    email_body: str
    email_date: datetime
    gmail_message_id: str
    inquiry_type: InquiryType
    reply_draft: str
    gmail_draft_id: str


class InquiryResponse(InquiryCreate):
    id: str
    status: InquiryStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus
