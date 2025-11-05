# 🚀 Quick Start Guide

Get the Post-Discharge Medical AI Assistant running in 5 minutes!

## ⚡ Fast Setup

### 1. Install Dependencies (1 minute)
```bash
cd fresh_system
pip install -r requirements.txt
```

### 2. Configure API Keys (1 minute)
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your keys:
# - GOOGLE_API_KEY=your_key_here
# - GROQ_API_KEY=your_key_here
```

**Get API Keys:**
- Google Gemini: https://makersuite.google.com/app/apikey (Free)
- Groq: https://console.groq.com/keys (Free)

### 3. Test the System (1 minute)
```bash
python test_system.py
```

### 4. Run the App (30 seconds)
```bash
streamlit run app.py
```

The app will open at: http://localhost:8501

## 📝 First Conversation

1. Click **"🚀 Start New Session"** in sidebar
2. Enter your name: `John Smith`
3. Ask: `"How are my medications?"`
4. Try: `"What is chronic kidney disease?"`

## 🎯 Test Patient Names

Try these names from the database:
- John Smith
- Alice Johnson
- Bob Martinez
- Carol White
- David Brown
- Emma Davis
- Frank Wilson

## ⚙️ Configuration

**Change Vector Store:**
Edit `config.py`:
```python
VECTOR_STORE_TYPE = "chromadb"  # or "faiss"
```

**Adjust RAG Threshold:**
```python
SIMILARITY_THRESHOLD = 0.7  # Lower = more results
```

## 🐛 Troubleshooting

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"API key not found"**
- Ensure `.env` file exists
- Check API keys are valid

**"PDF not found"**
- Ensure `nephrology.pdf` is in `../data/`

**"Slow first run"**
- Normal! Processing large PDF (~88MB)
- Takes 2-5 minutes first time
- Cached for future runs

## 📚 Features to Try

1. **Patient Retrieval**: Give your name to retrieve discharge info
2. **Medical Questions**: Ask about symptoms, medications, diet
3. **Knowledge Base**: Questions about kidney disease (uses RAG)
4. **Web Search**: Ask about latest treatments (auto fallback)
5. **Agent Routing**: Watch agents hand off in real-time
6. **Sources**: Click expanders to see where info came from

## 🔍 System Architecture

```
User → Streamlit UI
      ↓
      Multi-Agent Orchestrator
      ↓
      ┌─────────────────┬──────────────────┐
      ↓                 ↓                  ↓
Receptionist      Clinical AI        Web Search
   Agent             Agent              Agent
      ↓                 ↓
Patient DB        RAG Engine
                (ChromaDB/FAISS)
                      ↓
                Nephrology PDF
```

## 🎓 What Makes This Special

✅ **Multi-Agent**: 3 specialized agents working together  
✅ **Local Storage**: ChromaDB/FAISS (no cloud needed)  
✅ **Smart Routing**: Automatic agent handoffs  
✅ **Comprehensive Logging**: Every action tracked  
✅ **RAG + Web Search**: Best of both worlds  
✅ **Patient Context**: Personalized responses  

## 📖 Full Documentation

See `README.md` for complete details on:
- Architecture diagrams
- Component documentation
- API references
- Advanced configuration
- Troubleshooting

## 💡 Tips

- **First Question**: System asks for your name
- **Medical Questions**: Automatically routed to Clinical Agent
- **View Sources**: Expand to see where information came from
- **Session Management**: Use sidebar controls
- **Download Logs**: Save conversation history
- **Patient Context**: Clinical agent uses your discharge info

## 🎯 Assignment Requirements Met

✅ 25+ patient records  
✅ Nephrology reference materials  
✅ 3 specialized agents  
✅ Multi-agent orchestration  
✅ RAG implementation  
✅ Web search fallback  
✅ Patient retrieval tool  
✅ Comprehensive logging  
✅ Streamlit interface  
✅ Source citations  

---

**Ready to start?** Just run: `streamlit run app.py` 🚀
