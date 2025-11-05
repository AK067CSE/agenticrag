#!/usr/bin/env python3
"""
Advanced Ingestion Script with Dense + Sparse Indexing
- Pre-processes PDF into chunks
- Builds dense vector index (ChromaDB)
- Builds sparse BM25 index
- Saves chunks for hybrid retrieval
"""
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PDF_PATH = Path("../data/nephrology.pdf")
CHROMA_DIR = Path("chroma_db")
CHUNKS_FILE = Path("data/processed/chunks.json")
BM25_INDEX_FILE = Path("data/processed/bm25_index.pkl")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"


def load_and_chunk_pdf(pdf_path: Path) -> List[Dict]:
    """
    Load PDF and split into chunks with metadata
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of chunk dictionaries with content and metadata
    """
    logger.info(f"📖 Loading PDF from {pdf_path.absolute()}")
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path.absolute()}")
    
    # Load PDF
    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()
    logger.info(f"✅ Loaded {len(pages)} pages")
    
    # Split into chunks
    logger.info("✂️  Chunking document...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    docs = splitter.split_documents(pages)
    
    # Convert to dictionary format
    chunks = []
    for i, doc in enumerate(docs):
        chunks.append({
            "id": i,
            "content": doc.page_content,
            "metadata": {
                "source": doc.metadata.get("source", "nephrology.pdf"),
                "page": doc.metadata.get("page", 0),
                "chunk_index": i,
                "start_index": doc.metadata.get("start_index", 0)
            }
        })
    
    logger.info(f"✅ Created {len(chunks)} chunks")
    return chunks


def save_chunks(chunks: List[Dict], output_file: Path) -> None:
    """
    Save chunks to JSON file
    
    Args:
        chunks: List of chunk dictionaries
        output_file: Path to output JSON file
    """
    logger.info(f"💾 Saving chunks to {output_file.absolute()}")
    
    # Create directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Saved {len(chunks)} chunks")


def build_dense_index(chunks: List[Dict], chroma_dir: Path) -> None:
    """
    Build dense vector index using ChromaDB
    
    Args:
        chunks: List of chunk dictionaries
        chroma_dir: Directory for ChromaDB persistence
    """
    logger.info("🔢 Building dense vector index (ChromaDB)...")
    logger.info(f"   This will process {len(chunks)} chunks - may take 2-3 minutes...")
    
    # Wipe old DB for clean slate
    if chroma_dir.exists():
        logger.info("   Removing old index...")
        shutil.rmtree(chroma_dir)
    
    # Prepare documents for Chroma
    from langchain_core.documents import Document
    logger.info("   Preparing documents...")
    documents = [
        Document(
            page_content=chunk["content"],
            metadata=chunk["metadata"]
        )
        for chunk in chunks
    ]
    
    # Create embeddings
    logger.info("   Loading FastEmbed model (first time may download ~100MB)...")
    embeddings = FastEmbedEmbeddings(model_name=EMBED_MODEL)
    
    # Build and persist vector store
    logger.info("   Generating embeddings and building index...")
    logger.info("   ⏳ Please wait... (this takes 2-3 minutes)")
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(chroma_dir)
    )
    vectorstore.persist()
    
    logger.info(f"✅ Dense index built with {len(chunks)} vectors")


def build_sparse_index(chunks: List[Dict], output_file: Path) -> None:
    """
    Build sparse BM25 index
    
    Args:
        chunks: List of chunk dictionaries
        output_file: Path to save BM25 index
    """
    logger.info("📊 Building sparse BM25 index...")
    
    try:
        from rank_bm25 import BM25Okapi
        import pickle
        
        # Create directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Tokenize chunks for BM25
        tokenized_corpus = [chunk["content"].lower().split() for chunk in chunks]
        
        # Build BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Save index and chunks mapping
        index_data = {
            "bm25": bm25,
            "chunk_ids": [chunk["id"] for chunk in chunks]
        }
        
        with open(output_file, 'wb') as f:
            pickle.dump(index_data, f)
        
        logger.info(f"✅ BM25 index built and saved")
        
    except ImportError:
        logger.warning("⚠️  rank-bm25 not installed. Skipping sparse index.")
        logger.warning("   Install with: pip install rank-bm25")


def ingest(pdf_path: Path = PDF_PATH) -> None:
    """
    Main ingestion pipeline
    
    Args:
        pdf_path: Path to PDF file to ingest
    """
    logger.info("=" * 80)
    logger.info("🚀 Starting Advanced RAG Ingestion Pipeline")
    logger.info("=" * 80)
    
    # Step 1: Load and chunk PDF
    chunks = load_and_chunk_pdf(pdf_path)
    
    # Step 2: Save chunks to JSON
    save_chunks(chunks, CHUNKS_FILE)
    
    # Step 3: Build dense vector index
    build_dense_index(chunks, CHROMA_DIR)
    
    # Step 4: Build sparse BM25 index
    build_sparse_index(chunks, BM25_INDEX_FILE)
    
    logger.info("=" * 80)
    logger.info("✅ Ingestion Complete!")
    logger.info(f"   - Chunks: {CHUNKS_FILE.absolute()}")
    logger.info(f"   - Dense Index: {CHROMA_DIR.absolute()}")
    logger.info(f"   - Sparse Index: {BM25_INDEX_FILE.absolute()}")
    logger.info("=" * 80)
    logger.info("💡 You can now run: streamlit run app.py")
    logger.info("=" * 80)


if __name__ == "__main__":
    ingest()
