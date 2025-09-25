"""
Background paper fetcher for pre-loading popular BCI topics
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import threading
import time

from data_pipeline import DataPipeline
from utils.cache_service import cache_service

logger = logging.getLogger(__name__)

class BackgroundFetcher:
    """Background service to pre-fetch popular BCI papers"""
    
    def __init__(self):
        self.data_pipeline = DataPipeline()
        self.is_running = False
        self.thread = None
        
        # Popular BCI topics to pre-fetch
        self.popular_topics = [
            "EEG signal processing",
            "BCI rehabilitation",
            "motor imagery classification",
            "P300 speller interface",
            "SSVEP BCI",
            "brain-computer interface applications",
            "neural interface technology",
            "BCI machine learning",
            "EEG feature extraction",
            "BCI user interface"
        ]
    
    def start(self):
        """Start background fetching"""
        if self.is_running:
            logger.info("Background fetcher already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_background_fetch, daemon=True)
        self.thread.start()
        logger.info("Background fetcher started")
    
    def stop(self):
        """Stop background fetching"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background fetcher stopped")
    
    def _run_background_fetch(self):
        """Main background fetching loop"""
        while self.is_running:
            try:
                # Check if we need to fetch more papers
                if self._should_fetch_papers():
                    self._fetch_popular_topics()
                
                # Sleep for 30 minutes before next check
                time.sleep(1800)  # 30 minutes
                
            except Exception as e:
                logger.error(f"Error in background fetcher: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def _should_fetch_papers(self) -> bool:
        """Check if we should fetch more papers"""
        try:
            # Check cache stats
            cache_stats = cache_service.get_cache_stats()
            
            # If we have few cached API responses, fetch more
            if cache_stats.get('type') == 'redis':
                total_keys = cache_stats.get('total_keys', 0)
                return total_keys < 50  # Fetch if we have less than 50 cached responses
            else:
                # For memory cache, always fetch to build up the database
                return True
                
        except Exception as e:
            logger.error(f"Error checking if should fetch papers: {e}")
            return True
    
    def _fetch_popular_topics(self):
        """Fetch papers for popular topics"""
        logger.info("Starting background fetch of popular topics")
        
        for topic in self.popular_topics:
            if not self.is_running:
                break
                
            try:
                # Check if we already have cached results for this topic
                cached_papers = []
                for source in ['arxiv', 'pubmed', 'semantic_scholar']:
                    cached_result = cache_service.get_api_response(source, topic)
                    if cached_result:
                        cached_papers.extend(cached_result)
                
                # If we don't have cached results, fetch them
                if not cached_papers:
                    logger.info(f"Fetching papers for topic: {topic}")
                    self._fetch_topic_papers(topic)
                else:
                    logger.info(f"Topic '{topic}' already cached with {len(cached_papers)} papers")
                
                # Small delay between topics to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error fetching topic '{topic}': {e}")
                continue
        
        logger.info("Background fetch of popular topics completed")
    
    def _fetch_topic_papers(self, topic: str):
        """Fetch papers for a specific topic"""
        try:
            all_papers = []
            
            # Fetch from all sources
            for source in ['arxiv', 'pubmed', 'semantic_scholar']:
                try:
                    if source == 'arxiv':
                        papers = self.data_pipeline.arxiv_client.search_papers(topic, 10)
                    elif source == 'pubmed':
                        papers = self.data_pipeline.pubmed_client.search_papers(topic, 10)
                    elif source == 'semantic_scholar':
                        papers = self.data_pipeline.semantic_client.search_papers(topic, 10)
                    
                    all_papers.extend(papers)
                    
                    # Cache the results
                    cache_service.set_api_response(source, topic, papers)
                    logger.info(f"Cached {len(papers)} papers from {source} for topic '{topic}'")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source} for topic '{topic}': {e}")
                    continue
            
            logger.info(f"Fetched {len(all_papers)} total papers for topic '{topic}'")
            
        except Exception as e:
            logger.error(f"Error fetching papers for topic '{topic}': {e}")
    
    def get_fetch_stats(self) -> Dict[str, Any]:
        """Get background fetcher statistics"""
        try:
            cache_stats = cache_service.get_cache_stats()
            
            return {
                'is_running': self.is_running,
                'popular_topics': len(self.popular_topics),
                'cache_stats': cache_stats,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting fetch stats: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }

# Global background fetcher instance
background_fetcher = BackgroundFetcher()
