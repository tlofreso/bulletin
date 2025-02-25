import io
import json
import pytest
from unittest.mock import MagicMock, patch

import PyPDF2
from structured_output_extract import (
    count_pages, get_times, 
    MassTime, ConfessionTime, AdorationTime,
    MassTimes, ConfessionTimes, AdorationTimes
)


class TestCountPages:
    def test_count_pages_valid_pdf(self):
        # Create a simple PDF with 3 pages in memory
        pdf_bytes = io.BytesIO()
        writer = PyPDF2.PdfWriter()
        
        # Add 3 blank pages
        for _ in range(3):
            writer.add_blank_page(width=72, height=72)
        
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        
        # Count pages
        result = count_pages(pdf_bytes)
        
        assert result == 3
    
    def test_count_pages_invalid_pdf(self):
        # Create an invalid PDF
        pdf_bytes = io.BytesIO(b"This is not a valid PDF file")
        
        # Count pages
        result = count_pages(pdf_bytes)
        
        assert result == "0"


@pytest.fixture
def mock_openai_client():
    client = MagicMock()
    return client


@pytest.fixture
def mock_analyzed_document():
    return {
        "content": "Sunday Mass: 8:00 AM, 10:00 AM, 12:00 PM\nConfessions: Saturday 3:30-4:30 PM"
    }


@patch('structured_output_extract.analyze_document')
def test_get_times_mass(mock_analyze_document, mock_openai_client, mock_analyzed_document):
    # Setup
    mock_analyze_document.return_value = mock_analyzed_document
    
    # Mock OpenAI response
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_parsed = MassTimes(masses=[
        MassTime(day="Sunday", time=800),
        MassTime(day="Sunday", time=1000),
        MassTime(day="Sunday", time=1200)
    ])
    
    mock_message.parsed = mock_parsed
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_openai_client.beta.chat.completions.parse.return_value = mock_completion
    
    # Execute
    pdf_bytes = io.BytesIO(b"fake pdf content")
    mass_times, conf_times, adoration_times = get_times(mock_openai_client, ["mass"], pdf_bytes)
    
    # Verify
    assert mock_analyze_document.called
    assert mock_openai_client.beta.chat.completions.parse.called
    assert len(mass_times) == 3
    assert mass_times[0].day == "Sunday"
    assert mass_times[0].time == 800
    assert mass_times[1].time == 1000
    assert mass_times[2].time == 1200
    assert len(conf_times) == 0
    assert len(adoration_times) == 0


@patch('structured_output_extract.analyze_document')
def test_get_times_confession(mock_analyze_document, mock_openai_client, mock_analyzed_document):
    # Setup
    mock_analyze_document.return_value = mock_analyzed_document
    
    # Mock OpenAI response
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_parsed = ConfessionTimes(confessions=[
        ConfessionTime(day="Saturday", time=1530, duration=60)
    ])
    
    mock_message.parsed = mock_parsed
    mock_choice.message = mock_message
    mock_completion.choices = [mock_choice]
    mock_openai_client.beta.chat.completions.parse.return_value = mock_completion
    
    # Execute
    pdf_bytes = io.BytesIO(b"fake pdf content")
    mass_times, conf_times, adoration_times = get_times(mock_openai_client, ["conf"], pdf_bytes)
    
    # Verify
    assert mock_analyze_document.called
    assert mock_openai_client.beta.chat.completions.parse.called
    assert len(mass_times) == 0
    assert len(conf_times) == 1
    assert conf_times[0].day == "Saturday"
    assert conf_times[0].time == 1530
    assert conf_times[0].duration == 60
    assert len(adoration_times) == 0


@patch('structured_output_extract.analyze_document')
def test_get_times_multiple_types(mock_analyze_document, mock_openai_client, mock_analyzed_document):
    # Setup
    mock_analyze_document.return_value = mock_analyzed_document
    
    # Mock OpenAI responses for mass
    mock_mass_completion = MagicMock()
    mock_mass_choice = MagicMock()
    mock_mass_message = MagicMock()
    mock_mass_parsed = MassTimes(masses=[
        MassTime(day="Sunday", time=1000)
    ])
    
    mock_mass_message.parsed = mock_mass_parsed
    mock_mass_choice.message = mock_mass_message
    mock_mass_completion.choices = [mock_mass_choice]
    
    # Mock OpenAI responses for confession
    mock_conf_completion = MagicMock()
    mock_conf_choice = MagicMock()
    mock_conf_message = MagicMock()
    mock_conf_parsed = ConfessionTimes(confessions=[
        ConfessionTime(day="Saturday", time=1530, duration=60)
    ])
    
    mock_conf_message.parsed = mock_conf_parsed
    mock_conf_choice.message = mock_conf_message
    mock_conf_completion.choices = [mock_conf_choice]
    
    # Configure the mock to return different values for different calls
    mock_openai_client.beta.chat.completions.parse.side_effect = [
        mock_mass_completion,
        mock_conf_completion
    ]
    
    # Execute
    pdf_bytes = io.BytesIO(b"fake pdf content")
    mass_times, conf_times, adoration_times = get_times(mock_openai_client, ["mass", "conf"], pdf_bytes)
    
    # Verify
    assert mock_analyze_document.called
    assert mock_openai_client.beta.chat.completions.parse.call_count == 2
    assert len(mass_times) == 1
    assert mass_times[0].day == "Sunday"
    assert mass_times[0].time == 1000
    assert len(conf_times) == 1
    assert conf_times[0].day == "Saturday"
    assert conf_times[0].time == 1530
    assert len(adoration_times) == 0