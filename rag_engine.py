"""
RAG Engine for Nephrology Knowledge Base - Search Only
This is a lightweight version that only performs searches against a pre-built vector store.
"""
from pathlib import Path
from typing import List, Dict
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Configuration
CHROMA_DIR = Path("chroma_db")
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
TOP_K = 5
SIMILARITY_THRESHOLD = 0.7  # optional filter

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Lazy singleton – loads DB on first call
# --------------------------------------------------
_vectorstore = None

def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        if not CHROMA_DIR.exists():
            raise RuntimeError(
                f"Vector DB not found at {CHROMA_DIR.absolute()}.  "
                "Please run 'python ingest.py' first."
            )
        logger.info("🔗 Loading existing Chroma DB …")
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=FastEmbedEmbeddings(model_name=EMBED_MODEL),
            persist_directory=str(CHROMA_DIR)
        )
    return _vectorstore

# --------------------------------------------------
# Public helpers – drop-in compatible
# --------------------------------------------------
def retrieve_relevant_docs(query: str, k: int = TOP_K) -> List[Dict]:
    """
    Retrieve relevant documents for a query
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        List of relevant documents with content and metadata
    """
    store = _get_vectorstore()
    docs = store.similarity_search_with_score(query, k=k)
    
    filtered = []
    for doc, score in docs:
        # Convert score to similarity (1.0 - distance)
        similarity = 1.0 - min(max(score, 0.0), 1.0)
        if similarity >= SIMILARITY_THRESHOLD:
            filtered.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": similarity
            })
    
    logger.info("📄 %d chunks passed threshold for query: %.100s …", len(filtered), query)
    return filtered

def get_context_for_query(query: str, k: int = TOP_K) -> str:
    """
    Get formatted context string for a query
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        Formatted context string with source citations
    """
    docs = retrieve_relevant_docs(query, k)
    if not docs:
        return ""
        
    # Simple concat with source line
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc['metadata'].get('source', 'nephrology.pdf')
        page = doc['metadata'].get('page', '?')
        parts.append(f"[Source {i}: {source} (page {page})]\n{doc['content']}")
    
    return "\n\n---\n\n".join(parts)

def has_relevant_information(query: str) -> bool:
    """
    Check if there's relevant information for the query
    
    Args:
        query: Search query
        
    Returns:
        True if relevant documents found, False otherwise
    """
    return len(retrieve_relevant_docs(query, k=1)) > 0

# For backward compatibility
search_nephrology_knowledge = get_context_for_query
