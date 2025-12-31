from enum import Enum

from pydantic import BaseModel


class FilePipelineStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class FilePipeline(BaseModel):
    task_id: int
    status: FilePipelineStatus
    # file_path: str
    # status: FilePipelineStatus
    # created_at: datetime


class PDFExtractionResponse(BaseModel):
    """Response schema for PDF extraction endpoint."""

    task_id: int
    graph_id: str
    status: FilePipelineStatus
    markdown_file_path: str
    metadata: dict
    message: str
