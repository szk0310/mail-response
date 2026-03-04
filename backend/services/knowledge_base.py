import os
from pathlib import Path

import pdfplumber
import requests

DATA_DIR = Path(__file__).parent.parent / "data"
KNOWLEDGE_FILE = DATA_DIR / "company_knowledge.md"


def load_pdf_text(pdf_path: str) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def load_website_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Return raw text (basic extraction without BeautifulSoup dependency)
        return response.text
    except Exception as e:
        return f"[Webサイト取得失敗: {e}]"


def build_knowledge_base(pdf_paths: list[str] | None = None, website_urls: list[str] | None = None) -> str:
    """Build and save knowledge base from PDF files and website URLs."""
    sections: list[str] = ["# 株式会社shiro 会社情報\n"]

    if pdf_paths:
        sections.append("## 会社資料（PDF）\n")
        for path in pdf_paths:
            sections.append(f"### {Path(path).name}\n")
            sections.append(load_pdf_text(path))
            sections.append("\n")

    if website_urls:
        sections.append("## Webサイト情報\n")
        for url in website_urls:
            sections.append(f"### {url}\n")
            sections.append(load_website_text(url))
            sections.append("\n")

    knowledge_text = "\n".join(sections)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_FILE.write_text(knowledge_text, encoding="utf-8")
    return knowledge_text


def get_knowledge_base() -> str:
    """Load existing knowledge base, or return a placeholder if not yet built."""
    if KNOWLEDGE_FILE.exists():
        return KNOWLEDGE_FILE.read_text(encoding="utf-8")
    return (
        "# 株式会社shiro 会社情報\n\n"
        "※ 知識ベースがまだ構築されていません。\n"
        "build_knowledge_base() を実行して knowledge base を作成してください。\n"
    )
