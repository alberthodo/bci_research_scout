"""
PubMed API client for fetching biomedical papers
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PubMedClient:
    """Client for fetching papers from PubMed API"""
    
    def __init__(self, base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-BCI-Scout/1.0 (research tool)'
        })
    
    def search_papers(
        self, 
        query: str, 
        max_results: int = 100,
        retmax: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on PubMed
        
        Args:
            query: Search query (e.g., "brain computer interface")
            max_results: Maximum number of results to return
            retmax: Results per request (max 10000)
        
        Returns:
            List of paper metadata dictionaries
        """
        try:
            # Step 1: Search for PMIDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': min(retmax, 10000),
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            logger.info(f"Searching PubMed with query: {query}")
            search_response = self.session.get(search_url, params=search_params, timeout=30)
            search_response.raise_for_status()
            
            search_data = search_response.json()
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            
            if not pmids:
                logger.info("No papers found in PubMed")
                return []
            
            # Limit results
            pmids = pmids[:max_results]
            
            # Step 2: Fetch detailed information
            papers = self._fetch_paper_details(pmids)
            
            logger.info(f"Found {len(papers)} papers from PubMed")
            return papers
            
        except requests.RequestException as e:
            logger.error(f"Error fetching from PubMed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in PubMed search: {e}")
            return []
    
    def _fetch_paper_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed information for a list of PMIDs"""
        papers = []
        
        try:
            # Fetch details in batches
            batch_size = 200  # PubMed API limit
            for i in range(0, len(pmids), batch_size):
                batch_pmids = pmids[i:i + batch_size]
                batch_papers = self._fetch_batch_details(batch_pmids)
                papers.extend(batch_papers)
                
                # Rate limiting
                time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error fetching paper details: {e}")
        
        return papers
    
    def _fetch_batch_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch details for a batch of PMIDs"""
        try:
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            response = self.session.get(fetch_url, params=fetch_params, timeout=30)
            response.raise_for_status()
            
            return self._parse_pubmed_response(response.text)
            
        except Exception as e:
            logger.error(f"Error fetching batch details: {e}")
            return []
    
    def _parse_pubmed_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML response into paper metadata"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                paper = self._extract_paper_metadata(article)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing PubMed XML: {e}")
        except Exception as e:
            logger.error(f"Error processing PubMed response: {e}")
        
        return papers
    
    def _extract_paper_metadata(self, article) -> Optional[Dict[str, Any]]:
        """Extract metadata from a single PubMed article"""
        try:
            # Extract PMID
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None
            
            if not pmid:
                return None
            
            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text.strip() if title_elem is not None else "No title"
            
            # Extract abstract
            abstract_elem = article.find('.//AbstractText')
            abstract = abstract_elem.text.strip() if abstract_elem is not None else ""
            
            # Extract authors
            authors = []
            for author in article.findall('.//Author'):
                last_name = author.find('LastName')
                first_name = author.find('ForeName')
                if last_name is not None:
                    name = last_name.text
                    if first_name is not None:
                        name = f"{first_name.text} {name}"
                    authors.append(name)
            
            # Extract publication date
            pub_date = article.find('.//PubDate')
            year = None
            published_date = None
            if pub_date is not None:
                year_elem = pub_date.find('Year')
                if year_elem is not None:
                    year = int(year_elem.text)
                    published_date = f"{year}-01-01"  # Approximate date
            
            # Extract journal
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown Journal"
            
            # Extract DOI
            doi = None
            for article_id in article.findall('.//ArticleId'):
                if article_id.get('IdType') == 'doi':
                    doi = article_id.text
                    break
            
            # Extract MeSH terms (keywords)
            mesh_terms = []
            for mesh in article.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    mesh_terms.append(mesh.text)
            
            return {
                'id': f"pubmed_{pmid}",
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'doi': doi,
                'source': 'pubmed',
                'published_date': published_date,
                'year': year,
                'journal': journal,
                'citation_count': None,  # Would need additional API call
                'raw_data': {
                    'pmid': pmid,
                    'journal': journal,
                    'mesh_terms': mesh_terms
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting paper metadata: {e}")
            return None
    
    def get_bci_papers(self, max_results: int = 200) -> List[Dict[str, Any]]:
        """
        Get BCI/Neurotech papers from PubMed
        
        Args:
            max_results: Maximum number of papers to fetch
        
        Returns:
            List of BCI paper metadata
        """
        # BCI-related search queries for PubMed
        bci_queries = [
            "brain computer interface[Title/Abstract]",
            "BCI[Title/Abstract] AND (EEG OR electroencephalography)",
            "neural interface[Title/Abstract]",
            "SSVEP[Title/Abstract] OR P300[Title/Abstract]",
            "motor imagery[Title/Abstract] AND brain",
            "neurotechnology[Title/Abstract]",
            "neural prosthesis[Title/Abstract]"
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
