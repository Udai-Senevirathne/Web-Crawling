from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RAGConfig(BaseModel):
    top_k: int = Field(5, description="Number of chunks to retrieve")
    chunk_size: int = Field(1000, description="Characters per chunk")
    chunk_overlap: int = Field(200, description="Overlap between chunks")
    model: str = Field("llama-3.3-70b-versatile", description="LLM model to use")
    similarity_threshold: float = Field(0.7, description="Minimum similarity threshold")


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Client company name")
    enl_id: str = Field(..., min_length=1, description="Unique enterprise license ID")
    rag_config: Optional[RAGConfig] = Field(None, description="Client-specific RAG configuration")
    status: str = Field("active", description="Client status: active, suspended, inactive")


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Client company name")
    rag_config: Optional[RAGConfig] = Field(None, description="Client-specific RAG configuration")
    status: Optional[str] = Field(None, description="Client status: active, suspended, inactive")


class ClientOut(BaseModel):
    id: str = Field(..., description="MongoDB ObjectId as string")
    name: str = Field(..., description="Client company name")
    enl_id: str = Field(..., description="Unique enterprise license ID")
    rag_config: RAGConfig = Field(..., description="Client-specific RAG configuration")
    status: str = Field(..., description="Client status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    document_count: Optional[int] = Field(0, description="Number of ingested documents")
