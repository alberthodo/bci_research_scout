"""
Semantic Scholar API client for fetching paper metadata and citations
"""

import requests
from typing import List, Dict, Any, Optional
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticScholarClient:
    """Client for fetching papers from Semantic Scholar API"""
    
    def __init__(self, base_url: str = "https://api.semanticscholar.org/graph/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-BCI-Scout/1.0 (research tool)'
        })
    
    def search_papers(
        self, 
        query: str, 
        max_results: int = 100,
        fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on Semantic Scholar
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            fields: Fields to return (default: comprehensive set)
        
        Returns:
            List of paper metadata dictionaries
        """
        if fields is None:
            fields = [
                'paperId', 'title', 'abstract', 'authors', 'year', 'venue',
                'citationCount', 'influentialCitationCount', 'isOpenAccess',
                'openAccessPdf', 'url', 'doi', 'fieldsOfStudy', 's2FieldsOfStudy'
            ]
        
        try:
            search_url = f"{self.base_url}/paper/search"
            params = {
                'query': query,
                'limit': min(max_results, 100),  # API limit per request
                'fields': ','.join(fields)
            }
            
            logger.info(f"Searching Semantic Scholar with query: {query}")
            
            # Retry logic for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(search_url, params=params, timeout=30)
                    if response.status_code == 429:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Request failed, retrying... ({e})")
                    time.sleep(1)
            
            data = response.json()
            papers = data.get('data', [])
            
            # Handle pagination if needed
            if len(papers) < max_results and 'next' in data:
                papers.extend(self._fetch_additional_pages(data['next'], max_results - len(papers)))
            
            processed_papers = [self._process_paper(paper) for paper in papers]
            processed_papers = [p for p in processed_papers if p is not None]
            
            logger.info(f"Found {len(processed_papers)} papers from Semantic Scholar")
            return processed_papers
            
        except requests.RequestException as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Semantic Scholar search: {e}")
            return []
    
    def _fetch_additional_pages(self, next_url: str, remaining: int) -> List[Dict[str, Any]]:
        """Fetch additional pages of results"""
        papers = []
        
        try:
            while remaining > 0 and next_url:
                response = self.session.get(next_url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                page_papers = data.get('data', [])
                
                if not page_papers:
                    break
                
                papers.extend(page_papers[:remaining])
                remaining -= len(page_papers)
                next_url = data.get('next')
                
                # Rate limiting
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error fetching additional pages: {e}")
        
        return papers
    
    def _process_paper(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process raw paper data into standardized format"""
        try:
            # Extract basic information
            paper_id = paper_data.get('paperId')
            if not paper_id:
                return None
            
            title = paper_data.get('title', 'No title')
            abstract = paper_data.get('abstract', '')
            
            # Extract authors
            authors = []
            for author in paper_data.get('authors', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)
            
            # Extract year
            year = paper_data.get('year')
            if year:
                year = int(year)
            
            # Extract venue
            venue = paper_data.get('venue', '')
            
            # Extract citation counts
            citation_count = paper_data.get('citationCount', 0)
            influential_citations = paper_data.get('influentialCitationCount', 0)
            
            # Extract URLs
            url = paper_data.get('url', '')
            doi = paper_data.get('doi', '')
            
            # Extract open access PDF
            open_access_pdf = None
            if paper_data.get('isOpenAccess') and paper_data.get('openAccessPdf'):
                open_access_pdf = paper_data['openAccessPdf'].get('url')
            
            # Extract fields of study
            fields_of_study = paper_data.get('fieldsOfStudy', [])
            s2_fields = paper_data.get('s2FieldsOfStudy', [])
            
            return {
                'id': f"semantic_{paper_id}",
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'url': url,
                'doi': doi,
                'source': 'semantic_scholar',
                'published_date': f"{year}-01-01" if year else None,
                'year': year,
                'venue': venue,
                'citation_count': citation_count,
                'influential_citations': influential_citations,
                'open_access_pdf': open_access_pdf,
                'raw_data': {
                    'paper_id': paper_id,
                    'fields_of_study': fields_of_study,
                    's2_fields': s2_fields,
                    'is_open_access': paper_data.get('isOpenAccess', False)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing paper data: {e}")
            return None
    
    def get_bci_papers(self, max_results: int = 200) -> List[Dict[str, Any]]:
        """
        Get BCI/Neurotech papers from Semantic Scholar
        
        Args:
            max_results: Maximum number of papers to fetch
        
        Returns:
            List of BCI paper metadata
        """
        # BCI-related search queries for Semantic Scholar
        bci_queries = [
            "brain computer interface",
            "BCI EEG",
            "neural interface",
            "SSVEP brain",
            "P300 brain",
            "motor imagery EEG",
            "neurotechnology",
            "neural prosthesis"
        ]
        
        all_papers = []
        seen_ids = set()
        
        for query in bci_queries:
            papers = self.search_papers(query, max_results=max_results // len(bci_queries))
            
            for paper in papers:
                if paper['id'] not in seen_ids:
                    all_papers.append(paper)
                    seen_ids.add(paper['id'])
            
            # Rate limiting - longer delay to avoid 429 errors
            time.sleep(2)
        
        # Sort by citation count and year (most influential first)
        all_papers.sort(
            key=lambda x: (x.get('citation_count', 0), x.get('year', 0)), 
            reverse=True
        )
        
        return all_papers[:max_results]
    
    def get_paper_citations(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Get citations for a specific paper
        
        Args:
            paper_id: Semantic Scholar paper ID
        
        Returns:
            List of citing papers
        """
        try:
            citations_url = f"{self.base_url}/paper/{paper_id}/citations"
            params = {
                'fields': 'paperId,title,authors,year,citationCount',
                'limit': 100
            }
            
            response = self.session.get(citations_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            citations = data.get('data', [])
            
            return [self._process_paper(citation) for citation in citations]
            
        except Exception as e:
            logger.error(f"Error fetching citations for paper {paper_id}: {e}")
            return []
