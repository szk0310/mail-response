from anthropic import Anthropic

from schemas.inquiry import InquiryType

SIGNATURE = """
株式会社shiro
〒102-0071 東京都千代田区富士見1-3-10
E-mail: info@shiroinc.co.jp
https://shiroinc.co.jp
"""

SYSTEM_PROMPT_TEMPLATE = """あなたは株式会社shiroのメール担当者です。以下の会社情報を参照し、\
日本語で丁寧なビジネスメール返信を作成してください。
【注意】具体的な金額は記載せず、詳細は打ち合わせで確認する旨を案内すること。

## 会社情報
{knowledge_base}

## 署名
{signature}"""

CLASSIFY_PROMPT = """以下のメールを読み、問い合わせの種別を判定してください。
返答は以下の3つのうちいずれか1つのみを返してください（説明不要）:
- service_pricing  : サービス内容・料金に関する一般的な問い合わせ
- quote_request    : 見積もり依頼
- existing_client  : 既存クライアントからの問い合わせ

件名: {subject}
本文:
{body}"""


def classify_inquiry(client: Anthropic, body: str, subject: str) -> InquiryType:
    prompt = CLASSIFY_PROMPT.format(subject=subject, body=body)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip().lower()

    for inquiry_type in InquiryType:
        if inquiry_type.value in raw:
            return inquiry_type

    return InquiryType.service_pricing


def generate_reply(
    client: Anthropic,
    email_sender: str,
    email_subject: str,
    email_body: str,
    inquiry_type: InquiryType,
    knowledge_base_text: str,
) -> str:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        knowledge_base=knowledge_base_text,
        signature=SIGNATURE,
    )

    user_prompt = f"""以下のメールに対する返信文を作成してください。

差出人: {email_sender}
件名: {email_subject}
問い合わせ種別: {inquiry_type.value}

本文:
{email_body}

返信文（宛名から署名まで含む完全なメール本文）:"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()
