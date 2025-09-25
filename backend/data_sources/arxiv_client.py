"""
arXiv API client for fetching BCI/Neurotech papers
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ArxivClient:
    """Client for fetching papers from arXiv API"""
    
    def __init__(self, base_url: str = "http://export.arxiv.org/api/query"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-BCI-Scout/1.0 (research tool)'
        })
    
    def search_papers(
        self, 
        query: str, 
        max_results: int = 100,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on arXiv
        
        Args:
            query: Search query (e.g., "BCI OR brain-computer interface")
            max_results: Maximum number of results to return
            start: Starting index for results
            sort_by: Sort field (submittedDate, relevance, lastUpdatedDate)
            sort_order: Sort order (ascending, descending)
        
        Returns:
            List of paper metadata dictionaries
        """
        try:
            params = {
                'search_query': query,
                'start': start,
                'max_results': min(max_results, 2000),  # arXiv API limit
                'sortBy': sort_by,
                'sortOrder': sort_order
            }
            
            logger.info(f"Searching arXiv with query: {query}")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            papers = self._parse_arxiv_response(response.text)
            logger.info(f"Found {len(papers)} papers from arXiv")
            
            return papers
            
        except requests.RequestException as e:
            logger.error(f"Error fetching from arXiv: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in arXiv search: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response into paper metadata"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespaces
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                paper = self._extract_paper_metadata(entry, ns)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing arXiv XML: {e}")
        except Exception as e:
            logger.error(f"Error processing arXiv response: {e}")
        
        return papers
    
    def _extract_paper_metadata(self, entry, ns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract metadata from a single arXiv entry"""
        try:
            # Extract basic information
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else "No title"
            
            summary_elem = entry.find('atom:summary', ns)
            abstract = summary_elem.text.strip() if summary_elem is not None else ""
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            # Extract publication date
            published_elem = entry.find('atom:published', ns)
            published_date = None
            if published_elem is not None:
                try:
                    published_date = datetime.fromisoformat(
                        published_elem.text.replace('Z', '+00:00')
                    )
                except ValueError:
                    pass
            
            # Extract arXiv ID and URL
            id_elem = entry.find('atom:id', ns)
            arxiv_id = None
            arxiv_url = None
            if id_elem is not None:
                arxiv_url = id_elem.text
                # Extract arXiv ID from URL
                if 'arxiv.org/abs/' in arxiv_url:
                    arxiv_id = arxiv_url.split('arxiv.org/abs/')[-1]
            
            # Extract categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # Extract DOI if available
            doi = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'doi':
                    doi = link.get('href', '').replace('http://dx.doi.org/', '')
                    break
            
            return {
                'id': arxiv_id or f"arxiv_{hash(title)}",
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'url': arxiv_url,
                'doi': doi,
                'source': 'arxiv',
                'published_date': published_date.isoformat() if published_date else None,
                'categories': categories,
                'year': published_date.year if published_date else None,
                'citation_count': None,  # arXiv doesn't provide citation counts
                'raw_data': {
                    'arxiv_id': arxiv_id,
                    'categories': categories
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting paper metadata: {e}")
            return None
    
    def get_bci_papers(self, max_results: int = 200) -> List[Dict[str, Any]]:
        """
        Get BCI/Neurotech papers from arXiv
        
        Args:
            max_results: Maximum number of papers to fetch
        
        Returns:
            List of BCI paper metadata
        """
        # BCI-related search queries - broader to ensure results
        bci_queries = [
            "brain computer interface",
            "BCI",
            "neural interface", 
            "SSVEP",
            "P300",
            "motor imagery",
            "neurotechnology",
            "neural prosthesis",
            "electroencephalography",
            "brain signal"
        ]
        
        all_papers = []
        seen_ids = set()
        
        for query in bci_queries:
            papers = self.search_papers(query, max_results=max_results // len(bci_queries))
            
            for paper in papers:
                if paper['id'] not in seen_ids:
                    all_papers.append(paper)
                    seen_ids.add(paper['id'])
            
            # Rate limiting
            time.sleep(1)
        
        # Sort by publication date (newest first)
        all_papers.sort(
            key=lambda x: x.get('published_date', '1900-01-01'), 
            reverse=True
        )
        
        return all_papers[:max_results]
