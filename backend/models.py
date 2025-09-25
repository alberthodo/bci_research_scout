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

# Sprint 5 Models for Advanced Features

class TimelineData(BaseModel):
    """Timeline visualization data"""
    papers_per_year: Dict[int, int] = Field(..., description="Number of papers per year")
    keyword_trends: Dict[str, List[Dict[str, Any]]] = Field(..., description="Keyword trends over time")
    total_papers: int = Field(..., description="Total number of papers")
    year_range: Dict[str, int] = Field(..., description="Min and max years")

class ClusterPoint(BaseModel):
    """Individual point in cluster visualization"""
    id: str = Field(..., description="Paper ID")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    cluster_id: int = Field(..., description="Cluster assignment")
    title: str = Field(..., description="Paper title")
    year: int = Field(..., description="Publication year")
    keywords: List[str] = Field(..., description="Top keywords")
    citation_count: Optional[int] = Field(None, description="Citation count")

class ClusterData(BaseModel):
    """Cluster visualization data"""
    points: List[ClusterPoint] = Field(..., description="All cluster points")
    clusters: Dict[int, Dict[str, Any]] = Field(..., description="Cluster metadata")
    algorithm: str = Field(..., description="Clustering algorithm used")
    parameters: Dict[str, Any] = Field(..., description="Algorithm parameters")
    message: Optional[str] = Field(None, description="Optional message for edge cases")

class SourceInfo(BaseModel):
    """Source information for transparency"""
    name: str = Field(..., description="Source name")
    description: str = Field(..., description="Source description")
    last_updated: datetime = Field(..., description="Last update time")
    paper_count: int = Field(..., description="Number of papers from this source")
    coverage: Dict[str, Any] = Field(..., description="Coverage information")

class PromptTransparency(BaseModel):
    """Prompt transparency information"""
    system_prompt: str = Field(..., description="System prompt used")
    user_prompt_template: str = Field(..., description="User prompt template")
    parameters: Dict[str, Any] = Field(..., description="LLM parameters")
    model_info: Dict[str, str] = Field(..., description="Model information")

class ReproducibilityInfo(BaseModel):
    """Reproducibility information"""
    snapshot_id: str = Field(..., description="Unique snapshot ID")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    query: str = Field(..., description="Original query")
    parameters: Dict[str, Any] = Field(..., description="All parameters used")
    data_version: str = Field(..., description="Data version hash")
    model_version: str = Field(..., description="Model version")
