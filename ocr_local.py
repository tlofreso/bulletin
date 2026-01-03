"""Local OCR using Marker (replaces Azure Document Intelligence)"""

import tempfile
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict


# Lazy-load models (they're large and take time to initialize)
_converter = None


def get_converter():
    global _converter
    if _converter is None:
        _converter = PdfConverter(artifact_dict=create_model_dict())
    return _converter


def analyze_document(f):
    """
    Analyze a PDF document and return markdown content.

    Args:
        f: File object with PDF content (must support read())

    Returns:
        dict with 'content' key containing markdown text
    """
    # Write to temp file since Marker needs a file path
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(f.read())
        tmp_path = tmp.name

    try:
        converter = get_converter()
        result = converter(tmp_path)
        return {
            'content': result.markdown,
            'metadata': result.metadata if hasattr(result, 'metadata') else {}
        }
    finally:
        import os
        os.unlink(tmp_path)


def analyze_document_read(f):
    """Alias for analyze_document (Marker doesn't distinguish layout vs read modes)"""
    return analyze_document(f)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            result = analyze_document(f)
            print(result['content'])
    else:
        print("Usage: python ocr_local.py <pdf_file>")
