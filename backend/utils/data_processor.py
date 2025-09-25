"""
Data processing utilities for cleaning and preparing documents
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class DataProcessor:
    """Utility class for processing and cleaning document data"""
    
    def __init__(self):
        # Common patterns for cleaning text
        self.whitespace_pattern = re.compile(r'\s+')
        self.special_chars_pattern = re.compile(r'[^\w\s\-.,;:!?()\[\]{}"\']')
        self.multiple_punctuation = re.compile(r'[.]{2,}')
        
        # BCI-related keywords for filtering
        self.bci_keywords = {
            'brain', 'computer', 'interface', 'bci', 'eeg', 'electroencephalography',
            'neural', 'neurotechnology', 'ssvep', 'p300', 'motor', 'imagery',
            'prosthesis', 'neuroprosthesis', 'brain-machine', 'brain-computer',
            'cortical', 'neural', 'signal', 'processing', 'classification',
            'decoding', 'encoding', 'stimulation', 'feedback', 'control'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        try:
            # Remove extra whitespace
            text = self.whitespace_pattern.sub(' ', text)
            
            # Remove multiple punctuation
            text = self.multiple_punctuation.sub('.', text)
            
            # Strip leading/trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
        
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        try:
            # Convert to lowercase and split
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
                'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            # Count word frequencies
            word_counts = {}
            for word in words:
                if len(word) > 2 and word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Sort by frequency and return top keywords
            keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            return [word for word, count in keywords[:max_keywords]]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def is_bci_related(self, text: str, threshold: float = 0.05) -> bool:
        """
        Check if text is BCI-related based on keyword presence
        
        Args:
            text: Text to analyze
            threshold: Minimum ratio of BCI keywords to total words
        
        Returns:
            True if text appears to be BCI-related
        """
        if not text:
            return False
        
        try:
            # Extract words
            words = re.findall(r'\b\w+\b', text.lower())
            
            if not words:
                return False
            
            # Count BCI keywords
            bci_word_count = sum(1 for word in words if word in self.bci_keywords)
            
            # Check if ratio exceeds threshold
            ratio = bci_word_count / len(words)
            return ratio >= threshold
            
        except Exception as e:
            logger.error(f"Error checking BCI relevance: {e}")
            return False
    
    def validate_paper_metadata(self, paper: Dict[str, Any]) -> bool:
        """
        Validate paper metadata
        
        Args:
            paper: Paper metadata dictionary
        
        Returns:
            True if paper metadata is valid
        """
        try:
            # Check required fields
            required_fields = ['id', 'title', 'abstract']
            for field in required_fields:
                if not paper.get(field):
                    logger.warning(f"Paper missing required field: {field}")
                    return False
            
            # Check title length
            if len(paper['title']) < 10:
                logger.warning(f"Paper title too short: {paper['title']}")
                return False
            
            # Check abstract length
            if len(paper['abstract']) < 50:
                logger.warning(f"Paper abstract too short: {paper['abstract'][:100]}...")
                return False
            
            # Check if BCI-related
            combined_text = f"{paper['title']} {paper['abstract']}"
            if not self.is_bci_related(combined_text):
                logger.warning(f"Paper not BCI-related: {paper['title']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating paper metadata: {e}")
            return False
    
    def process_paper(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and clean a single paper
        
        Args:
            paper: Raw paper metadata
        
        Returns:
            Processed paper metadata or None if invalid
        """
        try:
            # Clean text fields
            processed_paper = paper.copy()
            processed_paper['title'] = self.clean_text(paper.get('title', ''))
            processed_paper['abstract'] = self.clean_text(paper.get('abstract', ''))
            
            # Clean authors list
            authors = paper.get('authors', [])
            if isinstance(authors, list):
                processed_paper['authors'] = [self.clean_text(author) for author in authors if author]
            else:
                processed_paper['authors'] = []
            
            # Extract keywords
            combined_text = f"{processed_paper['title']} {processed_paper['abstract']}"
            processed_paper['keywords'] = self.extract_keywords(combined_text)
            
            # Add processing metadata
            processed_paper['processed_at'] = datetime.now().isoformat()
            processed_paper['text_hash'] = hashlib.md5(combined_text.encode()).hexdigest()
            
            # Validate
            if not self.validate_paper_metadata(processed_paper):
                return None
            
            return processed_paper
            
        except Exception as e:
            logger.error(f"Error processing paper: {e}")
            return None
    
    def process_papers_batch(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of papers
        
        Args:
            papers: List of raw paper metadata
        
        Returns:
            List of processed paper metadata
        """
        processed_papers = []
        
        for i, paper in enumerate(papers):
            try:
                processed_paper = self.process_paper(paper)
                if processed_paper:
                    processed_papers.append(processed_paper)
                else:
                    logger.warning(f"Skipped invalid paper {i+1}: {paper.get('title', 'No title')}")
            except Exception as e:
                logger.error(f"Error processing paper {i+1}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_papers)}/{len(papers)} papers successfully")
        return processed_papers
    
    def deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on title similarity and text hash
        
        Args:
            papers: List of paper metadata
        
        Returns:
            List of unique papers
        """
        seen_hashes = set()
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            # Check text hash
            text_hash = paper.get('text_hash')
            if text_hash and text_hash in seen_hashes:
                continue
            
            # Check title similarity (normalized)
            title = paper.get('title', '').lower().strip()
            if title in seen_titles:
                continue
            
            # Add to seen sets
            if text_hash:
                seen_hashes.add(text_hash)
            seen_titles.add(title)
            
            unique_papers.append(paper)
        
        logger.info(f"Removed {len(papers) - len(unique_papers)} duplicate papers")
        return unique_papers
    
    def filter_by_date_range(
        self, 
        papers: List[Dict[str, Any]], 
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter papers by date range
        
        Args:
            papers: List of paper metadata
            start_year: Start year (inclusive)
            end_year: End year (inclusive)
        
        Returns:
            Filtered list of papers
        """
        if not start_year and not end_year:
            return papers
        
        filtered_papers = []
        
        for paper in papers:
            year = paper.get('year')
            if not year:
                continue
            
            if start_year and year < start_year:
                continue
            
            if end_year and year > end_year:
                continue
            
            filtered_papers.append(paper)
        
        logger.info(f"Filtered to {len(filtered_papers)} papers by date range")
        return filtered_papers
    
    def get_processing_stats(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about processed papers
        
        Args:
            papers: List of processed papers
        
        Returns:
            Statistics dictionary
        """
        if not papers:
            return {}
        
        try:
            # Count by source
            sources = {}
            years = {}
            total_authors = 0
            total_keywords = 0
            
            for paper in papers:
                source = paper.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
                
                year = paper.get('year')
                if year:
                    years[year] = years.get(year, 0) + 1
                
                authors = paper.get('authors', [])
                total_authors += len(authors)
                
                keywords = paper.get('keywords', [])
                total_keywords += len(keywords)
            
            return {
                'total_papers': len(papers),
                'sources': sources,
                'year_range': {
                    'min': min(years.keys()) if years else None,
                    'max': max(years.keys()) if years else None
                },
                'papers_by_year': years,
                'avg_authors_per_paper': total_authors / len(papers) if papers else 0,
                'avg_keywords_per_paper': total_keywords / len(papers) if papers else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating processing stats: {e}")
            return {}
