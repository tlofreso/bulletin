"""Pydantic models for OCR server API"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResult(BaseModel):
    content: str
    metadata: dict = {}


class JobCreate(BaseModel):
    """Response when a job is created"""
    job_id: str


class JobResponse(BaseModel):
    """Response when querying job status"""
    job_id: str
    status: JobStatus
    result: Optional[JobResult] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    jobs_pending: int
    jobs_processing: int
