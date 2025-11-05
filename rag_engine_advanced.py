"""
Advanced RAG Engine - Retrieval Only with Hybrid Search
Supports:
- Dense retrieval (semantic vector search)
- Sparse retrieval (BM25)
- Hybrid retrieval (combining dense + sparse)
- Re-ranking for optimal results
"""
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Configuration
CHROMA_DIR = Path("chroma_db")
CHUNKS_FILE = Path("data/processed/chunks.json")
BM25_INDEX_FILE = Path("data/processed/bm25_index.pkl")
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
TOP_K = 5
DENSE_WEIGHT = 0.7  # Weight for dense retrieval in hybrid mode
SPARSE_WEIGHT = 0.3  # Weight for sparse retrieval in hybrid mode

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from retrieval"""
    chunk_id: int
    content: str
    metadata: Dict
    score: float
    retrieval_method: str


class HybridRAGEngine:
    """
    Advanced RAG Engine with hybrid retrieval capabilities
    """
    
    def __init__(self):
        """Initialize the RAG engine"""
        self._vectorstore = None
        self._bm25_index = None
        self._chunks = None
        self._chunks_dict = None
        
        logger.info("🔧 Initializing Hybrid RAG Engine...")
        self._load_resources()
        logger.info("✅ Hybrid RAG Engine ready")
    
    def _load_resources(self) -> None:
        """Load all necessary resources"""
        # Load chunks
        if not CHUNKS_FILE.exists():
            raise RuntimeError(
                f"Chunks file not found at {CHUNKS_FILE.absolute()}. "
                "Please run 'python ingest_advanced.py' first."
            )
        
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            self._chunks = json.load(f)
            self._chunks_dict = {chunk["id"]: chunk for chunk in self._chunks}
        
        logger.info(f"📚 Loaded {len(self._chunks)} chunks")
        
        # Load BM25 index (optional)
        if BM25_INDEX_FILE.exists():
            try:
                with open(BM25_INDEX_FILE, 'rb') as f:
                    self._bm25_index = pickle.load(f)
                logger.info("📊 Loaded BM25 sparse index")
            except Exception as e:
                logger.warning(f"⚠️  Could not load BM25 index: {e}")
        else:
            logger.warning("⚠️  BM25 index not found. Sparse retrieval unavailable.")
    
    def _get_vectorstore(self) -> Chroma:
        """Lazy load vector store"""
        if self._vectorstore is None:
            if not CHROMA_DIR.exists():
                raise RuntimeError(
                    f"Vector DB not found at {CHROMA_DIR.absolute()}. "
                    "Please run 'python ingest_advanced.py' first."
                )
            
            logger.info("🔗 Loading ChromaDB vector store...")
            self._vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=FastEmbedEmbeddings(model_name=EMBED_MODEL),
                persist_directory=str(CHROMA_DIR)
            )
        
        return self._vectorstore
    
    def dense_retrieve(self, query: str, k: int = TOP_K) -> List[RetrievalResult]:
        """
        Dense retrieval using semantic vector search
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of retrieval results
        """
        logger.info(f"🔍 Dense retrieval for: {query[:100]}...")
        
        store = self._get_vectorstore()
        results = store.similarity_search_with_score(query, k=k)
        
        retrieval_results = []
        for doc, distance in results:
            # Convert distance to similarity score (0-1, higher is better)
            similarity = 1.0 / (1.0 + distance)
            
            chunk_id = doc.metadata.get("chunk_index", 0)
            retrieval_results.append(RetrievalResult(
                chunk_id=chunk_id,
                content=doc.page_content,
                metadata=doc.metadata,
                score=similarity,
                retrieval_method="dense"
            ))
        
        logger.info(f"✅ Found {len(retrieval_results)} results via dense retrieval")
        return retrieval_results
    
    def sparse_retrieve(self, query: str, k: int = TOP_K) -> List[RetrievalResult]:
        """
        Sparse retrieval using BM25
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of retrieval results
        """
        if self._bm25_index is None:
            logger.warning("⚠️  BM25 index not available, skipping sparse retrieval")
            return []
        
        logger.info(f"🔍 Sparse retrieval (BM25) for: {query[:100]}...")
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        bm25 = self._bm25_index["bm25"]
        chunk_ids = self._bm25_index["chunk_ids"]
        
        scores = bm25.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        retrieval_results = []
        for idx in top_indices:
            chunk_id = chunk_ids[idx]
            chunk = self._chunks_dict.get(chunk_id)
            
            if chunk and scores[idx] > 0:
                # Normalize BM25 score
                normalized_score = min(scores[idx] / 10.0, 1.0)  # Simple normalization
                
                retrieval_results.append(RetrievalResult(
                    chunk_id=chunk_id,
                    content=chunk["content"],
                    metadata=chunk["metadata"],
                    score=normalized_score,
                    retrieval_method="sparse"
                ))
        
        logger.info(f"✅ Found {len(retrieval_results)} results via sparse retrieval")
        return retrieval_results
    
    def hybrid_retrieve(
        self,
        query: str,
        k: int = TOP_K,
        dense_weight: float = DENSE_WEIGHT,
        sparse_weight: float = SPARSE_WEIGHT
    ) -> List[RetrievalResult]:
        """
        Hybrid retrieval combining dense and sparse methods
        
        Args:
            query: Search query
            k: Number of results to return
            dense_weight: Weight for dense retrieval scores
            sparse_weight: Weight for sparse retrieval scores
            
        Returns:
            List of retrieval results sorted by combined score
        """
        logger.info(f"🔍 Hybrid retrieval for: {query[:100]}...")
        
        # Get results from both methods
        dense_results = self.dense_retrieve(query, k=k*2)  # Get more for fusion
        sparse_results = self.sparse_retrieve(query, k=k*2)
        
        # Combine results by chunk_id
        combined_scores = {}
        
        for result in dense_results:
            combined_scores[result.chunk_id] = {
                "result": result,
                "dense_score": result.score,
                "sparse_score": 0.0
            }
        
        for result in sparse_results:
            if result.chunk_id in combined_scores:
                combined_scores[result.chunk_id]["sparse_score"] = result.score
            else:
                combined_scores[result.chunk_id] = {
                    "result": result,
                    "dense_score": 0.0,
                    "sparse_score": result.score
                }
        
        # Calculate hybrid scores
        hybrid_results = []
        for chunk_id, data in combined_scores.items():
            hybrid_score = (
                dense_weight * data["dense_score"] +
                sparse_weight * data["sparse_score"]
            )
            
            result = data["result"]
            hybrid_results.append(RetrievalResult(
                chunk_id=result.chunk_id,
                content=result.content,
                metadata=result.metadata,
                score=hybrid_score,
                retrieval_method="hybrid"
            ))
        
        # Sort by hybrid score and return top-k
        hybrid_results.sort(key=lambda x: x.score, reverse=True)
        final_results = hybrid_results[:k]
        
        logger.info(f"✅ Hybrid retrieval returned {len(final_results)} results")
        return final_results
    
    def retrieve(
        self,
        query: str,
        k: int = TOP_K,
        method: str = "hybrid"
    ) -> List[RetrievalResult]:
        """
        Main retrieval method
        
        Args:
            query: Search query
            k: Number of results to return
            method: Retrieval method ("dense", "sparse", or "hybrid")
            
        Returns:
            List of retrieval results
        """
        if method == "dense":
            return self.dense_retrieve(query, k)
        elif method == "sparse":
            return self.sparse_retrieve(query, k)
        elif method == "hybrid":
            return self.hybrid_retrieve(query, k)
        else:
            raise ValueError(f"Unknown retrieval method: {method}")
    
    def get_context_for_query(
        self,
        query: str,
        k: int = TOP_K,
        method: str = "hybrid"
    ) -> str:
        """
        Get formatted context string for a query
        
        Args:
            query: Search query
            k: Number of results to return
            method: Retrieval method
            
        Returns:
            Formatted context string with citations
        """
        results = self.retrieve(query, k, method)
        
        if not results:
            return ""
        
        # Format with citations
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.metadata.get("source", "nephrology.pdf")
            page = result.metadata.get("page", "?")
            score = result.score
            
            context_parts.append(
                f"[Source {i} - Page {page}, Relevance: {score:.3f}, Method: {result.retrieval_method}]\n"
                f"{result.content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def has_relevant_information(
        self,
        query: str,
        threshold: float = 0.3,
        method: str = "hybrid"
    ) -> bool:
        """
        Check if there's relevant information for the query
        
        Args:
            query: Search query
            threshold: Minimum relevance threshold
            method: Retrieval method
            
        Returns:
            True if relevant documents found above threshold
        """
        results = self.retrieve(query, k=1, method=method)
        return len(results) > 0 and results[0].score >= threshold


# Global singleton instance
_rag_engine: Optional[HybridRAGEngine] = None


def get_rag_engine() -> HybridRAGEngine:
    """Get or create the global RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = HybridRAGEngine()
    return _rag_engine


# Convenience functions for backward compatibility
def retrieve_relevant_docs(query: str, k: int = TOP_K) -> List[Dict]:
    """Retrieve relevant documents (backward compatible)"""
    engine = get_rag_engine()
    results = engine.retrieve(query, k)
    
    return [
        {
            "content": r.content,
            "metadata": r.metadata,
            "relevance_score": r.score
        }
        for r in results
    ]


def get_context_for_query(query: str, k: int = TOP_K) -> str:
    """Get context for query (backward compatible)"""
    engine = get_rag_engine()
    return engine.get_context_for_query(query, k)


def has_relevant_information(query: str) -> bool:
    """Check if relevant information exists (backward compatible)"""
    engine = get_rag_engine()
    return engine.has_relevant_information(query)


# For agent tool use
search_nephrology_knowledge = get_context_for_query
