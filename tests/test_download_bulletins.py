import io
import tempfile
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from download_bulletins import download_bulletin, PARISHES_ONLINE_ROOT, PARISHES_ONLINE_FILE_FORMAT


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status_code = 200
    response.content = b'PDF content'
    return response


@pytest.fixture
def mock_failed_response():
    response = MagicMock()
    response.status_code = 404
    return response


@patch('httpx.get')
def test_download_bulletin_parishes_online_success(mock_get, mock_response):
    # Setup
    mock_get.return_value = mock_response
    file = io.BytesIO()
    parish_id = "0123"
    
    # Execute
    url = download_bulletin(parish_id, file, "PO")
    
    # Verify
    assert mock_get.called
    assert file.getvalue() == b'PDF content'
    assert PARISHES_ONLINE_ROOT in url


@patch('httpx.get')
def test_download_bulletin_not_found(mock_get, mock_failed_response):
    # Setup
    mock_get.return_value = mock_failed_response
    file = io.BytesIO()
    parish_id = "0123"
    
    # Execute and verify
    with pytest.raises(Exception, match="No bulletin found"):
        download_bulletin(parish_id, file, "PO")


@patch('httpx.get')
def test_download_bulletin_ecatholic_success(mock_get, mock_response):
    # Setup
    mock_get.return_value = mock_response
    file = io.BytesIO()
    parish_id = "someid"
    
    # Execute
    url = download_bulletin(parish_id, file, "EC")
    
    # Verify
    assert mock_get.called
    assert file.getvalue() == b'PDF content'
    assert "ecatholic.com" in url


@patch('dm_find_url.get_dm_url')
@patch('httpx.get')
def test_download_bulletin_discover_mass(mock_get, mock_dm_url, mock_response):
    # Setup
    mock_get.return_value = mock_response
    mock_dm_url.return_value = "https://discovermass.com/bulletin/someparish"
    file = io.BytesIO()
    parish_id = "someparish"
    
    # We bypass the actual URL fetching by directly returning the URL
    with patch('download_bulletins.get_dm_url', return_value="https://discovermass.com/bulletin/someparish"):
        # Execute
        url = download_bulletin(parish_id, file, "DM")
    
    # Verify
    assert mock_get.called
    assert file.getvalue() == b'PDF content'
    assert url == "https://discovermass.com/bulletin/someparish"