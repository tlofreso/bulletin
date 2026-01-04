"""FastAPI OCR server with async job processing"""

import asyncio
import concurrent.futures
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, UploadFile, HTTPException

from models import JobStatus, JobResult, JobCreate, JobResponse, HealthResponse


# In-memory job storage
jobs: Dict[str, dict] = {}
job_queue: asyncio.Queue = None
worker_task = None
thread_pool = None
converter = None


def run_ocr(pdf_bytes: bytes) -> dict:
    """Run OCR synchronously (called in thread pool)"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        result = converter(tmp_path)
        return {
            "content": result.markdown,
            "metadata": result.metadata if hasattr(result, 'metadata') else {}
        }
    finally:
        os.unlink(tmp_path)


async def process_jobs():
    """Background worker that processes OCR jobs from the queue"""
    loop = asyncio.get_event_loop()

    while True:
        job_id = await job_queue.get()
        job = jobs.get(job_id)

        if not job:
            continue

        job["status"] = JobStatus.PROCESSING

        try:
            pdf_bytes = job["pdf_data"]

            # Run blocking OCR in thread pool to avoid blocking event loop
            result = await loop.run_in_executor(thread_pool, run_ocr, pdf_bytes)

            job["result"] = JobResult(**result)
            job["status"] = JobStatus.COMPLETED

            # Clear PDF data to free memory
            del job["pdf_data"]

        except Exception as e:
            job["status"] = JobStatus.FAILED
            job["error"] = str(e)
            if "pdf_data" in job:
                del job["pdf_data"]

        job_queue.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global job_queue, worker_task, thread_pool, converter

    # Initialize Marker models (this is slow, ~2GB download on first run)
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    print("Initializing Marker models...")
    converter = PdfConverter(artifact_dict=create_model_dict())
    print("Marker models loaded")

    # Thread pool for running blocking OCR (1 worker since Marker is memory-heavy)
    thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    job_queue = asyncio.Queue()
    worker_task = asyncio.create_task(process_jobs())
    print("OCR server ready")

    yield

    worker_task.cancel()
    thread_pool.shutdown(wait=False)
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="OCR Server",
    description="PDF to Markdown OCR service using Marker",
    lifespan=lifespan
)


@app.post("/jobs", response_model=JobCreate)
async def create_job(file: UploadFile):
    """Submit a PDF for OCR processing"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4())
    pdf_data = await file.read()

    jobs[job_id] = {
        "status": JobStatus.PENDING,
        "pdf_data": pdf_data,
        "result": None,
        "error": None
    }

    await job_queue.put(job_id)

    return JobCreate(job_id=job_id)


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get the status and result of an OCR job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return JobResponse(
        job_id=job_id,
        status=job["status"],
        result=job["result"],
        error=job["error"]
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a completed job to free memory"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"deleted": True}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check server health and queue status"""
    pending = sum(1 for j in jobs.values() if j["status"] == JobStatus.PENDING)
    processing = sum(1 for j in jobs.values() if j["status"] == JobStatus.PROCESSING)

    return HealthResponse(
        status="healthy",
        jobs_pending=pending,
        jobs_processing=processing
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
