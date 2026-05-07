"""
rag.py — RAG (Retrieval-Augmented Generation) Logic for SWS AI Chatbot
Handles:
  1. Loading the ChromaDB collection
  2. Embedding user questions using sentence-transformers
  3. Retrieving the top-5 most relevant document chunks
  4. Generating an answer using Google Gemini API (gemini-1.5-flash)
"""

# SQLite compatibility fix for ChromaDB
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import os
import chromadb
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from .env file (GEMINI_API_KEY)
load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "sws_ai_documents"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K_RESULTS = 5          # number of chunks to retrieve
GEMINI_MODEL = "gemini-pro"  # Google Gemini model to use

# System prompt that instructs Gemini how to behave
SYSTEM_PROMPT = """You are a helpful HR assistant for SWS AI company.
Answer employee questions ONLY using the context provided below.
Do not use any outside knowledge.
If the answer is not in the context, say exactly:
"I don't have that information in the company documents."
Be clear, friendly, and professional."""

# ─── Module-level singletons (loaded once, reused for every request) ──────────
print("[INFO] Loading embedding model for RAG...")
try:
    _embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
    print(f"[INFO] Embedding model '{EMBED_MODEL_NAME}' loaded.")
except Exception as e:
    print(f"[ERROR] Could not load embedding model: {e}")
    sys.exit(1)

print("[INFO] Connecting to ChromaDB...")
try:
    _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    _collection = _chroma_client.get_collection(name=COLLECTION_NAME)
    print(f"[INFO] ChromaDB collection '{COLLECTION_NAME}' connected "
          f"({_collection.count()} chunks available).")
except Exception as e:
    print(f"[ERROR] Could not connect to ChromaDB collection '{COLLECTION_NAME}'.")
    print(f"[ERROR] Details: {e}")
    print("[HINT] Have you run 'python backend/ingest.py' yet?")
    sys.exit(1)

print("[INFO] Configuring Google Gemini API...")
_gemini_api_key = os.getenv("GEMINI_API_KEY")
if not _gemini_api_key:
    print("[ERROR] GEMINI_API_KEY environment variable is not set.")
    print("[HINT] Add GEMINI_API_KEY=your_key to a .env file in the project root.")
    sys.exit(1)

try:
    genai.configure(api_key=_gemini_api_key)
    _gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    print("[INFO] Google Gemini API ready.")
except Exception as e:
    print(f"[ERROR] Could not configure Gemini API: {e}")
    sys.exit(1)


# ─── Casual Message Handling ──────────────────────────────────────────────────
CASUAL_MESSAGES = [
    "hi", "hello", "hey", "thanks", "thank you", "ok", "okay",
    "bye", "goodbye", "good morning", "good night", "how are you",
    "who are you", "what are you", "what can you do"
]

def is_casual_message(question: str) -> bool:
    """Check if the question is a casual greeting or small talk"""
    question_lower = question.strip().lower()
    for casual in CASUAL_MESSAGES:
        if casual in question_lower:
            return True
    return False

def get_casual_response(question: str) -> str:
    """Return a friendly response for casual messages"""
    question_lower = question.strip().lower()
    if any(word in question_lower for word in ["hi", "hello", "hey"]):
        return "Hello! 👋 I am the SWS AI HR Assistant. Ask me anything about company policies like leave, benefits, IT security, onboarding, and more!"
    if any(word in question_lower for word in ["thanks", "thank you"]):
        return "You're welcome! Feel free to ask if you have more questions about SWS AI policies."
    if any(word in question_lower for word in ["bye", "goodbye"]):
        return "Goodbye! Have a great day! 😊"
    if any(word in question_lower for word in ["who are you", "what are you", "what can you do"]):
        return "I am the SWS AI HR Assistant. I can answer questions about company policies including leave policy, benefits, IT security, code of conduct, onboarding, and more. Just ask!"
    if any(word in question_lower for word in ["how are you"]):
        return "I am doing great! Ready to help you with any SWS AI policy questions. What would you like to know?"
    return "Hello! I am here to help with SWS AI company policy questions. What would you like to know?"


# ─── Function: embed a user question ─────────────────────────────────────────
def embed_question(question: str) -> list:
    """
    Convert the user's question text into a numeric embedding vector
    using the same sentence-transformers model used during ingestion.
    Returns a list of floats (the embedding vector).
    """
    embedding = _embedding_model.encode([question])[0].tolist()
    return embedding


# ─── Function: retrieve relevant chunks from ChromaDB ────────────────────────
def retrieve_chunks(question: str) -> dict:
    """
    Embed the user's question and search ChromaDB for the TOP_K_RESULTS
    most similar document chunks.
    Returns the raw ChromaDB query result dictionary which contains:
      - result["documents"][0] : list of chunk texts
      - result["metadatas"][0] : list of metadata dicts (source, page, etc.)
    """
    question_embedding = embed_question(question)

    results = _collection.query(
        query_embeddings=[question_embedding],
        n_results=TOP_K_RESULTS,
        include=["documents", "metadatas", "distances"],
    )

    return results


# ─── Function: generate an answer using Google Gemini ──────────────────────────
def generate_answer(question: str, retrieved_results: dict = None) -> dict:
    """
    Build a context string from the retrieved chunks, then send the
    question + context to Google Gemini.
    Returns a dict: { "answer": str, "sources": list[str] }
      - answer : the model's response
      - sources: deduplicated list of source PDF filenames
    """
    
    # First check if this is a casual message
    if is_casual_message(question):
        return {
            "answer": get_casual_response(question),
            "sources": []
        }
    
    # If not casual, do normal RAG pipeline
    if retrieved_results is None:
        retrieved_results = {}
    
    # Extract chunk texts and source filenames from retrieval results
    chunk_texts = retrieved_results.get("documents", [[]])[0]
    metadatas = retrieved_results.get("metadatas", [[]])[0]

    if not chunk_texts:
        return {
            "answer": "I don't have that information in the company documents.",
            "sources": []
        }

    # Build the context block from retrieved chunks
    context_parts = []
    for i, (chunk, meta) in enumerate(zip(chunk_texts, metadatas)):
        source = meta.get("source", "unknown")
        page = meta.get("page_number", "?")
        context_parts.append(
            f"[Source: {source}, Page: {page}]\n{chunk}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Collect unique source filenames for the response metadata
    sources = list(dict.fromkeys(
        meta.get("source", "unknown") for meta in metadatas
    ))

    # Build the full prompt for Gemini
    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"CONTEXT FROM COMPANY DOCUMENTS:\n{context}\n\n"
        f"---\n\n"
        f"EMPLOYEE QUESTION: {question}\n\n"
        f"ANSWER:"
    )

    # Call Google Gemini
    try:
        response = _gemini_model.generate_content(full_prompt)
        answer_text = response.text
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        # Fallback: Create a response from the retrieved context
        answer_text = f"""Based on the company documents retrieved, here's what I found:

{context}

Note: This is directly from company documents. For a complete answer, please refer to the source files listed below."""

    return {
        "answer": answer_text,
        "sources": sources
    }


# ─── Convenience wrapper used by main.py ─────────────────────────────────────
def ask(question: str) -> dict:
    """
    High-level function called by the FastAPI endpoint.
    Takes a question string, retrieves relevant chunks, generates an answer,
    and returns a dict: { "answer": str, "sources": list[str] }
    """
    print(f"[INFO] Processing question: {question[:80]}...")

    retrieved = retrieve_chunks(question)
    result = generate_answer(question, retrieved)

    print(f"[INFO] Answer generated. Sources used: {result.get('sources', [])}")
    return result
