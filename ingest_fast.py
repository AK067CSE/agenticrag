
"""
Fast Ingestion Script - Optimized for Speed
Uses smaller embedding model and pypdf for faster processing
"""
import os
import json
import logging
import hashlib
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from tqdm import tqdm

import pypdf
import chromadb
from chromadb.utils import embedding_functions

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
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "all-MiniLM-L6-v2"  # Faster than BAAI/bge-base-en-v1.5


@dataclass
class DocumentChunk:
    """Document chunk with metadata"""
    id: str
    content: str
    metadata: dict


class FastPDFProcessor:
    """Fast PDF processor using pypdf"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID for chunk"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        # Split by paragraphs
        paragraphs = [p for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_words = para.split()
            
            if current_size + len(para_words) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap = current_chunk[-self.chunk_overlap:]
                current_chunk = overlap + para_words
                current_size = len(overlap) + len(para_words)
            else:
                current_chunk.extend(para_words)
                current_size += len(para_words)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_pdf(self, file_path: Path) -> List[DocumentChunk]:
        """Process PDF and return chunks"""
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        logger.info(f"📖 Loading PDF from {file_path}")
        reader = pypdf.PdfReader(str(file_path))
        all_chunks = []
        
        logger.info(f"📄 Processing {len(reader.pages)} pages...")
        
        for page_num, page in enumerate(tqdm(reader.pages, desc="Processing pages")):
            # Extract text
            text = page.extract_text() or ""
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split into chunks
            chunks = self._split_text(text)
            
            for chunk_num, chunk_text in enumerate(chunks):
                # Ensure ID is always a string
                chunk_id = str(self._generate_id(f"{file_path}_{page_num}_{chunk_num}"))
                all_chunks.append(DocumentChunk(
                    id=chunk_id,
                    content=chunk_text,
                    metadata={
                        "source": file_path.name,
                        "page": page_num + 1,
                        "chunk_index": len(all_chunks),
                        "chunk_num": chunk_num + 1
                    }
                ))
        
        logger.info(f"✅ Created {len(all_chunks)} chunks")
        return all_chunks


class FastChromaDBManager:
    """Fast ChromaDB manager with optimizations"""
    
    def __init__(self, persist_directory: Path = CHROMA_DIR):
        self.persist_directory = persist_directory
        persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        
        # Use faster, smaller embedding model
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        
        logger.info(f"💾 ChromaDB initialized at {persist_directory}")
    
    def create_collection(self, collection_name: str = COLLECTION_NAME):
        """Create or recreate collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted existing collection: {collection_name}")
        except Exception:
            pass
        
        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"✅ Collection '{collection_name}' ready")
        return collection
    
    def add_chunks(self, chunks: List[DocumentChunk], collection_name: str = COLLECTION_NAME):
        """Add chunks to collection in batches"""
        collection = self.create_collection(collection_name)
        
        batch_size = 100
        total_chunks = len(chunks)
        
        logger.info(f"📝 Adding {total_chunks} chunks to ChromaDB...")
        
        for i in tqdm(range(0, total_chunks, batch_size), desc="Adding to ChromaDB"):
            batch = chunks[i:i + batch_size]
            
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]
            ids = [str(chunk.id) for chunk in batch]  # Ensure IDs are strings
            
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        logger.info(f"✅ Successfully added {total_chunks} chunks to '{collection_name}'")
        return collection


def save_chunks_to_json(chunks: List[DocumentChunk], output_path: Path):
    """Save chunks to JSON file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(c) for c in chunks], f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Saved {len(chunks)} chunks to {output_path}")


def needs_processing(pdf_path: Path, chunks_path: Path) -> bool:
    """Check if PDF needs reprocessing"""
    if not chunks_path.exists():
        return True
    
    # Check if PDF was modified after chunks
    pdf_mtime = pdf_path.stat().st_mtime
    chunks_mtime = chunks_path.stat().st_mtime
    return pdf_mtime > chunks_mtime


def ingest_fast(pdf_path: Path = PDF_PATH, force: bool = False):
    """Fast ingestion pipeline"""
    logger.info("=" * 80)
    logger.info("🚀 Starting FAST Ingestion Pipeline")
    logger.info("=" * 80)
    
    # Check if processing needed
    if not force and not needs_processing(pdf_path, CHUNKS_FILE):
        logger.info("ℹ️  Using existing chunks (PDF unchanged)")
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            chunk_dicts = json.load(f)
            # Ensure IDs are strings when loading from JSON
            chunks = [DocumentChunk(
                id=str(c['id']),
                content=c['content'],
                metadata=c['metadata']
            ) for c in chunk_dicts]
    else:
        # Process PDF
        processor = FastPDFProcessor(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = processor.process_pdf(pdf_path)
        
        # Save chunks
        save_chunks_to_json(chunks, CHUNKS_FILE)
    
    # Build ChromaDB index
    chroma = FastChromaDBManager(CHROMA_DIR)
    chroma.add_chunks(chunks, COLLECTION_NAME)
    
    logger.info("=" * 80)
    logger.info("✅ Fast Ingestion Complete!")
    logger.info(f"   - Chunks: {CHUNKS_FILE}")
    logger.info(f"   - ChromaDB: {CHROMA_DIR}")
    logger.info(f"   - Embedding Model: {EMBED_MODEL} (fast & efficient)")
    logger.info("=" * 80)
    logger.info("💡 You can now run: streamlit run app.py")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast PDF ingestion")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    args = parser.parse_args()
    
    ingest_fast(force=args.force)
