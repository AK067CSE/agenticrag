"""
Fast RAG Engine - Optimized for Speed
Uses smaller embedding model (all-MiniLM-L6-v2) for faster retrieval
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging

import chromadb
from chromadb.utils import embedding_functions

# Configuration
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "all-MiniLM-L6-v2"  # Fast & efficient
TOP_K = 5
SIMILARITY_THRESHOLD = 0.5

logger = logging.getLogger(__name__)

# Global singleton
_rag_engine: Optional['FastRAGEngine'] = None


class FastRAGEngine:
    """Fast RAG Engine with ChromaDB"""
    
    def __init__(self):
        """Initialize the RAG engine"""
        self._client = None
        self._collection = None
        self._embedding_function = None
        
        logger.info("🔧 Initializing Fast RAG Engine...")
        self._load_resources()
        logger.info("✅ Fast RAG Engine ready")
    
    def _load_resources(self) -> None:
        """Load ChromaDB resources"""
        if not CHROMA_DIR.exists():
            raise RuntimeError(
                f"ChromaDB not found at {CHROMA_DIR.absolute()}. "
                "Please run 'python ingest_fast.py' first."
            )
        
        logger.info("🔗 Loading ChromaDB...")
        
        # Initialize client
        self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        
        # Initialize embedding function
        self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        
        # Get collection
        try:
            self._collection = self._client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embedding_function
            )
            doc_count = self._collection.count()
            logger.info(f"📚 Loaded collection with {doc_count} documents")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load collection '{COLLECTION_NAME}': {e}. "
                "Please run 'python ingest_fast.py' first."
            )
    
    def retrieve(
        self,
        query: str,
        k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD
    ) -> List[Dict]:
        """
        Retrieve relevant documents
        
        Args:
            query: Search query
            k: Number of results
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of documents with content, metadata, and scores
        """
        logger.info(f"🔍 Retrieving for: {query[:100]}...")
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=k
            )
            
            if not results or not results['documents'] or not results['documents'][0]:
                logger.info("❌ No results found")
                return []
            
            # Parse results
            documents = []
            for i in range(len(results['documents'][0])):
                # ChromaDB returns distances, convert to similarity (1 - distance)
                distance = results['distances'][0][i] if 'distances' in results else 0
                similarity = 1.0 - distance
                
                # Filter by threshold
                if similarity >= threshold:
                    documents.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results else {},
                        'relevance_score': similarity,
                        'id': results['ids'][0][i] if 'ids' in results else f"doc_{i}"
                    })
            
            logger.info(f"✅ Found {len(documents)} documents above threshold {threshold}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return []
    
    def get_context_for_query(
        self,
        query: str,
        k: int = TOP_K,
        threshold: float = SIMILARITY_THRESHOLD
    ) -> str:
        """
        Get formatted context string for a query
        
        Args:
            query: Search query
            k: Number of results
            threshold: Minimum similarity
            
        Returns:
            Formatted context with citations
        """
        docs = self.retrieve(query, k, threshold)
        
        if not docs:
            return ""
        
        # Format with citations
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc['metadata'].get('source', 'nephrology.pdf')
            page = doc['metadata'].get('page', '?')
            score = doc['relevance_score']
            
            context_parts.append(
                f"[Source {i} - {source} (Page {page}), Relevance: {score:.3f}]\n"
                f"{doc['content']}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def has_relevant_information(
        self,
        query: str,
        threshold: float = SIMILARITY_THRESHOLD
    ) -> bool:
        """
        Check if relevant information exists
        
        Args:
            query: Search query
            threshold: Minimum relevance threshold
            
        Returns:
            True if relevant docs found
        """
        results = self.retrieve(query, k=1, threshold=threshold)
        return len(results) > 0


# Singleton pattern
def get_rag_engine() -> FastRAGEngine:
    """Get or create the global RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = FastRAGEngine()
    return _rag_engine


# Convenience functions for backward compatibility
def retrieve_relevant_docs(query: str, k: int = TOP_K) -> List[Dict]:
    """Retrieve relevant documents"""
    engine = get_rag_engine()
    return engine.retrieve(query, k)


def get_context_for_query(query: str, k: int = TOP_K) -> str:
    """Get context for query"""
    engine = get_rag_engine()
    return engine.get_context_for_query(query, k)


def has_relevant_information(query: str, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """Check if relevant information exists"""
    engine = get_rag_engine()
    return engine.has_relevant_information(query, threshold)


# Test function
if __name__ == "__main__":
    print("🧪 Testing Fast RAG Engine")
    print("=" * 80)
    
    engine = get_rag_engine()
    
    test_query = "What is chronic kidney disease?"
    print(f"\n🔎 Query: {test_query}")
    print("-" * 80)
    
    # Retrieve documents
    docs = engine.retrieve(test_query, k=3)
    
    if docs:
        print(f"\n✅ Found {len(docs)} relevant documents:\n")
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}:")
            print(f"  Page: {doc['metadata'].get('page', 'N/A')}")
            print(f"  Score: {doc['relevance_score']:.3f}")
            print(f"  Content: {doc['content'][:200]}...")
            print()
    else:
        print("❌ No documents found")
    
    # Get formatted context
    print("\n📄 Formatted Context:")
    print("-" * 80)
    context = engine.get_context_for_query(test_query, k=2)
    print(context[:500] + "..." if len(context) > 500 else context)
