"""
Core RAG pipeline for end-to-end query processing
"""

import logging
import time
import hashlib
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime

from rag_engine.retrieval_system import RetrievalSystem
from llm_integration.gemini_client import GeminiClient
from vector_store.faiss_store import FAISSVectorStore
from data_pipeline import DataPipeline
from utils.cache_service import cache_service
from models import (
    QueryRequest, QueryResponse, TrendSummary, Claim, PaperMetadata,
    TimelineData, ClusterData, ClusterPoint, SourceInfo, PromptTransparency, ReproducibilityInfo
)
from config import settings

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Core RAG pipeline for processing literature queries"""
    
    def __init__(self):
        # Initialize components
        self.vector_store = FAISSVectorStore()
        self.retrieval_system = RetrievalSystem(self.vector_store)
        self.llm_client = GeminiClient()
        self.data_pipeline = DataPipeline()
        
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
            
            # First, try to fetch new papers from APIs based on the query
            # Only fetch if we have few papers or if it's a new query
            current_paper_count = len(self.vector_store.get_all_papers())
            
            # Check if we should fetch new papers
            should_fetch = (
                current_paper_count < 50 or  # Always fetch if we have few papers
                not self._is_similar_query_cached(request.query)  # Or if it's a new query
            )
            
            if should_fetch:
                new_papers = self._fetch_new_papers_for_query(request.query)
                
                # If we got new papers, add them to the vector store
                if new_papers:
                    logger.info(f"Fetched {len(new_papers)} new papers for query: {request.query}")
                    self.vector_store.add_documents(new_papers)
                    self.vector_store.save_index()
                    
                # Cache this query as processed
                self._cache_query_processed(request.query)
            else:
                logger.info(f"Sufficient papers in database ({current_paper_count}) and similar query cached, skipping API fetch")
            
            # Retrieve documents with reranking (now includes new papers)
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
    
    def _fetch_new_papers_for_query(self, query: str) -> List[Dict[str, Any]]:
        """Fetch new papers from APIs based on the search query with caching and parallel execution"""
        try:
            # Convert query to BCI-specific search terms
            bci_query = self._enhance_query_for_bci(query)
            
            logger.info(f"Fetching new papers for enhanced query: {bci_query}")
            
            # Check cache first for each source
            cached_papers = []
            sources_to_fetch = []
            
            for source in ['arxiv', 'pubmed', 'semantic_scholar']:
                cached_result = cache_service.get_api_response(source, bci_query)
                if cached_result:
                    cached_papers.extend(cached_result)
                    logger.info(f"Found {len(cached_result)} cached papers from {source}")
                else:
                    sources_to_fetch.append(source)
            
            # If we have cached results, return them
            if cached_papers and not sources_to_fetch:
                logger.info(f"Returning {len(cached_papers)} cached papers")
                return self._deduplicate_papers(cached_papers)
            
            # Fetch from remaining sources in parallel
            all_new_papers = cached_papers.copy()
            
            if sources_to_fetch:
                logger.info(f"Fetching from sources: {sources_to_fetch}")
                
                # Use ThreadPoolExecutor for parallel API calls
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_source = {}
                    
                    for source in sources_to_fetch:
                        if source == 'arxiv':
                            future = executor.submit(
                                self._fetch_from_arxiv, bci_query, 20
                            )
                        elif source == 'pubmed':
                            future = executor.submit(
                                self._fetch_from_pubmed, bci_query, 20
                            )
                        elif source == 'semantic_scholar':
                            future = executor.submit(
                                self._fetch_from_semantic_scholar, bci_query, 20
                            )
                        
                        future_to_source[future] = source
                    
                    # Collect results with timeout
                    for future in concurrent.futures.as_completed(future_to_source, timeout=30):
                        source = future_to_source[future]
                        try:
                            papers = future.result()
                            all_new_papers.extend(papers)
                            
                            # Cache the results
                            cache_service.set_api_response(source, bci_query, papers)
                            logger.info(f"Fetched and cached {len(papers)} papers from {source}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to fetch from {source}: {e}")
            
            # Process and deduplicate papers
            processed_papers = self.data_pipeline.process_papers(all_new_papers)
            unique_papers = self._deduplicate_papers(processed_papers)
            
            logger.info(f"Total new papers after deduplication: {len(unique_papers)}")
            return unique_papers
            
        except Exception as e:
            logger.error(f"Error fetching new papers: {e}")
            return []
    
    def _is_similar_query_cached(self, query: str) -> bool:
        """Check if a similar query has been processed recently"""
        try:
            # Get similar queries from cache
            similar_queries = cache_service.get_query_similarity(query)
            if not similar_queries:
                return False
            
            # Check if any similar query was processed recently
            for similar_query in similar_queries:
                if self._is_query_recently_processed(similar_query):
                    logger.info(f"Found similar cached query: {similar_query}")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking query similarity: {e}")
            return False
    
    def _is_query_recently_processed(self, query: str) -> bool:
        """Check if query was processed recently (within last 2 hours)"""
        try:
            cache_key = f"processed_query:{hashlib.md5(query.encode()).hexdigest()}"
            processed_time = cache_service.get(cache_key)
            if not processed_time:
                return False
            
            # Check if processed within last 2 hours
            from datetime import datetime, timedelta
            if isinstance(processed_time, str):
                processed_time = datetime.fromisoformat(processed_time)
            
            return datetime.now() - processed_time < timedelta(hours=2)
        except Exception as e:
            logger.error(f"Error checking query processing time: {e}")
            return False
    
    def _cache_query_processed(self, query: str) -> None:
        """Cache that a query was processed"""
        try:
            cache_key = f"processed_query:{hashlib.md5(query.encode()).hexdigest()}"
            cache_service.set(cache_key, datetime.now().isoformat(), ttl_seconds=7200)  # 2 hours
            
            # Also cache query similarity
            similar_queries = cache_service.get_query_similarity(query) or []
            if query not in similar_queries:
                similar_queries.append(query)
                cache_service.set_query_similarity(query, similar_queries)
        except Exception as e:
            logger.error(f"Error caching query: {e}")
    
    def _fetch_from_arxiv(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv"""
        try:
            return self.data_pipeline.arxiv_client.search_papers(query, max_results)
        except Exception as e:
            logger.warning(f"arXiv fetch failed: {e}")
            return []
    
    def _fetch_from_pubmed(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers from PubMed"""
        try:
            return self.data_pipeline.pubmed_client.search_papers(query, max_results)
        except Exception as e:
            logger.warning(f"PubMed fetch failed: {e}")
            return []
    
    def _fetch_from_semantic_scholar(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers from Semantic Scholar"""
        try:
            return self.data_pipeline.semantic_client.search_papers(query, max_results)
        except Exception as e:
            logger.warning(f"Semantic Scholar fetch failed: {e}")
            return []
    
    def _enhance_query_for_bci(self, query: str) -> str:
        """Enhance the query to be more BCI-specific"""
        query_lower = query.lower()
        
        # If the query already contains BCI terms, use it as-is
        bci_terms = ['bci', 'brain-computer interface', 'brain computer interface', 'eeg', 'ecog', 'fmri', 'fnirs', 'ssvep', 'p300', 'motor imagery', 'neural interface']
        if any(term in query_lower for term in bci_terms):
            return query
        
        # Otherwise, enhance it with BCI context
        enhanced_query = f"({query}) AND (brain-computer interface OR BCI OR EEG OR neural interface)"
        return enhanced_query
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title similarity"""
        if not papers:
            return papers
        
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title = paper.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _generate_trend_summary(
        self, 
        request: QueryRequest, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trend summary using LLM with caching"""
        try:
            # Check cache first
            cached_response = cache_service.get_llm_response(request.query, documents)
            if cached_response:
                logger.info("Using cached LLM response")
                return cached_response
            
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
            
            # Cache the response
            cache_service.set_llm_response(request.query, documents, summary_data)
            
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
    
    # Sprint 5 Methods for Advanced Features
    
    def get_timeline_data(self) -> TimelineData:
        """Get timeline data for visualization"""
        try:
            # Get all papers from vector store
            all_papers = self.vector_store.get_all_papers()
            
            # Calculate papers per year
            papers_per_year = {}
            keyword_trends = {}
            total_papers = len(all_papers)
            years = []
            
            for paper in all_papers:
                year = paper.get('year', 0)
                if year:
                    years.append(year)
                    papers_per_year[year] = papers_per_year.get(year, 0) + 1
                    
                    # Extract keywords from title and abstract
                    text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                    keywords = self._extract_keywords(text)
                    
                    for keyword in keywords:
                        if keyword not in keyword_trends:
                            keyword_trends[keyword] = []
                        keyword_trends[keyword].append({
                            'year': year,
                            'count': 1,
                            'paper_id': paper.get('id', '')
                        })
            
            # Aggregate keyword trends by year
            for keyword in keyword_trends:
                yearly_counts = {}
                for entry in keyword_trends[keyword]:
                    year = entry['year']
                    yearly_counts[year] = yearly_counts.get(year, 0) + 1
                
                keyword_trends[keyword] = [
                    {'year': year, 'count': count}
                    for year, count in yearly_counts.items()
                ]
            
            year_range = {
                'min': min(years) if years else 2020,
                'max': max(years) if years else 2024
            }
            
            return TimelineData(
                papers_per_year=papers_per_year,
                keyword_trends=keyword_trends,
                total_papers=total_papers,
                year_range=year_range
            )
            
        except Exception as e:
            logger.error(f"Error getting timeline data: {e}")
            return TimelineData(
                papers_per_year={},
                keyword_trends={},
                total_papers=0,
                year_range={'min': 2020, 'max': 2024}
            )
    
    def get_cluster_data(self) -> ClusterData:
        """Get cluster data for visualization using UMAP"""
        try:
            import umap
            import numpy as np
            from sklearn.cluster import KMeans
            
            # Get all papers and their embeddings
            all_papers = self.vector_store.get_all_papers()
            if len(all_papers) < 5:  # Need minimum papers for clustering
                return ClusterData(
                    points=[],
                    clusters={},
                    algorithm="umap",
                    parameters={},
                    message=f"Need at least 5 papers for clustering. Currently have {len(all_papers)} papers."
                )
            
            # Get embeddings for all papers
            embeddings = []
            paper_ids = []
            for paper in all_papers:
                embedding = self.vector_store.get_embedding(paper.get('id', ''))
                if embedding is not None:
                    embeddings.append(embedding)
                    paper_ids.append(paper.get('id', ''))
            
            if len(embeddings) < 5:
                return ClusterData(
                    points=[],
                    clusters={},
                    algorithm="umap",
                    parameters={},
                    message=f"Need at least 5 papers for clustering. Currently have {len(embeddings)} papers."
                )
            
            embeddings = np.array(embeddings)
            
            # Apply UMAP dimensionality reduction
            umap_reducer = umap.UMAP(
                n_components=2,
                n_neighbors=15,
                min_dist=0.1,
                random_state=42
            )
            embedding_2d = umap_reducer.fit_transform(embeddings)
            
            # Apply K-means clustering
            n_clusters = min(8, len(embeddings) // 5)  # Adaptive cluster count
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Create cluster points
            points = []
            for i, paper_id in enumerate(paper_ids):
                paper = next((p for p in all_papers if p.get('id') == paper_id), {})
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                keywords = self._extract_keywords(text)[:5]  # Top 5 keywords
                
                point = ClusterPoint(
                    id=paper_id,
                    x=float(embedding_2d[i, 0]),
                    y=float(embedding_2d[i, 1]),
                    cluster_id=int(cluster_labels[i]),
                    title=paper.get('title', ''),
                    year=paper.get('year', 0),
                    keywords=keywords,
                    citation_count=paper.get('citation_count')
                )
                points.append(point)
            
            # Create cluster metadata
            clusters = {}
            for cluster_id in range(n_clusters):
                cluster_points = [p for p in points if p.cluster_id == cluster_id]
                cluster_keywords = {}
                for point in cluster_points:
                    for keyword in point.keywords:
                        cluster_keywords[keyword] = cluster_keywords.get(keyword, 0) + 1
                
                # Get top keywords for this cluster
                top_keywords = sorted(
                    cluster_keywords.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
                
                clusters[cluster_id] = {
                    'size': len(cluster_points),
                    'top_keywords': [kw[0] for kw in top_keywords],
                    'year_range': {
                        'min': min(p.year for p in cluster_points) if cluster_points else 0,
                        'max': max(p.year for p in cluster_points) if cluster_points else 0
                    }
                }
            
            return ClusterData(
                points=points,
                clusters=clusters,
                algorithm="umap",
                parameters={
                    'n_neighbors': 15,
                    'min_dist': 0.1,
                    'n_clusters': n_clusters
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting cluster data: {e}")
            return ClusterData(
                points=[],
                clusters={},
                algorithm="umap",
                parameters={}
            )
    
    def get_sources_info(self) -> Dict[str, SourceInfo]:
        """Get detailed source information for transparency"""
        try:
            all_papers = self.vector_store.get_all_papers()
            
            sources = {}
            for paper in all_papers:
                source = paper.get('source', 'unknown')
                if source not in sources:
                    sources[source] = {
                        'papers': [],
                        'years': set(),
                        'total_citations': 0
                    }
                
                sources[source]['papers'].append(paper)
                if paper.get('year'):
                    sources[source]['years'].add(paper.get('year'))
                if paper.get('citation_count'):
                    sources[source]['total_citations'] += paper.get('citation_count', 0)
            
            # Convert to SourceInfo objects
            source_infos = {}
            for source_name, data in sources.items():
                source_info = SourceInfo(
                    name=source_name,
                    description=f"Papers from {source_name}",
                    last_updated=datetime.now(),
                    paper_count=len(data['papers']),
                    coverage={
                        'year_range': {
                            'min': min(data['years']) if data['years'] else 0,
                            'max': max(data['years']) if data['years'] else 0
                        },
                        'total_citations': data['total_citations'],
                        'avg_citations': data['total_citations'] / len(data['papers']) if data['papers'] else 0
                    }
                )
                source_infos[source_name] = source_info
            
            return source_infos
            
        except Exception as e:
            logger.error(f"Error getting sources info: {e}")
            return {}
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using simple frequency analysis"""
        import re
        from collections import Counter
        
        # BCI-related keywords to look for
        bci_keywords = [
            'eeg', 'ecog', 'fmri', 'fnirs', 'ssvep', 'p300', 'motor imagery',
            'brain-computer interface', 'bci', 'neural interface', 'neurofeedback',
            'classification', 'decoding', 'feature extraction', 'signal processing',
            'machine learning', 'deep learning', 'cnn', 'lstm', 'svm',
            'non-invasive', 'invasive', 'implant', 'electrode', 'stimulation'
        ]
        
        # Convert to lowercase and find matches
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in bci_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        # Also extract common words (simple approach)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_lower)
        word_counts = Counter(words)
        
        # Get top words that aren't common stop words
        stop_words = {'this', 'that', 'with', 'from', 'they', 'been', 'have', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'also', 'after', 'back', 'well', 'work', 'even', 'most', 'through', 'years', 'much', 'before', 'right', 'being', 'good', 'many', 'some', 'very', 'when', 'here', 'than', 'into', 'only', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'find', 'any', 'new', 'way', 'may', 'say', 'use', 'her', 'many', 'and', 'get', 'has', 'had', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        top_words = [word for word, count in word_counts.most_common(10) 
                    if word not in stop_words and len(word) > 3]
        
        # Combine BCI keywords with top words
        all_keywords = list(set(found_keywords + top_words))
        
        return all_keywords[:10]  # Return top 10 keywords
