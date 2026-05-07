"""
main.py — FastAPI Backend for SWS AI RAG Chatbot
Exposes REST API endpoints for chat and health check.
"""

# SQLite compatibility fix for ChromaDB
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import rag
from rag import is_casual_message, get_casual_response

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="SWS AI RAG Chatbot",
    description="RAG-powered chatbot for SWS AI company",
    version="1.0.0"
)

# Enable CORS for all origins (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ─── Request/Response Models ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """
    Expected request body for /api/chat endpoint.
    Contains the user's question.
    """
    question: str


class ChatResponse(BaseModel):
    """
    Response body for /api/chat endpoint.
    Contains the AI's answer and source documents.
    """
    answer: str
    sources: list


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    """
    Health check endpoint.
    Returns status of the backend.
    """
    return {"status": "SWS AI RAG Chatbot running"}


@app.post("/api/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.
    
    Args:
        request: ChatRequest with 'question' field
    
    Returns:
        ChatResponse with 'answer' and 'sources' fields
    """
    try:
        question = request.question.strip()
        
        # Check if this is a casual message first
        if is_casual_message(question):
            casual_answer = get_casual_response(question)
            return ChatResponse(
                answer=casual_answer,
                sources=[]
            )
        
        # Normal RAG flow for policy questions
        result = rag.ask(question)
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    
    except Exception as e:
        print(f"[ERROR] Chat endpoint failed: {e}")
        return ChatResponse(
            answer="An error occurred while processing your request. Please try again.",
            sources=[]
        )


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    print("[INFO] Starting FastAPI server...")
    print("[INFO] Backend running on http://localhost:8000")
    print("[INFO] API docs available at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
