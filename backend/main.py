"""
RAG-based BCI Literature Scout - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any
import os
from dotenv import load_dotenv

from rag_engine.rag_pipeline import RAGPipeline
from models import QueryRequest, QueryResponse, TimelineData, ClusterData, SourceInfo
from background_fetcher import background_fetcher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG-based BCI Literature Scout",
    description="A lightweight RAG demo for BCI/Neurotech literature research",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize RAG pipeline
rag_pipeline = None

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint - health check"""
    return {"message": "RAG-based BCI Literature Scout API", "status": "healthy"}

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "rag-bci-scout"}

@app.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    from utils.cache_service import cache_service
    return cache_service.get_cache_stats()

@app.get("/background/stats")
async def get_background_stats() -> Dict[str, Any]:
    """Get background fetcher statistics"""
    return background_fetcher.get_fetch_stats()

@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline and background fetcher on startup"""
    global rag_pipeline
    try:
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline()
        logger.info("RAG pipeline initialized successfully")
        
        # Start background fetcher
        logger.info("Starting background fetcher...")
        background_fetcher.start()
        logger.info("Background fetcher started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        rag_pipeline = None

@app.post("/query", response_model=QueryResponse)
async def query_literature(request: QueryRequest) -> QueryResponse:
    """
    Main query endpoint for literature search
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503, 
            detail="RAG pipeline not initialized"
        )
    
    try:
        # Process query through RAG pipeline
        response = rag_pipeline.process_query(request)
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@app.get("/timeline", response_model=TimelineData)
async def get_timeline_data():
    """
    Get timeline data for visualization (papers per year, keyword trends)
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503, 
            detail="RAG pipeline not initialized"
        )
    
    try:
        timeline_data = rag_pipeline.get_timeline_data()
        return timeline_data
        
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting timeline data: {str(e)}"
        )

@app.get("/clusters", response_model=ClusterData)
async def get_cluster_data():
    """
    Get cluster data for visualization (UMAP/t-SNE clustering)
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503, 
            detail="RAG pipeline not initialized"
        )
    
    try:
        cluster_data = rag_pipeline.get_cluster_data()
        return cluster_data
        
    except Exception as e:
        logger.error(f"Error getting cluster data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cluster data: {str(e)}"
        )

@app.get("/sources")
async def get_sources():
    """
    Get detailed source information for transparency
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503, 
            detail="RAG pipeline not initialized"
        )
    
    try:
        sources = rag_pipeline.get_sources_info()
        return sources
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sources: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
