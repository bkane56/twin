from pathlib import Path
import json
from pypdf import PdfReader

DATA_DIR = Path(__file__).resolve().parent / "data"


def read_pdf_text(path: Path, fallback: str) -> str:
    try:
        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts) if text_parts else fallback
    except FileNotFoundError:
        return fallback


linkedin = read_pdf_text(DATA_DIR / "linkedin.pdf", "LinkedIn profile not available")
resume = read_pdf_text(DATA_DIR / "Brian_Kane-Resume.pdf", "Resume not available")

with open(DATA_DIR / "summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

with open(DATA_DIR / "style.txt", "r", encoding="utf-8") as f:
    style = f.read()

with open(DATA_DIR / "facts.json", "r", encoding="utf-8") as f:
    facts = json.load(f)

with open(DATA_DIR / "fun_facts.txt", "r", encoding="utf-8") as f:
    fun_facts = [line.strip() for line in f if line.strip()]
    