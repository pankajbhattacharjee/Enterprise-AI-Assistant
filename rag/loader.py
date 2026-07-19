from pathlib import Path
import fitz
from docx import Document as DocxDocument


def extract_text(path: Path) -> list[tuple[int | None, str]]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return [(None, path.read_text(encoding="utf-8", errors="replace"))]
    if suffix == ".pdf":
        pdf = fitz.open(path)
        try:
            return [(index + 1, page.get_text("text")) for index, page in enumerate(pdf)]
        finally:
            pdf.close()
    if suffix == ".docx":
        document = DocxDocument(path)
        return [(None, "\n".join(paragraph.text for paragraph in document.paragraphs))]
    raise ValueError(f"Unsupported document format: {suffix}")
