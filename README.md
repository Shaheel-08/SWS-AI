# SWS AI RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** chatbot for SWS AI company that answers employee questions based on company policy documents.

---

## 📋 Project Description

This chatbot allows SWS AI employees to ask questions about company policies, procedures, and information. Instead of using a general-purpose AI, it retrieves relevant information from company documents and uses that to generate accurate, contextual answers.

**Key Features:**
- 📄 Reads PDF documents from `backend/documents/` folder
- 🔍 Retrieves relevant information using semantic search
- 🤖 Generates answers using Google Gemini AI
- 💾 Stores embeddings locally in ChromaDB (no cloud dependencies)
- 🎨 Beautiful, user-friendly chat interface
- ⚡ Fast and responsive

---

## 🛠️ Tech Stack & Why

| Component | Technology | Reason |
|-----------|-----------|--------|
| **Backend** | Python + FastAPI | Fast, modern, easy to learn |
| **Vector Database** | ChromaDB | Local storage, no setup needed |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Free, no API key required |
| **LLM** | Google Gemini (gemini-1.5-flash) | Free tier available, reliable |
| **PDF Parser** | PyMuPDF | Robust PDF text extraction |
| **Frontend** | HTML + CSS + JavaScript | Single file, no build process |
| **Styling** | Livvic Font + Blue/White Theme | Clean, professional look |

---

## 📦 Installation & Setup

### Step 1: Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

**What gets installed:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings model
- `google-generativeai` - Gemini API
- `pymupdf` - PDF reading
- `python-dotenv` - Environment variables
- `pydantic` - Data validation

### Step 2: Add Your API Key

The `.env` file already contains the Gemini API key:

```
GEMINI_API_KEY=AIzaSyA47qtFi1bZL9FCvxm54lHTvjq-Zttl0wY
```

No action needed — the key is already set up!

### Step 3: Add PDF Documents

Place your company policy PDF files in the `backend/documents/` folder:

```
backend/
└── documents/
    ├── company_policies.pdf
    ├── hr_handbook.pdf
    └── employee_handbook.pdf
```

### Step 4: Ingest Documents

Run the ingestion script to extract text from PDFs and store in ChromaDB:

```bash
python backend/ingest.py
```

**What happens:**
- Reads all PDFs from `backend/documents/`
- Extracts text using PyMuPDF
- Splits text into 500-character chunks with 50-character overlap
- Generates embeddings using sentence-transformers
- Stores in ChromaDB collection named `sws_ai_documents`
- Prints progress for each document

**Expected output:**
```
[INFO] Found 3 PDF file(s) to ingest.
[INFO] Loading embedding model: all-MiniLM-L6-v2 ...
[INFO] Connecting to ChromaDB at: backend/chroma_db ...

[INFO] Ingesting: company_policies.pdf
  [INFO] Extracted text from 5 page(s).
  [INFO] Created 25 chunk(s).
  [SUCCESS] 'company_policies.pdf' ingested successfully (25 chunks stored).

All documents ingested successfully.
Total chunks stored in ChromaDB: 75
```

### Step 5: Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
[INFO] Starting FastAPI server...
[INFO] Backend running on http://localhost:8000
[INFO] API docs available at http://localhost:8000/docs
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Open the Frontend

Open `frontend/index.html` in your web browser:

```bash
# On Windows
start frontend/index.html

# On Mac
open frontend/index.html

# On Linux
xdg-open frontend/index.html
```

Or simply drag the file into your browser.

### Step 7: Start Chatting!

Type a question in the chat box and click "Send":

```
Q: What is the company vacation policy?
A: Based on our company documents, employees get...
   📄 Sources: company_policies.pdf
```

---

## 🏗️ Architecture Explained Simply

### How It Works (4 Steps)

```
1. USER TYPES QUESTION
          ↓
2. FRONTEND SENDS TO BACKEND
   POST http://localhost:8000/api/chat
          ↓
3. BACKEND RETRIEVES DOCUMENTS
   - Embeds the question using all-MiniLM-L6-v2
   - Searches ChromaDB for top 5 similar chunks
   - Finds relevant company documents
          ↓
4. BACKEND GENERATES ANSWER
   - Sends question + context to Gemini API
   - Gemini returns answer based on documents only
   - Returns answer + source files to frontend
          ↓
FRONTEND DISPLAYS ANSWER WITH SOURCES
```

### Component Breakdown

**Backend (`backend/main.py`):**
- FastAPI server running on port 8000
- `GET /` - Health check
- `POST /api/chat` - Main chat endpoint
- CORS enabled for browser requests

**RAG Pipeline (`backend/rag.py`):**
- `retrieve_chunks()` - Searches ChromaDB for similar documents
- `generate_answer()` - Calls Gemini API with context
- `ask()` - Orchestrates the pipeline

**Document Ingestion (`backend/ingest.py`):**
- Reads PDFs from `documents/` folder
- Chunks text into 500-character overlapping pieces
- Generates embeddings and stores in ChromaDB
- Runs once to prepare the database

**Frontend (`frontend/index.html`):**
- Single HTML file with embedded CSS and JavaScript
- Sends questions to backend API
- Displays answers in chat bubbles
- Shows typing indicator while waiting for response

### Why This Architecture?

✅ **No external dependencies:** ChromaDB stores everything locally  
✅ **Free to run:** sentence-transformers and Gemini free tier  
✅ **Privacy:** Documents never leave your system  
✅ **Fast:** Semantic search finds answers in milliseconds  
✅ **Scalable:** Works with 10s or 1000s of documents  
✅ **Simple:** Easy for beginners to understand and modify  

---

## 🚀 Workflow Summary

### First Time Setup
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Add PDFs to backend/documents/

# 3. Ingest documents
python backend/ingest.py

# 4. Start backend
cd backend && uvicorn main:app --reload --port 8000

# 5. Open frontend/index.html in browser
```

### Regular Usage
```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 (or just open in browser)
# Open frontend/index.html in web browser
# Start asking questions!
```

---

## 📁 File Structure

```
sws-ai-rag-chatbot/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── rag.py               # RAG pipeline
│   ├── ingest.py            # PDF ingestion
│   ├── requirements.txt      # Python dependencies
│   ├── .env                 # API keys (GEMINI_API_KEY)
│   ├── chroma_db/           # Local vector database (auto-created)
│   └── documents/           # Place your PDFs here
├── frontend/
│   └── index.html           # Chat UI
├── auto_commit.sh           # Auto-commit script
└── README.md                # This file
```

---

## ⚙️ Configuration

### Change Embedding Model
Edit `backend/rag.py` and `backend/ingest.py`:
```python
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # Change to another model
```

### Change Chunk Size
Edit `backend/ingest.py`:
```python
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 50      # overlap between chunks
```

### Change Port
Edit `backend/main.py`:
```python
uvicorn.run(app, port=9000)  # Change from 8000 to 9000
```

Also update the frontend in `frontend/index.html`:
```javascript
const API_URL = "http://localhost:9000/api/chat";
```

---

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not found"
**Solution:** Check `.env` file has the API key
```bash
cat backend/.env
# Should show: GEMINI_API_KEY=AIzaSyA47qtFi1bZL9FCvxm54lHTvjq-Zttl0wY
```

### Issue: "No PDF files found"
**Solution:** Make sure PDFs are in `backend/documents/`
```bash
ls backend/documents/  # Should show your PDF files
```

### Issue: "ChromaDB collection not found"
**Solution:** Run ingest script first
```bash
python backend/ingest.py
```

### Issue: Backend returns error 500
**Solution:** Check backend console for error message
```bash
# Look at terminal where uvicorn is running
```

### Issue: Frontend can't connect to backend
**Solution:** Make sure backend is running on port 8000
```bash
# Terminal should show: Uvicorn running on http://0.0.0.0:8000
```

---

## 📊 API Reference

### Health Check
```
GET http://localhost:8000/

Response:
{
  "status": "SWS AI RAG Chatbot running"
}
```

### Chat Endpoint
```
POST http://localhost:8000/api/chat

Request:
{
  "question": "What is the vacation policy?"
}

Response:
{
  "answer": "Based on company policy, employees get 20 days of vacation per year...",
  "sources": ["company_policies.pdf", "hr_handbook.pdf"]
}
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

---

## 🔄 Auto-Commit Setup

To automatically commit progress to GitHub every 15 minutes:

```bash
bash auto_commit.sh &
```

The script:
- Runs in the background
- Commits changes every 900 seconds (15 minutes)
- Pushes to `main` branch
- Useful for tracking progress

---

## 📝 Example Questions

The chatbot is trained to answer questions like:

- "What is our vacation policy?"
- "How many days of PTO do employees get?"
- "What are the benefits?"
- "How do I submit a time off request?"
- "What is the dress code?"
- "When is the annual performance review?"

All answers come from your company PDFs!

---

## ✅ Checklist for Production

- [ ] Add production PDFs to `backend/documents/`
- [ ] Run `python backend/ingest.py` to ingest documents
- [ ] Test backend API at `http://localhost:8000/docs`
- [ ] Test frontend at `frontend/index.html`
- [ ] Verify Gemini API key works
- [ ] Deploy backend to production server
- [ ] Deploy frontend to static hosting (GitHub Pages, Netlify, etc.)
- [ ] Monitor API usage and ChromaDB size

---

## 📞 Support

For questions or issues, check:
1. The troubleshooting section above
2. Backend console for error messages
3. Browser console (F12) for frontend errors
4. ChromaDB documentation: https://docs.trychroma.com

---

## 📄 License

This project is provided as-is for SWS AI company.

---

**Built with ❤️ for SWS AI**
