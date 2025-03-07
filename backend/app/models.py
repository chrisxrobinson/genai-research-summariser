from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    RESEARCH_PAPER = "RESEARCH_PAPER"
    ARTICLE = "ARTICLE"
    REPORT = "REPORT"
    OTHER = "OTHER"


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    document_type: DocumentType = DocumentType.RESEARCH_PAPER
    authors: List[str] = []
    publication_date: Optional[datetime] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    pdf_key: str  # S3 key for PDF file
    raw_text_key: Optional[str] = None  # S3 key for extracted text
    tags: List[str] = []
    
    class Config:
        use_enum_values = True


class DocumentMetadata(BaseModel):
    id: UUID
    title: str
    document_type: str
    authors: List[str]
    publication_date: Optional[datetime] = None
    upload_date: datetime
    status: str
    tags: List[str]
    summary: Optional[str] = None
    page_count: Optional[int] = None
    file_size: Optional[int] = None  # in bytes


class DocumentContent(BaseModel):
    id: UUID
    raw_text: str
    summary: Optional[str] = None
    insights: Optional[str] = None
    opportunities: Optional[str] = None


class DocumentSummary(BaseModel):
    id: UUID
    title: str
    authors: List[str]
    publication_date: Optional[datetime] = None
    upload_date: datetime
    summary: str
    tags: List[str]


class DocumentQuestion(BaseModel):
    question: str


class DocumentAnswer(BaseModel):
    answer: str
    context: List[str] = []
    sources: List[Dict[str, str]] = []


class DocumentUpload(BaseModel):
    title: Optional[str] = None
    document_type: DocumentType = DocumentType.RESEARCH_PAPER
    tags: List[str] = []
