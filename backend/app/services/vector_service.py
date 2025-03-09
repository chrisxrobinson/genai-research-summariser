import uuid
from typing import Dict, List

import pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import get_settings
from .llm_service import llm_service

settings = get_settings()


class VectorService:
    def __init__(self):
        # Initialize Pinecone
        self._initialize_pinecone()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        pinecone.init(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
        )
        # Create index if it doesn't exist
        if settings.pinecone_index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.embedding_dimension,
                metric="cosine",
            )
        self.index = pinecone.Index(settings.pinecone_index_name)

    async def index_document(self, document_id: uuid.UUID, text: str) -> int:
        """
        Split document text into chunks, create embeddings, and index in Pinecone
        Args:
            document_id: UUID of the document
            text: Full text content of the document
        Returns:
            Number of chunks indexed
        """
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        # Create embeddings for chunks
        embeddings = await llm_service.create_embeddings(chunks)
        # Prepare vectors for Pinecone
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}_{i}"
            vectors.append(
                {
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": {
                        "document_id": str(document_id),
                        "chunk_id": i,
                        "chunk_text": chunk[
                            :1000
                        ],  # Store first 1000 chars of text in metadata
                    },
                }
            )
        # Insert vectors in batches (Pinecone has limits)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch)
        return len(chunks)

    async def query_document(
        self, document_id: uuid.UUID, query: str, top_k: int = 5
    ) -> List[Dict]:
        """
        Query the document with a specific question
        Args:
            document_id: UUID of the document to query
            query: Query text
            top_k: Number of results to return
        Returns:
            List of retrieved chunks with metadata
        """
        # Create embedding for query
        query_embedding = await llm_service.create_embeddings([query])
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding[0],
            filter={"document_id": str(document_id)},
            top_k=top_k,
            include_metadata=True,
        )
        # Extract matches
        matches = []
        for match in results["matches"]:
            matches.append(
                {
                    "score": match["score"],
                    "chunk_id": match["metadata"]["chunk_id"],
                    "text": match["metadata"]["chunk_text"],
                    "document_id": match["metadata"]["document_id"],
                }
            )
        return matches

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """
        Delete all vectors for a document from Pinecone
        Args:
            document_id: UUID of the document
        Returns:
            Success status
        """
        try:
            # Delete by metadata filter
            self.index.delete(filter={"document_id": str(document_id)})
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False


# Initialize vector service singleton
vector_service = VectorService()
