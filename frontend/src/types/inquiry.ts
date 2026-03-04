export type InquiryType = 'service_pricing' | 'quote_request' | 'existing_client'
export type InquiryStatus = 'draft' | 'sent' | 'rejected'

export interface Inquiry {
  id: string
  email_sender: string
  email_subject: string
  email_body: string
  email_date: string
  gmail_message_id: string
  inquiry_type: InquiryType
  reply_draft: string
  gmail_draft_id: string
  status: InquiryStatus
  created_at: string
}

export const INQUIRY_TYPE_LABELS: Record<InquiryType, string> = {
  service_pricing: 'サービス・料金',
  quote_request: '見積もり依頼',
  existing_client: '既存クライアント',
}

export const INQUIRY_STATUS_LABELS: Record<InquiryStatus, string> = {
  draft: '下書き',
  sent: '送信済み',
  rejected: '却下',
}
