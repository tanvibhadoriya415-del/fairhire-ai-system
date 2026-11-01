
import argparse
import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def clean_text(text):
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path):
    reader = PdfReader(str(path))

    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported.")

    return "\n\n".join(
        page.extract_text() or "" for page in reader.pages
    )


def extract_docx(path):
    document = Document(str(path))
    sections = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            sections.append(paragraph.text)

    for table in document.tables:
        for row in table.rows:
            sections.append(
                " | ".join(cell.text.strip() for cell in row.cells)
            )

    return "\n".join(sections)


def parse_resume(file_path):
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only PDF, DOCX, and TXT files are supported.")

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 10 MB size limit.")

    if extension == ".pdf":
        raw_text = extract_pdf(path)
    elif extension == ".docx":
        raw_text = extract_docx(path)
    else:
        raw_text = path.read_text(encoding="utf-8", errors="ignore")

    text = clean_text(raw_text)

    if not text:
        raise ValueError(
            "No text extracted. The file may be scanned or image-only."
        )

    return {
        "file_name": path.name,
        "file_type": extension[1:],
        "character_count": len(text),
        "word_count": len(text.split()),
        "text": text,
        "status": "success"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF or DOCX resume."
    )
    parser.add_argument("file", help="Resume file path")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    try:
        result = parse_resume(args.file)
        output = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")
            print(f"Extraction successful: {output_path}")
        else:
            print(output)

    except (FileNotFoundError, ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()