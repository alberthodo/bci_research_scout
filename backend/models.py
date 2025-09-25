"""
Pydantic models for the RAG BCI Literature Scout
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    """Request model for literature queries"""
    query: str = Field(..., description="Search query for BCI literature")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    sources: Optional[List[str]] = Field(None, description="Data sources to search")
    max_results: Optional[int] = Field(10, description="Maximum number of results")

class PaperMetadata(BaseModel):
    """Metadata for a research paper"""
    id: str = Field(..., description="Unique paper identifier")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(..., description="List of authors")
    year: int = Field(..., description="Publication year")
    abstract: str = Field(..., description="Paper abstract")
    url: str = Field(..., description="Paper URL")
    source: str = Field(..., description="Data source (arxiv, pubmed, etc.)")
    doi: Optional[str] = Field(None, description="DOI if available")
    citation_count: Optional[int] = Field(None, description="Number of citations")

class Claim(BaseModel):
    """A claim with supporting evidence"""
    text: str = Field(..., description="The claim text")
    confidence: float = Field(..., description="Confidence score (0-1)")
    evidence: List[str] = Field(..., description="Supporting evidence snippets")
    supporting_papers: List[str] = Field(..., description="Paper IDs that support this claim")

class TrendSummary(BaseModel):
    """Trend summary response"""
    summary: str = Field(..., description="Brief trend summary")
    claims: List[Claim] = Field(..., description="List of key claims")
    papers: List[PaperMetadata] = Field(..., description="Retrieved papers")
    timeline: Optional[Dict[str, int]] = Field(None, description="Papers per year")
    reproducibility_snapshot: Dict[str, Any] = Field(..., description="Snapshot for reproducibility")

class QueryResponse(BaseModel):
    """Response model for literature queries"""
    query: str = Field(..., description="Original query")
    summary: TrendSummary = Field(..., description="Trend summary and claims")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
