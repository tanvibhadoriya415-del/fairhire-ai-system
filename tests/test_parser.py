import pytest
from pathlib import Path
from resume_parser import parse_resume, clean_text, extract_docx


def test_clean_text():
    raw = "Hello   world!\r\n\r\n\n\nTest   line."
    cleaned = clean_text(raw)
    assert "Hello world!" in cleaned
    assert "Test line." in cleaned
    assert "\r" not in cleaned


def test_parse_txt_resume(tmp_path):
    txt_file = tmp_path / "test_resume.txt"
    txt_file.write_text(
        "Alex Rivera\nSoftware Engineer\nalex@example.com\n\nSkills:\nPython, SQL, React, Git\n\nExperience:\n2 years at TechCorp",
        encoding="utf-8",
    )
    res = parse_resume(txt_file)
    assert res["file_name"] == "test_resume.txt"
    assert res["file_type"] == "txt"
    assert res["character_count"] > 20
    assert "Alex Rivera" in res["text"]


def test_parse_docx_resume():
    sample_path = Path("sample_resume.docx")
    if sample_path.exists():
        res = parse_resume(sample_path)
        assert res["file_type"] == "docx"
        assert "Aarav Sharma" in res["text"]
        assert "Python" in res["text"]


def test_unsupported_file_extension(tmp_path):
    bad_file = tmp_path / "resume.png"
    bad_file.write_bytes(b"\x89PNG\r\n\x1a\n...")
    with pytest.raises(ValueError, match="Only PDF, DOCX, and TXT files are supported"):
        parse_resume(bad_file)


def test_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="No text extracted"):
        parse_resume(empty_file)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_resume("non_existent_file_12345.pdf")
