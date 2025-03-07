import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from ..database import storage
from ..models import (Document, DocumentAnswer, DocumentContent, DocumentMetadata,
                     DocumentQuestion, DocumentSummary, DocumentType,
                     DocumentUpload, ProcessingStatus)
from ..services.llm_service import llm_service
from ..services.ocr_service import ocr_service
from ..services.vector_service import vector_service

router = APIRouter(
    responses={404: {"description": "Not found"}},
)


async def process_document_task(document_id: uuid.UUID):
    """Background task to process a document"""
    try:
        # Update status to PROCESSING
        metadata = await storage.get_document_metadata(document_id)
        if not metadata:
            print(f"Document {document_id} not found")
            return
            
        metadata["status"] = ProcessingStatus.PROCESSING
        await storage.save_document_metadata(metadata)
        
        # Get PDF content
        pdf_content = await storage.get_pdf(metadata["pdf_key"])
        if not pdf_content:
            metadata["status"] = ProcessingStatus.FAILED
            await storage.save_document_metadata(metadata)
            return
            
        # Extract text with OCR
        extracted_text = await ocr_service.process_pdf(pdf_content)
        if not extracted_text:
            metadata["status"] = ProcessingStatus.FAILED
            await storage.save_document_metadata(metadata)
            return
            
        # Upload extracted text to S3
        raw_text_key = await storage.upload_text(document_id, extracted_text, "raw_text")
        if not raw_text_key:
            metadata["status"] = ProcessingStatus.FAILED
            await storage.save_document_metadata(metadata)
            return
        
        # Update metadata with raw text key
        metadata["raw_text_key"] = raw_text_key
        
        # Process document with LLM
        llm_results = await llm_service.process_document(extracted_text)
        
        # Upload processed results to S3
        summary_key = await storage.upload_text(document_id, llm_results["summary"], "summaries")
        insights_key = await storage.upload_text(document_id, llm_results["insights"], "insights")
        opportunities_key = await storage.upload_text(document_id, llm_results["opportunities"], "opportunities")
        
        # Add keys to metadata
        metadata["summary_key"] = summary_key
        metadata["insights_key"] = insights_key
        metadata["opportunities_key"] = opportunities_key
        metadata["summary"] = llm_results["summary"][:500] + "..." if len(llm_results["summary"]) > 500 else llm_results["summary"]
        
        # Index document for vector search
        chunks_indexed = await vector_service.index_document(document_id, extracted_text)
        metadata["chunks_indexed"] = chunks_indexed
        
        # Update status to COMPLETED
        metadata["status"] = ProcessingStatus.COMPLETED
        metadata["processed_at"] = datetime.utcnow().isoformat()
        await storage.save_document_metadata(metadata)
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        # Update status to FAILED
        try:
            metadata = await storage.get_document_metadata(document_id)
            if metadata:
                metadata["status"] = ProcessingStatus.FAILED
                metadata["error"] = str(e)
                await storage.save_document_metadata(metadata)
        except Exception as inner_e:
            print(f"Error updating failure status: {inner_e}")


@router.post("/upload", response_model=DocumentMetadata, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    document_type: DocumentType = Form(DocumentType.RESEARCH_PAPER),
    tags: str = Form("[]")
):
    """
    Upload a new document for processing
    
    The file will be processed asynchronously and results will be available later
    """
    # Validate input
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    try:
        # Parse tags
        import json
        tags_list = json.loads(tags)
        if not isinstance(tags_list, list):
            tags_list = []
    except:
        tags_list = []
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create document ID
        document_id = uuid.uuid4()
        
        # Generate title from filename if not provided
        if not title:
            title = file.filename.replace('.pdf', '').replace('_', ' ').title()
        
        # Upload PDF to S3
        pdf_key = await storage.upload_pdf(document_id, file_content)
        if not pdf_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload PDF"
            )
            
        # Create document metadata
        document = Document(
            id=document_id,
            title=title,
            document_type=document_type,
            pdf_key=pdf_key,
            tags=tags_list,
        )
        
        # Save metadata to DynamoDB
        metadata_dict = document.model_dump()
        await storage.save_document_metadata(metadata_dict)
        
        # Start background processing task
        background_tasks.add_task(process_document_task, document_id)
        
        # Add additional metadata for response
        metadata_dict["file_size"] = file_size
        
        return DocumentMetadata(**metadata_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentMetadata])
async def list_documents():
    """List all documents"""
    try:
        documents = await storage.list_documents()
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: uuid.UUID):
    """Get document metadata by ID"""
    try:
        document = await storage.get_document_metadata(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID):
    """Delete a document by ID"""
    try:
        # Delete from vector store first (if exists)
        await vector_service.delete_document(document_id)
        
        # Then delete from storage
        success = await storage.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/{document_id}/content", response_model=DocumentContent)
async def get_document_content(document_id: uuid.UUID):
    """Get document content (raw text and summaries)"""
    try:
        # Get metadata
        metadata = await storage.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
            
        # Check if document has been processed
        if metadata.get("status") != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not ready. Current status: {metadata.get('status')}"
            )
            
        # Get content from S3
        raw_text = await storage.get_text(metadata.get("raw_text_key"))
        summary = await storage.get_text(metadata.get("summary_key")) if "summary_key" in metadata else None
        insights = await storage.get_text(metadata.get("insights_key")) if "insights_key" in metadata else None
        opportunities = await storage.get_text(metadata.get("opportunities_key")) if "opportunities_key" in metadata else None
        
        return DocumentContent(
            id=document_id,
            raw_text=raw_text,
            summary=summary,
            insights=insights,
            opportunities=opportunities
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document content: {str(e)}"
        )


@router.post("/{document_id}/ask", response_model=DocumentAnswer)
async def ask_question(document_id: uuid.UUID, question: DocumentQuestion):
    """Ask a question about a specific document"""
    try:
        # Get metadata
        metadata = await storage.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
            
        # Check if document has been processed
        if metadata.get("status") != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not ready. Current status: {metadata.get('status')}"
            )
            
        # Query vector store
        query_results = await vector_service.query_document(
            document_id, 
            question.question,
            top_k=5
        )
        
        if not query_results:
            return DocumentAnswer(
                answer="I don't have enough information to answer this question.",
                context=[],
                sources=[]
            )
            
        # Extract context chunks
        context_chunks = [match["text"] for match in query_results]
        
        # Generate answer with LLM
        answer = await llm_service.answer_question(question.question, context_chunks)
        
        # Prepare sources
        sources = []
        for i, match in enumerate(query_results):
            sources.append({
                "chunk_id": match["chunk_id"],
                "relevance_score": f"{match['score']:.2f}"
            })
            
        return DocumentAnswer(
            answer=answer,
            context=context_chunks,
            sources=sources
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@router.get("/{document_id}/pdf", response_class=JSONResponse)
async def get_document_pdf_url(document_id: uuid.UUID):
    """Get a pre-signed URL for downloading the PDF"""
    try:
        # Get metadata
        metadata = await storage.get_document_metadata(document_id)
        if not metadata or "pdf_key" not in metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
            
        # Generate presigned URL
        presigned_url = storage.s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': storage.bucket_name,
                'Key': metadata["pdf_key"]
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        return {"url": presigned_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF URL: {str(e)}"
        )