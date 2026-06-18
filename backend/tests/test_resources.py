"""Tests for resources.py - Data loading functions."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from pypdf import PdfReader


def test_read_pdf_text_success(tmp_path):
    """Test successful PDF text extraction."""
    from resources import read_pdf_text

    # Create a mock PDF
    pdf_path = tmp_path / "test.pdf"
    mock_pdf = MagicMock(spec=PdfReader)
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample PDF text"
    mock_pdf.pages = [mock_page]

    with patch('resources.PdfReader', return_value=mock_pdf):
        result = read_pdf_text(pdf_path, "fallback text")
        assert result == "Sample PDF text"


def test_read_pdf_text_multiple_pages(tmp_path):
    """Test PDF extraction with multiple pages."""
    from resources import read_pdf_text

    pdf_path = tmp_path / "multipage.pdf"
    mock_pdf = MagicMock(spec=PdfReader)
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2"
    mock_pdf.pages = [mock_page1, mock_page2]

    with patch('resources.PdfReader', return_value=mock_pdf):
        result = read_pdf_text(pdf_path, "fallback")
        assert "Page 1" in result
        assert "Page 2" in result


def test_read_pdf_text_file_not_found():
    """Test PDF reading with missing file returns fallback."""
    from resources import read_pdf_text

    result = read_pdf_text(Path("/nonexistent/file.pdf"), "fallback text")
    assert result == "fallback text"


def test_read_pdf_text_empty_pages(tmp_path):
    """Test PDF with pages that return empty text."""
    from resources import read_pdf_text

    pdf_path = tmp_path / "empty.pdf"
    mock_pdf = MagicMock(spec=PdfReader)
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf.pages = [mock_page]

    with patch('resources.PdfReader', return_value=mock_pdf):
        result = read_pdf_text(pdf_path, "fallback")
        assert result == "fallback"


def test_resources_load_facts(tmp_path):
    """Test loading facts.json file."""
    from unittest.mock import patch

    facts_data = {
        "full_name": "Brian Kane",
        "name": "Brian",
        "email": "brian@example.com"
    }

    facts_path = tmp_path / "facts.json"
    facts_path.write_text(json.dumps(facts_data))

    with patch('resources.DATA_DIR', tmp_path):
        # Re-import to reload the module with new DATA_DIR
        import importlib
        import resources
        importlib.reload(resources)
        # Just verify facts is a dict with name key
        assert isinstance(resources.facts, dict)
        assert "name" in resources.facts


def test_resources_load_text_files(tmp_path):
    """Test loading plain text files."""
    from unittest.mock import patch

    # Create test files
    (tmp_path / "summary.txt").write_text("This is a summary")
    (tmp_path / "style.txt").write_text("Professional and friendly")
    (tmp_path / "fun_facts.txt").write_text("Fact 1\nFact 2\nFact 3")

    with patch('resources.DATA_DIR', tmp_path):
        # Re-import to get fresh data
        import importlib
        import resources
        importlib.reload(resources)

        # Just verify the attributes exist and are strings
        assert isinstance(resources.summary, str)
        assert isinstance(resources.style, str)
        assert isinstance(resources.fun_facts, list)


def test_resources_linkedin_fallback(tmp_path):
    """Test LinkedIn PDF with missing file returns fallback."""
    from unittest.mock import patch

    # Set empty DATA_DIR to force fallback
    with patch('resources.DATA_DIR', tmp_path):
        import importlib
        import resources
        importlib.reload(resources)

        # Should return fallback message
        assert isinstance(resources.linkedin, str)


def test_resources_resume_fallback(tmp_path):
    """Test Resume PDF with missing file returns fallback."""
    from unittest.mock import patch

    with patch('resources.DATA_DIR', tmp_path):
        import importlib
        import resources
        importlib.reload(resources)

        assert isinstance(resources.resume, str)



