"""
Main data pipeline for fetching, processing, and indexing BCI literature
"""

import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import argparse

from data_sources.arxiv_client import ArxivClient
from data_sources.pubmed_client import PubMedClient
from data_sources.semantic_scholar_client import SemanticScholarClient
from vector_store.faiss_store import FAISSVectorStore
from utils.data_processor import DataProcessor
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

class DataPipeline:
    """Main data pipeline for BCI literature processing"""
    
    def __init__(self):
        self.arxiv_client = ArxivClient()
        self.pubmed_client = PubMedClient()
        self.semantic_client = SemanticScholarClient()
        self.vector_store = FAISSVectorStore(
            embedding_model=settings.EMBEDDING_MODEL,
            vector_dimension=settings.VECTOR_DIMENSION,
            index_path=os.path.join(settings.DATA_DIR, "vector_store/faiss_index"),
            metadata_path=os.path.join(settings.DATA_DIR, "vector_store/metadata.json")
        )
        self.data_processor = DataProcessor()
        
        # Create data directory
        os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    def fetch_papers_from_sources(
        self, 
        max_papers_per_source: int = 100,
        sources: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch papers from all configured sources
        
        Args:
            max_papers_per_source: Maximum papers to fetch per source
            sources: List of sources to fetch from (None = all sources)
        
        Returns:
            List of fetched papers
        """
        if sources is None:
            sources = ['arxiv', 'pubmed', 'semantic_scholar']
        
        all_papers = []
        
        try:
            # Fetch from arXiv
            if 'arxiv' in sources:
                logger.info("Fetching papers from arXiv...")
                arxiv_papers = self.arxiv_client.get_bci_papers(max_papers_per_source)
                all_papers.extend(arxiv_papers)
                logger.info(f"Fetched {len(arxiv_papers)} papers from arXiv")
            
            # Fetch from PubMed
            if 'pubmed' in sources:
                logger.info("Fetching papers from PubMed...")
                pubmed_papers = self.pubmed_client.get_bci_papers(max_papers_per_source)
                all_papers.extend(pubmed_papers)
                logger.info(f"Fetched {len(pubmed_papers)} papers from PubMed")
            
            # Fetch from Semantic Scholar
            if 'semantic_scholar' in sources:
                logger.info("Fetching papers from Semantic Scholar...")
                semantic_papers = self.semantic_client.get_bci_papers(max_papers_per_source)
                all_papers.extend(semantic_papers)
                logger.info(f"Fetched {len(semantic_papers)} papers from Semantic Scholar")
            
            logger.info(f"Total papers fetched: {len(all_papers)}")
            return all_papers
            
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return []
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean fetched papers
        
        Args:
            papers: List of raw papers
        
        Returns:
            List of processed papers
        """
        try:
            logger.info(f"Processing {len(papers)} papers...")
            
            # Process papers
            processed_papers = self.data_processor.process_papers_batch(papers)
            
            # Remove duplicates
            unique_papers = self.data_processor.deduplicate_papers(processed_papers)
            
            # Get processing statistics
            stats = self.data_processor.get_processing_stats(unique_papers)
            logger.info(f"Processing stats: {json.dumps(stats, indent=2)}")
            
            return unique_papers
            
        except Exception as e:
            logger.error(f"Error processing papers: {e}")
            return []
    
    def index_papers(self, papers: List[Dict[str, Any]]) -> bool:
        """
        Index papers in the vector store
        
        Args:
            papers: List of processed papers
        
        Returns:
            True if indexing successful
        """
        try:
            if not papers:
                logger.warning("No papers to index")
                return False
            
            logger.info(f"Indexing {len(papers)} papers in vector store...")
            
            # Add documents to vector store
            added_count = self.vector_store.add_documents(papers)
            
            # Save the index
            self.vector_store.save_index()
            
            # Get vector store statistics
            stats = self.vector_store.get_stats()
            logger.info(f"Vector store stats: {json.dumps(stats, indent=2)}")
            
            logger.info(f"Successfully indexed {added_count} papers")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing papers: {e}")
            return False
    
    def run_full_pipeline(
        self, 
        max_papers_per_source: int = 100,
        sources: List[str] = None,
        save_raw_data: bool = True
    ) -> bool:
        """
        Run the complete data pipeline
        
        Args:
            max_papers_per_source: Maximum papers to fetch per source
            sources: List of sources to fetch from
            save_raw_data: Whether to save raw fetched data
        
        Returns:
            True if pipeline completed successfully
        """
        try:
            logger.info("Starting BCI literature data pipeline...")
            start_time = datetime.now()
            
            # Step 1: Fetch papers
            papers = self.fetch_papers_from_sources(max_papers_per_source, sources)
            
            if not papers:
                logger.error("No papers fetched from sources")
                return False
            
            # Save raw data if requested
            if save_raw_data:
                raw_data_path = os.path.join(settings.DATA_DIR, f"raw_papers_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
                with open(raw_data_path, 'w', encoding='utf-8') as f:
                    json.dump(papers, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved raw data to {raw_data_path}")
            
            # Step 2: Process papers
            processed_papers = self.process_papers(papers)
            
            if not processed_papers:
                logger.error("No papers processed successfully")
                return False
            
            # Step 3: Index papers
            success = self.index_papers(processed_papers)
            
            if success:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
                logger.info(f"Processed {len(processed_papers)} papers from {len(papers)} fetched")
                return True
            else:
                logger.error("Failed to index papers")
                return False
                
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False
    
    def test_vector_store(self) -> bool:
        """Test the vector store with a sample query"""
        try:
            logger.info("Testing vector store...")
            
            # Test query
            test_query = "SSVEP brain computer interface"
            results = self.vector_store.search(test_query, top_k=5)
            
            if results:
                logger.info(f"Vector store test successful. Found {len(results)} results for query: '{test_query}'")
                for i, result in enumerate(results[:3]):
                    logger.info(f"  {i+1}. {result['title'][:80]}... (score: {result['similarity_score']:.3f})")
                return True
            else:
                logger.warning("Vector store test returned no results")
                return False
                
        except Exception as e:
            logger.error(f"Vector store test failed: {e}")
            return False

def main():
    """Main entry point for the data pipeline"""
    parser = argparse.ArgumentParser(description='BCI Literature Data Pipeline')
    parser.add_argument('--max-papers', type=int, default=100, help='Maximum papers per source')
    parser.add_argument('--sources', nargs='+', choices=['arxiv', 'pubmed', 'semantic_scholar'], 
                       default=['arxiv'], help='Data sources to use')
    parser.add_argument('--test-only', action='store_true', help='Only test vector store')
    parser.add_argument('--no-save-raw', action='store_true', help='Do not save raw data')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = DataPipeline()
    
    if args.test_only:
        # Test vector store only
        success = pipeline.test_vector_store()
        exit(0 if success else 1)
    else:
        # Run full pipeline
        success = pipeline.run_full_pipeline(
            max_papers_per_source=args.max_papers,
            sources=args.sources,
            save_raw_data=not args.no_save_raw
        )
        exit(0 if success else 1)

if __name__ == "__main__":
    main()
