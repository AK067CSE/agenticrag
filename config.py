"""
Configuration Settings for Post Discharge Medical AI Assistant
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

# Data Files
PATIENTS_JSON = DATA_DIR / "patients.json"
NEPHROLOGY_PDF = DATA_DIR / "nephrology.pdf"

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Validate API keys
if not GROQ_API_KEY:
    print("⚠️  WARNING: GROQ_API_KEY not found in .env file")
    print("   All agents (Receptionist, Clinical, Web Search) use Groq LLM")
    print("   Please add: GROQ_API_KEY=your_key_here to .env")

if not GOOGLE_API_KEY:
    print("ℹ️  Note: GOOGLE_API_KEY not set (optional, Groq is primary LLM)")

# Model Configuration
GEMINI_MODEL = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_EMBEDDINGS_MODEL = "models/text-embedding-004"
GROQ_MODEL = "llama-3.3-70b-versatile"

# RAG Configuration - Using Local Vector Stores
VECTOR_STORE_TYPE = "chromadb"  # Options: "chromadb" or "faiss"
COLLECTION_NAME = "nephrology_knowledge_base"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SIMILARITY_THRESHOLD = 0.7
TOP_K_RESULTS = 5

# ChromaDB Configuration (Local)
CHROMA_PERSIST_DIR = str(CHROMA_DIR)

# FAISS Configuration (Local)
FAISS_INDEX_DIR = BASE_DIR / "faiss_index"
FAISS_INDEX_DIR.mkdir(exist_ok=True)
FAISS_INDEX_PATH = str(FAISS_INDEX_DIR / "nephrology_index")

# Agent Configuration
TEMPERATURE = 0.7
MAX_TOKENS = 2048

# Medical Disclaimer
MEDICAL_DISCLAIMER = """
⚠️ IMPORTANT DISCLAIMER:
This is an AI assistant for educational purposes only. The information provided should not be 
considered as medical advice. Always consult with qualified healthcare professionals for personal 
medical advice, diagnosis, or treatment.
"""

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
