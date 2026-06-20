"""
Document loaders — handles .txt, .md, and .pdf files from the data directory.
"""
import os
from pathlib import Path


def load_documents(data_dir: str = "./data") -> list[dict]:
    """
    Recursively load all supported documents from the data directory.

    Returns:
        List of dicts with keys:
            - content: str  (full text of the document)
            - metadata: dict  (source, page, section)
    """
    data_path = Path(data_dir)
    documents: list[dict] = []

    if not data_path.exists():
        print(f"[WARNING] Data directory not found: {data_dir}")
        return documents

    for file_path in sorted(data_path.rglob("*")):
        if file_path.is_dir():
            continue

        suffix = file_path.suffix.lower()
        if suffix not in {".txt", ".md", ".pdf"}:
            continue

        try:
            if suffix in {".txt", ".md"}:
                docs = _load_text_file(file_path)
            elif suffix == ".pdf":
                docs = _load_pdf_file(file_path)
            else:
                continue

            documents.extend(docs)
            print(f"[LOADED] {file_path.name} — {len(docs)} section(s)")

        except Exception as exc:
            print(f"[ERROR] Failed to load {file_path.name}: {exc}")

    print(f"[INFO] Total documents loaded: {len(documents)}")
    return documents


def _load_text_file(file_path: Path) -> list[dict]:
    """Load a plain text or markdown file as a single document."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    return [
        {
            "content": content,
            "metadata": {
                "source": file_path.name,
                "page": "1",
                "section": file_path.stem.replace("_", " ").title(),
            },
        }
    ]


def _load_pdf_file(file_path: Path) -> list[dict]:
    """Load a PDF file, creating one document per page."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    docs: list[dict] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue

        docs.append(
            {
                "content": text,
                "metadata": {
                    "source": file_path.name,
                    "page": str(page_num),
                    "section": f"Page {page_num}",
                },
            }
        )

    # If extraction produced no pages, fall back to full concatenated text
    if not docs:
        full_text = ""
        for page in reader.pages:
            extracted = page.extract_text() or ""
            full_text += extracted + "\n"
        if full_text.strip():
            docs.append(
                {
                    "content": full_text.strip(),
                    "metadata": {
                        "source": file_path.name,
                        "page": "1",
                        "section": "Full Document",
                    },
                }
            )

    return docs
