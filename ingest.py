#!/usr/bin/env python3
"""
ingest.py – one-time ingestion of the nephrology PDF
Usage: python ingest.py
"""
import shutil
import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PDF_PATH = Path("../data/nephrology.pdf")  # Updated path to point to the data directory
CHROMA_DIR = Path("chroma_db")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_NAME = "nephrology_knowledge_base"
EMBED_MODEL = "BAAI/bge-base-en-v1.5"

def ingest() -> None:
    if not PDF_PATH.exists():
        logger.error(f"❗ Place your nephrology PDF at {PDF_PATH.absolute()}")
        exit(1)

    # Wipe old DB for a clean slate
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)

    logger.info("📖 Loading PDF …")
    docs = PyPDFLoader(str(PDF_PATH)).load()

    logger.info("✂️  Chunking …")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True
    )
    chunks = splitter.split_documents(docs)

    logger.info("🔢 Embedding & storing …")
    embeddings = FastEmbedEmbeddings(model_name=EMBED_MODEL)
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR)
    ).persist()

    logger.info(f"✅ Done! {len(chunks)} chunks stored in {CHROMA_DIR.absolute()}")

if __name__ == "__main__":
    ingest()
