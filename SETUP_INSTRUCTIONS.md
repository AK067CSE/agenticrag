# 📦 Complete Setup Instructions

## Step-by-Step Setup Guide

### Prerequisites Check
- [ ] Python 3.9+ installed
- [ ] pip package manager
- [ ] Text editor (VS Code recommended)
- [ ] Terminal/Command Prompt access

---

## 🚀 Installation Steps

### Step 1: Navigate to Project Directory
```bash
cd c:\Users\abhik\Downloads\genaiagents\post_discharge_ai_assistant\fresh_system
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected output:** All packages install successfully (~2-3 minutes)

### Step 4: Configure Environment Variables

#### Option A: Copy and Edit
```bash
copy .env.example .env
notepad .env
```

#### Option B: Create Manually
Create a file named `.env` with:
```env
GOOGLE_API_KEY=your_actual_google_gemini_key
GROQ_API_KEY=your_actual_groq_key
```

### Step 5: Get API Keys (Free)

#### Google Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Paste into `.env` file

#### Groq API Key
1. Visit: https://console.groq.com/keys
2. Sign up/Sign in
3. Click "Create API Key"
4. Copy the key
5. Paste into `.env` file

### Step 6: Verify Data Files

Check that these files exist:
```bash
# Check patients database
dir ..\data\patients.json

# Check nephrology PDF
dir ..\data\nephrology.pdf
```

**Both files should be present in the parent `data/` directory**

### Step 7: Run System Test
```bash
python test_system.py
```

**Expected output:**
```
✅ Configuration test passed!
✅ Patient retrieval test passed!
✅ RAG engine test passed!
✅ Web search test passed!
✅ Individual agents test passed!
✅ Orchestrator test passed!

Results: 6/6 tests passed
🎉 All tests passed! System is ready to use.
```

### Step 8: Launch Application
```bash
streamlit run app.py
```

**Expected output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Step 9: Open Browser
- Browser should auto-open to http://localhost:8501
- If not, manually open the URL

---

## 🎮 First-Time Usage

### 1. Start Session
- Click **"🚀 Start New Session"** in the left sidebar
- System initializes all agents
- Receptionist greets you

### 2. Provide Name
- Enter your name when prompted
- Try: "John Smith" (test patient in database)
- System retrieves discharge report

### 3. View Patient Info
- Discharge information displayed
- Medications listed
- Follow-up care shown

### 4. Ask Questions
Try these sample questions:
```
- "How are my medications working?"
- "What should I avoid eating?"
- "I have swelling in my legs. Is this normal?"
- "What is chronic kidney disease?"
- "Tell me about the latest CKD treatments"
```

### 5. Observe Agent Routing
- General questions → Receptionist Agent
- Medical questions → Clinical Agent
- Latest info → Web Search (automatic fallback)

---

## 🔍 Verification Checklist

After setup, verify:

- [ ] ✅ Application starts without errors
- [ ] ✅ Session can be started
- [ ] ✅ Patient name can be entered
- [ ] ✅ Discharge report is retrieved
- [ ] ✅ Medical questions get responses
- [ ] ✅ Sources are displayed
- [ ] ✅ Agent badges show correctly
- [ ] ✅ Logs are being created in `logs/` folder
- [ ] ✅ Vector database is created (first run only)

---

## 🐛 Common Issues & Solutions

### Issue: "Module not found: streamlit"
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "No module named 'google.generativeai'"
**Solution:**
```bash
pip install google-generativeai
```

### Issue: "GOOGLE_API_KEY not found"
**Solution:**
- Check `.env` file exists in `fresh_system/` directory
- Verify API key is set: `GOOGLE_API_KEY=your_key`
- No quotes needed around the key

### Issue: "patients.json not found"
**Solution:**
```bash
# Check file location
dir ..\data\patients.json

# Verify config.py points to correct path
# Should be: ../data/patients.json
```

### Issue: "PDF processing takes too long"
**Solution:**
- First run: 2-5 minutes is normal (processing 88MB PDF)
- Subsequent runs: <10 seconds (loads cached vectors)
- Vector database is saved to `chroma_db/` or `faiss_index/`

### Issue: "ChromaDB errors"
**Solution:**
```bash
# Delete and rebuild
rmdir /s chroma_db
python app.py
```

### Issue: "Web search not working"
**Solution:**
- Check GROQ_API_KEY in `.env`
- Verify internet connection
- DuckDuckGo may be temporarily blocked (rare)

### Issue: "Port 8501 already in use"
**Solution:**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

---

## 📂 Directory Structure After Setup

```
fresh_system/
├── .env                    # Your API keys (DO NOT commit)
├── app.py                  # Main Streamlit application
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── README.md              # Full documentation
├── QUICKSTART.md          # Quick setup guide
├── ARCHITECTURE_JUSTIFICATION.md  # Design decisions
├── test_system.py         # System tests
│
├── Agents/
│   ├── receptionist_agent.py
│   ├── clinical_agent.py
│   └── web_search_agent.py
│
├── Tools/
│   ├── patient_retrieval_tool.py
│   └── rag_engine.py
│
├── Core/
│   ├── multi_agent_orchestrator.py
│   └── logger_system.py
│
├── logs/                   # Auto-created
│   └── medical_assistant_TIMESTAMP.log
│
└── chroma_db/             # Auto-created (or faiss_index/)
    └── [vector database files]
```

---

## 🔄 Updating the System

### Update Patient Data
1. Edit `../data/patients.json`
2. Restart application
3. Changes take effect immediately

### Update Knowledge Base
1. Replace `../data/nephrology.pdf`
2. Delete `chroma_db/` directory
3. Restart application
4. PDF will be re-processed

### Update Configuration
1. Edit `config.py`
2. Restart application

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

---

## 💡 Pro Tips

### Tip 1: View Logs in Real-Time
```bash
# In separate terminal
Get-Content logs\medical_assistant_*.log -Wait
```

### Tip 2: Switch Vector Store
Edit `config.py`:
```python
VECTOR_STORE_TYPE = "faiss"  # or "chromadb"
```

### Tip 3: Adjust RAG Threshold
Edit `config.py`:
```python
SIMILARITY_THRESHOLD = 0.6  # Lower = more results
```

### Tip 4: Download Conversation
- Use "📥 Download Log" button in sidebar
- Saves complete conversation history

### Tip 5: Reset Everything
```bash
# Delete all cached data
rmdir /s chroma_db
rmdir /s faiss_index
rmdir /s logs

# Restart fresh
python app.py
```

---

## 📊 Performance Expectations

### First Run
- Startup: 2-5 minutes (PDF processing)
- Response time: 2-4 seconds per query
- Memory usage: ~500MB-1GB

### Subsequent Runs
- Startup: 5-10 seconds (loads cached vectors)
- Response time: 2-4 seconds per query
- Memory usage: ~300-500MB

### RAG Queries
- Vector search: <100ms
- LLM generation: 2-3 seconds
- Total response: ~3-4 seconds

### Web Search Queries
- Search: 1-2 seconds
- Synthesis: 2-3 seconds
- Total response: ~4-5 seconds

---

## 🎯 Success Criteria

You've successfully set up the system when:

1. ✅ Application launches without errors
2. ✅ All 6 system tests pass
3. ✅ Can retrieve patient information
4. ✅ RAG returns relevant answers
5. ✅ Web search fallback works
6. ✅ Agent handoffs occur smoothly
7. ✅ Logs are being generated
8. ✅ Sources are properly cited

---

## 📞 Troubleshooting Help

If issues persist:

1. **Check Logs:** `logs/medical_assistant_*.log`
2. **Run Tests:** `python test_system.py`
3. **Verify API Keys:** Keys are valid and have quota
4. **Check Paths:** All file paths are correct
5. **Internet Connection:** Required for API calls and web search

---

## 🎉 Next Steps

Once setup is complete:

1. ✅ Read `README.md` for full documentation
2. ✅ Review `ARCHITECTURE_JUSTIFICATION.md` for design decisions
3. ✅ Try sample conversations from `QUICKSTART.md`
4. ✅ Explore different patient cases
5. ✅ Test edge cases
6. ✅ Review logs to understand agent behavior

---

**You're now ready to use the Post-Discharge Medical AI Assistant!** 🚀

For questions or issues, refer to:
- `README.md` - Complete documentation
- `QUICKSTART.md` - Quick reference
- `test_system.py` - Run diagnostics
- `logs/` - System behavior logs
