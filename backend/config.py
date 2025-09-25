"""
Configuration settings for the RAG BCI Literature Scout
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Data Storage
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    VECTOR_STORE_PATH: str = os.path.join(DATA_DIR, "vector_store")
    METADATA_PATH: str = os.path.join(DATA_DIR, "metadata.json")
    
    # API Keys (to be configured in Sprint 3)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Vector Store Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))  # all-MiniLM-L6-v2 dimension
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "8"))
    
    # Data Sources
    ARXIV_BASE_URL: str = "http://export.arxiv.org/api/query"
    PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Global settings instance
settings = Settings()
