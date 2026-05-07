"""



ingest.py — PDF Ingestion Script for SWS AI RAG Chatbot
Loads all PDFs from the documents/ folder, extracts text,
splits into chunks, embeds them, and stores in ChromaDB.
"""

# SQLite compatibility fix for ChromaDB
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import os
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer

# ─── Configuration ───────────────────────────────────────────────────────────
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "sws_ai_documents"
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 50      # overlap between consecutive chunks
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


# ─── Helper: split text into overlapping chunks ───────────────────────────────
def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split a long string of text into smaller overlapping chunks.
    Returns a list of (chunk_text, chunk_index) tuples.
    """
    chunks = []
    start = 0
    chunk_index = 0
    

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append((chunk, chunk_index))
        chunk_index += 1
        start += chunk_size - overlap  # move forward with overlap

    return chunks


# ─── Helper: extract text from a PDF file ────────────────────────────────────
def extract_text_from_pdf(pdf_path):
    """
    Open a PDF file and extract all text page by page using PyMuPDF.
    Returns a list of (page_number, page_text) tuples.
    """
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():  # skip blank pages
                pages.append((page_num + 1, text))  # 1-indexed page numbers
        doc.close()
    except Exception as e:
        print(f"  [ERROR] Failed to read PDF '{pdf_path}': {e}")
        raise
    return pages


# ─── Main ingestion function ──────────────────────────────────────────────────
def ingest_documents():
    """
    Main function that:
    1. Loads the embedding model
    2. Connects to ChromaDB
    3. Loops through all PDFs in the documents/ folder
    4. Extracts, chunks, embeds, and stores each document
    """

    # Verify documents folder exists
    if not os.path.isdir(DOCUMENTS_DIR):
        print(f"[ERROR] Documents folder not found: {DOCUMENTS_DIR}")
        sys.exit(1)

    # Collect PDF files
    pdf_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"[WARNING] No PDF files found in: {DOCUMENTS_DIR}")
        print("Please place your PDF documents in the documents/ folder and run again.")
        sys.exit(0)

    print(f"[INFO] Found {len(pdf_files)} PDF file(s) to ingest.")

    # Load the free HuggingFace embedding model (no API key needed)
    print(f"[INFO] Loading embedding model: {EMBED_MODEL_NAME} ...")
    try:
        model = SentenceTransformer(EMBED_MODEL_NAME)
        print("[INFO] Embedding model loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to load embedding model: {e}")
        sys.exit(1)

    # Connect to ChromaDB (local persistent storage)
    print(f"[INFO] Connecting to ChromaDB at: {CHROMA_DB_PATH} ...")
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        # Delete existing collection so we start fresh on each ingest
        try:
            client.delete_collection(name=COLLECTION_NAME)
            print("[INFO] Deleted existing ChromaDB collection (starting fresh).")
        except Exception:
            pass  # collection did not exist yet — that is fine
        collection = client.create_collection(name=COLLECTION_NAME)
        print(f"[INFO] ChromaDB collection '{COLLECTION_NAME}' is ready.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to ChromaDB: {e}")
        sys.exit(1)

    # Process each PDF
    total_chunks_stored = 0
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(DOCUMENTS_DIR, pdf_filename)
        print(f"\n[INFO] Ingesting: {pdf_filename}")

        try:
            # Step 1: Extract text from PDF
            pages = extract_text_from_pdf(pdf_path)
            print(f"  [INFO] Extracted text from {len(pages)} page(s).")

            # Step 2: Chunk all pages together, keeping page number in metadata
            all_chunk_data = []  # list of (chunk_text, chunk_index, page_number)
            for page_number, page_text in pages:
                page_chunks = split_into_chunks(page_text)
                for chunk_text, chunk_index in page_chunks:
                    all_chunk_data.append((chunk_text, chunk_index, page_number))

            print(f"  [INFO] Created {len(all_chunk_data)} chunk(s).")

            # Step 3: Generate embeddings for all chunks in one batch (faster)
            chunk_texts = [cd[0] for cd in all_chunk_data]
            embeddings = model.encode(chunk_texts, show_progress_bar=False).tolist()

            # Step 4: Build IDs, documents, metadatas, and store in ChromaDB
            ids = []
            documents = []
            metadatas = []
            for i, (chunk_text, chunk_index, page_number) in enumerate(all_chunk_data):
                unique_id = f"{pdf_filename}_chunk_{i}"
                ids.append(unique_id)
                documents.append(chunk_text)
                metadatas.append({
                    "source": pdf_filename,
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                })

            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_chunks_stored += len(all_chunk_data)
            print(f"  [SUCCESS] '{pdf_filename}' ingested successfully "
                  f"({len(all_chunk_data)} chunks stored).")

        except Exception as e:
            print(f"  [ERROR] Failed to ingest '{pdf_filename}': {e}")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"All documents ingested successfully.")
    print(f"Total chunks stored in ChromaDB: {total_chunks_stored}")
    print(f"{'='*60}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ingest_documents()
