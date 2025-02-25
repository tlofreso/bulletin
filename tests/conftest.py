import pytest
import os
import tempfile

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set environment variables for tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("BULLETIN_ASSISTANT_ID", "test_assistant")
    monkeypatch.setenv("NOTION_API_KEY", "test_notion")
    monkeypatch.setenv("PARISH_DB_ID", "test_parish_db")

@pytest.fixture
def temp_pdf_file():
    """Create a temporary file that will be deleted after test runs."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 21 >>\nstream\nBT /F1 12 Tf 100 700 Td (Test PDF) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\n0000000210 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n284\n%%EOF\n")
        tmp_name = tmp.name
    
    yield tmp_name
    
    # Clean up - delete the file after the test is done
    try:
        os.unlink(tmp_name)
    except:
        pass  # If cleanup fails, just continue

@pytest.fixture
def mock_ocr_response():
    """Return a mock OCR response."""
    return {
        "content": "Parish Bulletin\n\nSunday Mass: 8:00am, 10:00am, 12:00pm\nWeekday Masses: Monday-Friday 8:30am\n\nConfessions: Saturday 3:30pm-4:30pm\nAdoration: Wednesday 9:00am-7:00pm"
    }