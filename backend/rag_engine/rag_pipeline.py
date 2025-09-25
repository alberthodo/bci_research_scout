"""
Core RAG pipeline for end-to-end query processing
"""

import logging
import time
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from rag_engine.retrieval_system import RetrievalSystem
from llm_integration.gemini_client import GeminiClient
from vector_store.faiss_store import FAISSVectorStore
from models import QueryRequest, QueryResponse, TrendSummary, Claim, PaperMetadata
from config import settings

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Core RAG pipeline for processing literature queries"""
    
    def __init__(self):
        # Initialize components
        self.vector_store = FAISSVectorStore()
        self.retrieval_system = RetrievalSystem(self.vector_store)
        self.llm_client = GeminiClient()
        
        # Pipeline configuration
        self.default_top_k = settings.TOP_K_RESULTS
        self.confidence_threshold = 0.3  # Minimum confidence for claims
    
    def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a literature query through the complete RAG pipeline
        
        Args:
            request: Query request with search parameters
        
        Returns:
            Query response with trend summary and claims
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {request.query}")
            
            # Step 1: Retrieve relevant documents
            retrieved_docs = self._retrieve_documents(request)
            
            if not retrieved_docs:
                return self._empty_response(request, start_time)
            
            # Step 2: Extract evidence and generate summary
            trend_summary = self._generate_trend_summary(request, retrieved_docs)
            
            # Step 3: Create reproducibility snapshot
            reproducibility_snapshot = self._create_reproducibility_snapshot(
                request, retrieved_docs
            )
            
            # Step 4: Build response
            response = self._build_response(
                request, trend_summary, retrieved_docs, reproducibility_snapshot, start_time
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Query processed successfully in {processing_time:.2f} seconds")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._error_response(request, str(e), start_time)
    
    def _retrieve_documents(self, request: QueryRequest) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for the query"""
        try:
            # Build filters from request
            filters = self._build_filters(request)
            
            # Retrieve documents with reranking
            documents = self.retrieval_system.retrieve_documents(
                query=request.query,
                top_k=request.max_results or self.default_top_k,
                filters=filters,
                rerank=True
            )
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _build_filters(self, request: QueryRequest) -> Optional[Dict[str, Any]]:
        """Build metadata filters from request"""
        filters = {}
        
        # Date range filter
        if request.date_range:
            if 'start' in request.date_range:
                filters['year'] = {'min': int(request.date_range['start'][:4])}
            if 'end' in request.date_range:
                if 'year' in filters:
                    filters['year']['max'] = int(request.date_range['end'][:4])
                else:
                    filters['year'] = {'max': int(request.date_range['end'][:4])}
        
        # Source filter
        if request.sources:
            filters['source'] = request.sources
        
        return filters if filters else None
    
    def _generate_trend_summary(
        self, 
        request: QueryRequest, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trend summary using LLM"""
        try:
            # Generate retrieval seed for reproducibility
            retrieval_seed = self._generate_retrieval_seed(request)
            
            # Generate summary using Gemini
            summary_data = self.llm_client.generate_trend_summary(
                query=request.query,
                documents=documents,
                retrieval_seed=retrieval_seed
            )
            
            # Filter claims by confidence threshold
            filtered_claims = [
                claim for claim in summary_data.get('claims', [])
                if claim.get('confidence_score', 0) >= self.confidence_threshold
            ]
            
            summary_data['claims'] = filtered_claims
            
            logger.info(f"Generated summary with {len(filtered_claims)} high-confidence claims")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating trend summary: {e}")
            return {
                'trend_summary': "Unable to generate summary due to processing error.",
                'claims': [],
                'reproducibility_snapshot': {}
            }
    
    def _generate_retrieval_seed(self, request: QueryRequest) -> int:
        """Generate reproducible retrieval seed"""
        seed_string = f"{request.query}_{request.date_range}_{request.sources}"
        return hash(seed_string) % 10000
    
    def _create_reproducibility_snapshot(
        self, 
        request: QueryRequest, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create reproducibility snapshot"""
        try:
            doc_ids = [doc.get('id', f"doc_{i}") for i, doc in enumerate(documents)]
            
            snapshot = {
                'query': request.query,
                'timestamp': datetime.now().isoformat(),
                'doc_ids': doc_ids,
                'retrieval_seed': self._generate_retrieval_seed(request),
                'filters': self._build_filters(request),
                'top_k': request.max_results or self.default_top_k,
                'pipeline_version': '1.0',
                'model': 'gemini-1.5-flash',
                'embedding_model': settings.EMBEDDING_MODEL
            }
            
            # Add hash for integrity checking
            snapshot_string = f"{request.query}_{doc_ids}_{snapshot['retrieval_seed']}"
            snapshot['integrity_hash'] = hashlib.md5(snapshot_string.encode()).hexdigest()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error creating reproducibility snapshot: {e}")
            return {}
    
    def _build_response(
        self,
        request: QueryRequest,
        trend_summary: Dict[str, Any],
        documents: List[Dict[str, Any]],
        reproducibility_snapshot: Dict[str, Any],
        start_time: float
    ) -> QueryResponse:
        """Build final query response"""
        try:
            # Convert documents to PaperMetadata objects
            papers = []
            for doc in documents:
                paper = PaperMetadata(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    authors=doc.get('authors', []),
                    year=doc.get('year', 0),
                    abstract=doc.get('abstract', ''),
                    url=doc.get('url', ''),
                    source=doc.get('source', ''),
                    doi=doc.get('doi'),
                    citation_count=doc.get('citation_count')
                )
                papers.append(paper)
            
            # Convert claims to Claim objects
            claims = []
            for claim_data in trend_summary.get('claims', []):
                claim = Claim(
                    text=claim_data.get('text', ''),
                    confidence=claim_data.get('confidence_score', 0.5),
                    evidence=[claim_data.get('evidence', '')],
                    supporting_papers=[claim_data.get('supporting_doc', '')]
                )
                claims.append(claim)
            
            # Create trend summary object
            summary = TrendSummary(
                summary=trend_summary.get('trend_summary', ''),
                claims=claims,
                papers=papers,
                timeline=self._generate_timeline(papers),
                reproducibility_snapshot=reproducibility_snapshot
            )
            
            # Create response
            response = QueryResponse(
                query=request.query,
                summary=summary,
                processing_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error building response: {e}")
            return self._error_response(request, str(e), start_time)
    
    def _generate_timeline(self, papers: List[PaperMetadata]) -> Dict[str, int]:
        """Generate timeline of papers by year"""
        timeline = {}
        for paper in papers:
            year = paper.year
            if year:
                timeline[str(year)] = timeline.get(str(year), 0) + 1
        return timeline
    
    def _empty_response(self, request: QueryRequest, start_time: float) -> QueryResponse:
        """Return empty response when no documents found"""
        empty_summary = TrendSummary(
            summary="No relevant documents found for this query.",
            claims=[],
            papers=[],
            timeline={},
            reproducibility_snapshot={
                'query': request.query,
                'timestamp': datetime.now().isoformat(),
                'doc_ids': [],
                'retrieval_seed': self._generate_retrieval_seed(request)
            }
        )
        
        return QueryResponse(
            query=request.query,
            summary=empty_summary,
            processing_time=time.time() - start_time,
            timestamp=datetime.now()
        )
    
    def _error_response(self, request: QueryRequest, error: str, start_time: float) -> QueryResponse:
        """Return error response"""
        error_summary = TrendSummary(
            summary=f"Error processing query: {error}",
            claims=[],
            papers=[],
            timeline={},
            reproducibility_snapshot={
                'query': request.query,
                'timestamp': datetime.now().isoformat(),
                'error': error
            }
        )
        
        return QueryResponse(
            query=request.query,
            summary=error_summary,
            processing_time=time.time() - start_time,
            timestamp=datetime.now()
        )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        try:
            retrieval_stats = self.retrieval_system.get_retrieval_stats()
            vector_stats = self.vector_store.get_stats()
            
            return {
                'pipeline_version': '1.0',
                'components': {
                    'vector_store': vector_stats,
                    'retrieval_system': retrieval_stats,
                    'llm_client': {
                        'model': 'gemini-1.5-flash',
                        'connection_status': self.llm_client.test_connection()
                    }
                },
                'configuration': {
                    'default_top_k': self.default_top_k,
                    'confidence_threshold': self.confidence_threshold,
                    'embedding_model': settings.EMBEDDING_MODEL
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {}
