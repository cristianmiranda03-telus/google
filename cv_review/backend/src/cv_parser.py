"""Extract text from uploaded CV files (PDF, TXT, DOCX)."""
from pathlib import Path
from typing import Union

def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    Extract plain text from a CV file.
    Supports: .pdf, .txt, .docx
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")

    if suffix == ".pdf":
        return _extract_pdf(path)

    if suffix in (".docx", ".doc"):
        return _extract_docx(path)

    raise ValueError(f"Unsupported file type: {suffix}. Use .pdf, .txt, or .docx")


def _extract_pdf(path: Path) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise ImportError("Install pypdf or PyPDF2 for PDF support: pip install pypdf")


def _extract_docx(path: Path) -> str:
    try:
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        raise ImportError("Install python-docx for DOCX support: pip install python-docx")
