"""
Retrieval system for semantic search with reranking
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from vector_store.faiss_store import FAISSVectorStore
from config import settings

logger = logging.getLogger(__name__)

class RetrievalSystem:
    """Advanced retrieval system with reranking and filtering"""
    
    def __init__(self, vector_store: FAISSVectorStore):
        self.vector_store = vector_store
        self.top_k = settings.TOP_K_RESULTS
    
    def retrieve_documents(
        self, 
        query: str, 
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank documents for a query
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filters: Optional metadata filters
            rerank: Whether to apply reranking
        
        Returns:
            List of retrieved documents with scores
        """
        try:
            if top_k is None:
                top_k = self.top_k
            
            # Initial retrieval from vector store
            initial_results = self.vector_store.search(query, top_k=top_k * 2, filter_metadata=filters)
            
            if not initial_results:
                logger.warning(f"No documents found for query: {query}")
                return []
            
            # Apply reranking if requested
            if rerank:
                reranked_results = self._rerank_documents(query, initial_results)
            else:
                reranked_results = initial_results
            
            # Apply final filtering and return top results
            final_results = self._apply_final_filters(reranked_results, filters)
            
            logger.info(f"Retrieved {len(final_results)} documents for query: {query}")
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in document retrieval: {e}")
            return []
    
    def _rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on multiple criteria
        
        Args:
            query: Original query
            documents: List of documents to rerank
        
        Returns:
            Reranked list of documents
        """
        try:
            reranked_docs = []
            
            for doc in documents:
                # Calculate composite score
                composite_score = self._calculate_composite_score(query, doc)
                doc['composite_score'] = composite_score
                doc['rerank_score'] = composite_score
                reranked_docs.append(doc)
            
            # Sort by composite score (lower is better for distance-based scores)
            reranked_docs.sort(key=lambda x: x['composite_score'])
            
            logger.info(f"Reranked {len(reranked_docs)} documents")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Error in document reranking: {e}")
            return documents
    
    def _calculate_composite_score(
        self, 
        query: str, 
        document: Dict[str, Any]
    ) -> float:
        """
        Calculate composite score for document ranking
        
        Args:
            query: Search query
            document: Document metadata
        
        Returns:
            Composite score (lower is better)
        """
        try:
            # Base similarity score (from vector search)
            similarity_score = document.get('similarity_score', 1.0)
            
            # Recency score (newer papers get better scores)
            recency_score = self._calculate_recency_score(document)
            
            # Citation score (more cited papers get better scores)
            citation_score = self._calculate_citation_score(document)
            
            # Title relevance score
            title_score = self._calculate_title_relevance(query, document)
            
            # Abstract relevance score
            abstract_score = self._calculate_abstract_relevance(query, document)
            
            # Weighted composite score
            composite_score = (
                0.4 * similarity_score +      # Vector similarity (40%)
                0.2 * recency_score +         # Recency (20%)
                0.15 * citation_score +       # Citations (15%)
                0.15 * title_score +          # Title relevance (15%)
                0.1 * abstract_score          # Abstract relevance (10%)
            )
            
            return composite_score
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return document.get('similarity_score', 1.0)
    
    def _calculate_recency_score(self, document: Dict[str, Any]) -> float:
        """Calculate recency score (newer = better)"""
        try:
            year = document.get('year')
            if not year:
                return 0.5  # Neutral score for unknown year
            
            current_year = datetime.now().year
            age = current_year - year
            
            # Score decreases with age, but not too aggressively
            if age <= 1:
                return 1.0
            elif age <= 3:
                return 0.8
            elif age <= 5:
                return 0.6
            elif age <= 10:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.5
    
    def _calculate_citation_score(self, document: Dict[str, Any]) -> float:
        """Calculate citation score (more citations = better)"""
        try:
            citation_count = document.get('citation_count', 0)
            if citation_count is None:
                citation_count = 0
            
            # Normalize citation count (log scale)
            if citation_count == 0:
                return 0.3  # Neutral score for no citations
            elif citation_count < 10:
                return 0.5
            elif citation_count < 50:
                return 0.7
            elif citation_count < 100:
                return 0.8
            elif citation_count < 500:
                return 0.9
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Error calculating citation score: {e}")
            return 0.5
    
    def _calculate_title_relevance(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate title relevance score"""
        try:
            title = document.get('title', '').lower()
            query_terms = query.lower().split()
            
            if not title or not query_terms:
                return 0.5
            
            # Count query terms in title
            matches = sum(1 for term in query_terms if term in title)
            relevance = matches / len(query_terms)
            
            return min(relevance, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating title relevance: {e}")
            return 0.5
    
    def _calculate_abstract_relevance(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate abstract relevance score"""
        try:
            abstract = document.get('abstract', '').lower()
            query_terms = query.lower().split()
            
            if not abstract or not query_terms:
                return 0.5
            
            # Count query terms in abstract
            matches = sum(1 for term in query_terms if term in abstract)
            relevance = matches / len(query_terms)
            
            return min(relevance, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating abstract relevance: {e}")
            return 0.5
    
    def _apply_final_filters(
        self, 
        documents: List[Dict[str, Any]], 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply final filtering to documents"""
        if not filters:
            return documents
        
        filtered_docs = []
        for doc in documents:
            if self._matches_filters(doc, filters):
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def _matches_filters(self, document: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches all filters"""
        try:
            for key, value in filters.items():
                doc_value = document.get(key)
                
                if doc_value is None:
                    return False
                
                # Handle different filter types
                if isinstance(value, list):
                    if doc_value not in value:
                        return False
                elif isinstance(value, dict):
                    if 'min' in value and doc_value < value['min']:
                        return False
                    if 'max' in value and doc_value > value['max']:
                        return False
                else:
                    if doc_value != value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking filters: {e}")
            return True
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        try:
            vector_stats = self.vector_store.get_stats()
            
            return {
                'vector_store_stats': vector_stats,
                'top_k_default': self.top_k,
                'reranking_enabled': True,
                'scoring_weights': {
                    'similarity': 0.4,
                    'recency': 0.2,
                    'citations': 0.15,
                    'title_relevance': 0.15,
                    'abstract_relevance': 0.1
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {}
