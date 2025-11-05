#currently not used but we can utilize it 
import os
import uuid
import uvicorn
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
from agent_orchestrator import orchestrator
from logger import log_event
from utils import load_and_chunk_pdf, build_or_load_chroma
import shutil
from fastapi import UploadFile, File
from fastapi.responses import FileResponse

# Load environment variables
load_dotenv()

# ----------------------------
# 1. Startup
# ----------------------------
def init_patient_db():
    pass

# Preload and ingest the default PDF if it exists
def preload_pdf():
    import time
    
    default_pdf = "data/nephrology.pdf"
    chroma_dir = "chroma_db"
    
    if not os.path.exists(default_pdf):
        log_event("[Startup] Default PDF not found, skipping preload")
        return
        
    try:
        log_event("[Startup] Preloading default PDF...")
        
        # Do not delete directory; instead rebuild collection safely
        log_event("[Startup] Loading and chunking PDF...")
        try:
            docs = load_and_chunk_pdf()
            log_event(f"[Startup] Loaded {len(docs)} chunks from PDF")
            
            # Force rebuild with the new documents
            vectorstore = build_or_load_chroma(docs, force_rebuild=True)
            
            # Verify documents were added
            if vectorstore is not None:
                try:
                    collection = vectorstore._collection
                    count = collection.count()
                    log_event(f"[Startup] Successfully added {count} documents to ChromaDB")
                    if count > 0:
                        sample = collection.get(limit=1)
                        log_event(f"[Startup] Sample document: {str(sample)[:200]}...")
                except Exception as e:
                    log_event(f"[Startup] Error verifying ChromaDB: {str(e)}")
            
            log_event("[Startup] Default PDF preloaded successfully")
            return True
            
        except Exception as e:
            log_event(f"[Startup] Error preloading PDF: {str(e)}")
            import traceback
            log_event(f"[Startup] Traceback: {traceback.format_exc()}")
            return False
    except Exception as e:
        log_event(f"[Startup] Unexpected error in preload_pdf: {str(e)}")
        import traceback
        log_event(f"[Startup] Traceback: {traceback.format_exc()}")
        return False

preload_pdf()

# ----------------------------
# 2. App
# ----------------------------
app = FastAPI(title="Post-Discharge AI Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import agent AFTER preload so retriever sees a populated vectorstore

# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    patient_context: Optional[dict] = None
    sources: list = []
    timestamp: str

# Routes
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Main chat endpoint that handles all user messages."""
    try:
        response = orchestrator.process_message(
            user_input=chat_request.message,
            session_id=chat_request.session_id or str(uuid.uuid4())
        )
        return {
            "response": response.get("response", "I'm sorry, I couldn't process that."),
            "session_id": chat_request.session_id or str(uuid.uuid4()),
            "patient_context": response.get("patient"),
            "sources": response.get("sources", []),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        log_event(f"[API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# ----------------------------
# 5. PDF Upload Endpoint
# ----------------------------
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save the uploaded file
    dest = "data/uploaded_document.pdf"
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    log_event(f"[API] PDF uploaded: {file.filename}")
    
    try:
        # Process the uploaded PDF
        docs = load_and_chunk_pdf(dest)  # Pass the uploaded file path
        build_or_load_chroma(docs, force_rebuild=True)
        log_event("[API] PDF processed and vectorstore updated")
        return {"detail": "PDF uploaded and processed successfully."}
    except Exception as e:
        log_event(f"[API] Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

# ----------------------------
# 6. Logs Download
# ----------------------------
@app.get("/logs")
def download_logs():
    log_path = "logs/system.log"
    if not os.path.exists(log_path):
        raise HTTPException(status_code=404, detail="No logs found.")
    return FileResponse(log_path, media_type="text/plain", filename="system.log")

# ----------------------------
# 7. Run the server
# ----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
