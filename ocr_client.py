"""Client for remote OCR server"""

import os
import time
from typing import Optional

import requests


class OCRClient:
    """Client for communicating with the OCR server"""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or os.environ.get("OCR_SERVER_URL", "http://localhost:8000")
        self.server_url = self.server_url.rstrip("/")
        self.poll_interval = 2  # seconds
        self.timeout = 600  # 10 minutes max

    def submit_job(self, pdf_bytes: bytes, filename: str = "document.pdf") -> str:
        """Submit a PDF for processing, returns job_id"""
        response = requests.post(
            f"{self.server_url}/jobs",
            files={"file": (filename, pdf_bytes, "application/pdf")}
        )
        response.raise_for_status()
        return response.json()["job_id"]

    def get_job(self, job_id: str) -> dict:
        """Get job status and result"""
        response = requests.get(f"{self.server_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()

    def delete_job(self, job_id: str):
        """Delete a completed job"""
        response = requests.delete(f"{self.server_url}/jobs/{job_id}")
        response.raise_for_status()

    def wait_for_result(self, job_id: str) -> dict:
        """Poll until job completes and return result"""
        start_time = time.time()

        while True:
            job = self.get_job(job_id)
            status = job["status"]

            if status == "completed":
                result = job["result"]
                self.delete_job(job_id)
                return result

            if status == "failed":
                error = job.get("error", "Unknown error")
                self.delete_job(job_id)
                raise RuntimeError(f"OCR job failed: {error}")

            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"OCR job timed out after {self.timeout} seconds")

            time.sleep(self.poll_interval)


# Module-level client instance (lazy-loaded)
_client: Optional[OCRClient] = None


def get_client() -> OCRClient:
    """Get or create the OCR client"""
    global _client
    if _client is None:
        _client = OCRClient()
    return _client


def analyze_document(f):
    """
    Analyze a PDF document via remote OCR server.

    Args:
        f: File object with PDF content (must support read())

    Returns:
        dict with 'content' key containing markdown text
    """
    client = get_client()
    pdf_bytes = f.read()
    job_id = client.submit_job(pdf_bytes)
    return client.wait_for_result(job_id)


def analyze_document_read(f):
    """Alias for analyze_document"""
    return analyze_document(f)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            result = analyze_document(f)
            print(result['content'])
    else:
        print("Usage: python ocr_client.py <pdf_file>")
        print(f"Server URL: {get_client().server_url}")
