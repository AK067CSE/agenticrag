# 🏥 Post-Discharge Medical AI Assistant

**DataSmith AI - GenAI Intern Assignment**

A comprehensive multi-agent AI system for post-discharge patient care, featuring intelligent agent orchestration, RAG-powered clinical information, and web search capabilities.

## 🎯 Overview

This Proof of Concept (POC) demonstrates a production-ready multi-agent AI system that:

- ✅ Manages 25+ patient discharge reports
- ✅ Uses RAG with nephrology reference materials (large PDF textbook)
- ✅ Implements 3 specialized AI agents with intelligent orchestration
- ✅ Provides modern Streamlit web interface
- ✅ Uses **local vector stores** (ChromaDB/FAISS) - No cloud dependencies
- ✅ Includes comprehensive logging system
- ✅ Features web search fallback for queries outside knowledge base

---

## 🤖 Multi-Agent Architecture

### 1. **Receptionist Agent** 🏨
- Greets patients professionally
- Collects patient name
- Retrieves discharge reports from database
- Asks follow-up questions about recovery
- Routes medical queries to Clinical Agent

### 2. **Clinical AI Agent** ⚕️
- Handles medical questions
- Uses RAG over nephrology knowledge base
- Falls back to web search when needed
- Provides source citations
- Offers evidence-based clinical information

### 3. **Web Search Agent** 🌐
- Performs web searches via DuckDuckGo
- Provides latest medical information
- Used when knowledge base lacks coverage
- Includes source URLs and citations

### Multi-Agent Orchestrator 🎭
- Coordinates between all agents
- Manages conversation flow
- Handles agent handoffs
- Tracks patient context
- Logs all interactions

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-Agent Orchestrator                        │
│  - Session Management                                        │
│  - Agent Routing & Handoffs                                  │
│  - Context Management                                        │
└──────┬───────────────────┬────────────────────┬─────────────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│ Receptionist│    │  Clinical AI │    │  Web Search  │
│    Agent    │    │    Agent     │    │    Agent     │
│             │    │              │    │              │
│ - Greeting  │    │ - RAG Engine │    │ - DuckDuckGo │
│ - Patient   │    │ - Medical Q&A│    │ - Groq LLM   │
│   Retrieval │    │ - Citations  │    │ - Citations  │
│ - Routing   │    │ - Fallback   │    │              │
└─────┬───────┘    └──────┬───────┘    └──────────────┘
      │                   │
      ▼                   ▼
┌─────────────┐    ┌──────────────┐
│  Patient    │    │  RAG Engine  │
│  Database   │    │              │
│             │    │ - ChromaDB   │
│ - JSON      │    │   or FAISS   │
│ - 25+ pts   │    │ - Gemini     │
│             │    │   Embeddings │
└─────────────┘    └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Nephrology  │
                   │  PDF (~88MB) │
                   │  Knowledge   │
                   │     Base     │
                   └──────────────┘
```

---

## 📂 Project Structure

```
fresh_system/
├── app.py                          # Streamlit web application
├── multi_agent_orchestrator.py     # Agent coordination & routing
├── receptionist_agent.py           # Patient intake agent
├── clinical_agent.py               # Medical Q&A agent
├── web_search_agent.py             # Web search agent
├── rag_engine.py                   # RAG implementation (ChromaDB/FAISS)
├── patient_retrieval_tool.py       # Patient database access
├── config.py                       # Configuration settings
├── logger_system.py                # Comprehensive logging
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file

Data Files (in parent directory):
├── data/
│   ├── patients.json               # 25+ patient records
│   └── nephrology.pdf              # Reference textbook (~88MB)
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Google Gemini API Key
- Groq API Key

### Step 1: Clone & Navigate
```bash
cd post_discharge_ai_assistant/fresh_system
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure API Keys
1. Copy `.env.example` to `.env`:
   ```bash
   create env
   ```

2. Edit `.env` and add your API keys:
   ```env
   GOOGLE_API_KEY=your_actual_google_api_key
   GROQ_API_KEY=your_actual_groq_api_key
   ```



### Step 4: Verify Data Files
Ensure these files exist in the parent `data/` directory:
- `patients.json` - Patient database this is the dummy data that i have added
- `nephrology.pdf` - Reference textbook your tema's reference book pdf 
- make sure in a data folder keep the patients.json and the pdf 

---

## ▶️ Running the Application

### Start the Streamlit App
```bash
streamlit run app.py
```

The application will:
1. Initialize all three agents
2. Load patient database (25+ records)
3. Process nephrology PDF and create vector embeddings (first run only)
4. Start web interface on `http://localhost:8501`

### First Run Notes
- **Initial startup may take 2-5 minutes** to process the large PDF and create embeddings
- Vector database is persisted locally (ChromaDB or FAISS)
- Subsequent runs will be much faster (loads existing vectors)

---

## 💬 Usage Example

### Sample Conversation Flow

**1. Session Start**
```
System: Hello! 👋 I'm your Post-Discharge Care Assistant.
        What's your name?
```

**2. Patient Identification**
```
User: My name is John Smith

Receptionist: Hi John! I found your discharge report from 2024-01-15 
              for Chronic Kidney Disease Stage 3. How are you feeling today?
```

**3. Follow-up Questions**
```
Receptionist: Are you following your medication schedule?
              Have you been monitoring your blood pressure daily?
```

**4. Medical Query (Routes to Clinical Agent)**
```
User: I'm having swelling in my legs. Should I be worried?

System: Let me connect you with our Clinical AI Agent...

Clinical Agent: Based on your CKD Stage 3 diagnosis and nephrology 
                guidelines, leg swelling (edema) can indicate fluid retention...
                
                [Detailed medical information with citations]
                
                📚 Source: Nephrology Knowledge Base
                References: 3 documents with relevance scores
```

**5. Web Search Fallback**
```
User: What are the latest SGLT2 inhibitors approved in 2024?

Clinical Agent: This requires recent information. Searching the web...
                
                [Web search results with current information]
                
                🌐 Web Sources:
                1. [Recent medical literature link]
                2. [Clinical guidelines link]
```

---

## 🎨 Features

### Patient Management
- ✅ Load 25+ patient discharge reports from JSON
- ✅ Search patients by name (case-insensitive)
- ✅ Retrieve detailed discharge information
- ✅ Handle duplicate names with warnings
- ✅ Format patient data for display

### RAG Implementation
- ✅ Process large PDF textbook (~88MB)
- ✅ Chunk documents intelligently (1000 chars, 200 overlap)
- ✅ **Local vector storage** (ChromaDB or FAISS)
- ✅ Google Gemini embeddings (768 dimensions)
- ✅ Similarity search with configurable threshold
- ✅ Source attribution and citations
- ✅ Relevance scoring

### Web Search Integration
- ✅ DuckDuckGo search integration
- ✅ Automatic fallback when RAG lacks info
- ✅ Groq LLM for answer synthesis
- ✅ Source URLs and citations
- ✅ Medical disclaimer inclusion

### Logging System
- ✅ Comprehensive interaction logging
- ✅ Agent handoff tracking
- ✅ Tool call logging
- ✅ RAG retrieval logging
- ✅ Web search logging
- ✅ Error logging with context
- ✅ Session start/end tracking
- ✅ Timestamped log files

### User Interface
- ✅ Modern Streamlit design
- ✅ Agent identification badges
- ✅ Real-time status updates
- ✅ Source information display
- ✅ Patient context indicators
- ✅ Session management controls
- ✅ Conversation log download
- ✅ Responsive layout

---

## 🔧 Configuration

### Vector Store Selection
Edit `config.py`:
```python
VECTOR_STORE_TYPE = "chromadb"  # Options: "chromadb" or "faiss"
```

### RAG Parameters
```python
CHUNK_SIZE = 1000              # Document chunk size
CHUNK_OVERLAP = 200            # Overlap between chunks
SIMILARITY_THRESHOLD = 0.7     # Minimum similarity score
TOP_K_RESULTS = 5              # Number of results to retrieve
```

### Model Configuration
```python
GEMINI_MODEL = "gemini-2.0-flash-thinking-exp-01-21"
GEMINI_EMBEDDINGS_MODEL = "models/text-embedding-004"
GROQ_MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.7
```

---

## 📊 Technical Specifications

### Technologies Used

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Web interface |
| **Orchestration** | Custom Python | Multi-agent coordination |
| **LLM (Primary)** | Google Gemini 2.0 | Clinical & receptionist agents |
| **LLM (Web Search)** | Groq (Llama 3.3 70B) | Web search synthesis |
| **Embeddings** | Google Gemini Text Embeddings | Document vectorization |
| **Vector DB** | ChromaDB / FAISS | Local vector storage |
| **Web Search** | DuckDuckGo | Medical information retrieval |
| **Document Processing** | LangChain + PyPDF | PDF parsing & chunking |
| **Logging** | Python logging | System monitoring |
| **Data Storage** | JSON | Patient records |

### Why These Choices?

**Google Gemini 2.0 Flash Thinking:**
- Latest thinking model with enhanced reasoning
- Excellent for medical domain understanding
- Fast inference time
- Cost-effective

**ChromaDB/FAISS (Local):**
- No cloud dependencies
- Fast similarity search
- Persistent storage
- Privacy-focused (data stays local)

**Groq with Llama 3.3:**
- Extremely fast inference
- Excellent for web search synthesis
- Free tier available
- Good medical knowledge

**DuckDuckGo:**
- No API key required
- Privacy-focused
- Reliable medical search results
- Free to use

---

## 📝 Logging

All system events are logged to timestamped files in `logs/` directory:

```
logs/
└── medical_assistant_20250115_120000.log
```

**Logged Events:**
- 🚀 Session start/end
- 💬 User messages
- 🤖 Agent responses
- 🔄 Agent handoffs
- 🔧 Tool calls (patient retrieval, RAG, web search)
- 📚 Document retrieval details
- 🌐 Web search queries
- ❌ Errors with full context

**Example Log Entry:**
```
2025-01-15 12:00:00 - MedicalAssistant - INFO - 🔄 AGENT HANDOFF: ReceptionistAgent → ClinicalAgent
2025-01-15 12:00:00 - MedicalAssistant - INFO -    Reason: Medical query detected: I'm having swelling...
2025-01-15 12:00:01 - MedicalAssistant - INFO - 📚 RAG RETRIEVAL: Query='swelling legs CKD', Retrieved 3 documents
```

---

## ⚠️ Medical Disclaimer

```
⚠️ IMPORTANT DISCLAIMER:
This is an AI assistant for educational purposes only. The information 
provided should not be considered as medical advice. Always consult with 
qualified healthcare professionals for personal medical advice, diagnosis, 
or treatment.
```

This disclaimer is:
- Displayed in the sidebar
- Included in all clinical responses
- Emphasized throughout the application

---

## 🧪 Testing

### Test Individual Components

```bash
# Test patient retrieval
python patient_retrieval_tool.py

# Test RAG engine
python rag_engine.py

# Test web search agent
python web_search_agent.py

# Test receptionist agent
python receptionist_agent.py

# Test clinical agent
python clinical_agent.py

# Test orchestrator
python multi_agent_orchestrator.py
```

### Test the Full Application

1. Start the Streamlit app
2. Click "Start New Session"
3. Provide a patient name (e.g., "John Smith")
4. Ask follow-up questions
5. Ask medical questions to trigger agent routing

---

## 🎯 Assignment Checklist

- ✅ 25+ dummy patient reports created
- ✅ Nephrology reference materials processed
- ✅ Receptionist Agent implemented
- ✅ Clinical AI Agent with RAG implemented
- ✅ Patient data retrieval tool implemented
- ✅ Web search tool integration
- ✅ Comprehensive logging system
- ✅ Simple web interface working
- ✅ Agent handoff mechanism functional
- ✅ Local vector storage (ChromaDB/FAISS)
- ✅ All code commented and documented
- ✅ README with architecture justification
- ✅ Requirements file
- ✅ Environment configuration

---

## 🚧 Troubleshooting

### Issue: "API Key not found"
**Solution:** Ensure `.env` file exists with valid API keys

### Issue: "Module not found"
**Solution:** Run `pip install -r requirements.txt`

### Issue: "PDF not found"
**Solution:** Ensure `nephrology.pdf` exists in `../data/` directory

### Issue: "Slow first run"
**Solution:** Normal! Processing large PDF takes time. Vector DB is cached for future runs.

### Issue: "ChromaDB errors"
**Solution:** Delete `chroma_db/` folder and restart to rebuild

### Issue: "FAISS errors"
**Solution:** Delete `faiss_index/` folder and restart to rebuild

---

## 📈 Future Enhancements

Potential improvements for production:
- [ ] Add user authentication
- [ ] Implement conversation memory across sessions
- [ ] Add support for multiple languages
- [ ] Include medication interaction checking
- [ ] Add appointment scheduling
- [ ] Implement voice interface
- [ ] Add more specialized agents (pharmacy, diet, exercise)
- [ ] Integrate with EHR systems
- [ ] Add push notifications for follow-ups
- [ ] Implement analytics dashboard

---

## 👨‍💻 Developer Information

**Assignment:** GenAI Intern - Post Discharge Medical AI Assistant POC  
**Company:** DataSmith AI  
**Duration:** 2-3 Days  
**Technology Stack:** Python, Streamlit, LangChain, Google Gemini, Groq, ChromaDB/FAISS

---

## 📄 License

This is an educational project for internship evaluation purposes.

---

## 🙏 Acknowledgments

- Google Gemini for powerful AI capabilities
- Groq for fast inference
- LangChain for RAG framework
- ChromaDB/FAISS for vector storage
- Streamlit for rapid UI development
- DuckDuckGo for web search
-agentic ai rag(agno) fusion better langgraph agentic rag with 3-4 chunking strategies like token based paragraph based,agentic chunking ,structure based to check for accuracy as retriever depends on chunking
-furtehr can be implemented for complex tasks using langgraph,crewai,autogen,agno
---

**Built with ❤️ for DataSmith AI GenAI Internship**
