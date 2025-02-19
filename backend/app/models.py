from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ResearchItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    abstract: str
    summary_key: Optional[str] = None  # S3 key for summary
    opportunities_key: Optional[str] = None  # S3 key for opportunities
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pdf_key: Optional[str] = None  # S3 key for original PDF
