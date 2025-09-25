"""
FAISS vector store implementation for document embeddings
"""

import faiss
import numpy as np
import pickle
import json
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
from sentence_transformers import SentenceTransformer
import hashlib

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    """FAISS-based vector store for document embeddings"""
    
    def __init__(
        self, 
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        vector_dimension: int = 384,
        index_path: str = "data/vector_store/faiss_index",
        metadata_path: str = "data/vector_store/metadata.json"
    ):
        self.embedding_model_name = embedding_model
        self.vector_dimension = vector_dimension
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Initialize embedding model
        self.embedding_model = None
        self.index = None
        self.metadata = []
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        try:
            if os.path.exists(f"{self.index_path}.index") and os.path.exists(self.metadata_path):
                self._load_index()
                logger.info(f"Loaded existing FAISS index with {len(self.metadata)} documents")
            else:
                self._create_new_index()
                logger.info("Created new FAISS index")
        except Exception as e:
            logger.error(f"Error loading/creating index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.vector_dimension)
        self.metadata = []
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{self.index_path}.index")
            
            # Load metadata
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            # Load embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, f"{self.index_path}.index")
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved FAISS index with {len(self.metadata)} documents")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document dictionaries with 'text' and 'metadata' keys
        
        Returns:
            Number of documents added
        """
        if not documents:
            return 0
        
        try:
            # Extract texts for embedding
            texts = []
            for doc in documents:
                # Combine title and abstract for embedding
                text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
                texts.append(text.strip())
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Add metadata
            for i, doc in enumerate(documents):
                doc_metadata = {
                    'id': doc.get('id', f"doc_{len(self.metadata)}"),
                    'title': doc.get('title', ''),
                    'authors': doc.get('authors', []),
                    'abstract': doc.get('abstract', ''),
                    'url': doc.get('url', ''),
                    'doi': doc.get('doi', ''),
                    'source': doc.get('source', ''),
                    'year': doc.get('year'),
                    'published_date': doc.get('published_date'),
                    'citation_count': doc.get('citation_count'),
                    'text_hash': hashlib.md5(texts[i].encode()).hexdigest(),
                    'index': len(self.metadata)
                }
                self.metadata.append(doc_metadata)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            # Get results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                if idx >= len(self.metadata):
                    continue
                
                doc_metadata = self.metadata[idx].copy()
                doc_metadata['similarity_score'] = float(score)
                doc_metadata['distance'] = float(score)
                
                # Apply metadata filters if provided
                if filter_metadata and not self._matches_filter(doc_metadata, filter_metadata):
                    continue
                
                results.append(doc_metadata)
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def _matches_filter(self, doc_metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if document matches metadata filter"""
        for key, value in filter_metadata.items():
            if key not in doc_metadata:
                return False
            
            doc_value = doc_metadata[key]
            
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
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        for doc in self.metadata:
            if doc['id'] == doc_id:
                return doc
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.metadata),
            'vector_dimension': self.vector_dimension,
            'embedding_model': self.embedding_model_name,
            'index_type': 'FAISS IndexFlatL2',
            'sources': list(set(doc['source'] for doc in self.metadata)),
            'years': list(set(doc['year'] for doc in self.metadata if doc['year']))
        }
    
    def clear(self):
        """Clear all documents from the vector store"""
        self._create_new_index()
        logger.info("Cleared vector store")
    
    def rebuild_index(self):
        """Rebuild the FAISS index from metadata"""
        if not self.metadata:
            logger.warning("No metadata to rebuild index from")
            return
        
        try:
            # Extract texts from metadata
            texts = []
            for doc in self.metadata:
                text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
                texts.append(text.strip())
            
            # Generate embeddings
            logger.info(f"Rebuilding index for {len(texts)} documents")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            
            # Create new index
            self.index = faiss.IndexFlatL2(self.vector_dimension)
            self.index.add(embeddings.astype('float32'))
            
            logger.info("Successfully rebuilt FAISS index")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            raise
    
    # Sprint 5 Methods for Advanced Features
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Get all papers from the vector store"""
        return self.metadata.copy()
    
    def get_embedding(self, doc_id: str) -> Optional[np.ndarray]:
        """Get embedding for a specific document by ID"""
        try:
            # Find the document in metadata
            doc_index = None
            for i, doc in enumerate(self.metadata):
                if doc['id'] == doc_id:
                    doc_index = i
                    break
            
            if doc_index is None:
                return None
            
            # Get the embedding from the FAISS index
            if self.index.ntotal > doc_index:
                # FAISS doesn't have a direct way to get a single vector
                # We'll need to reconstruct it from the text
                doc = self.metadata[doc_index]
                text = f"{doc.get('title', '')} {doc.get('abstract', '')}"
                embedding = self.embedding_model.encode([text])
                return embedding[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting embedding for {doc_id}: {e}")
            return None