#!/usr/bin/env python
"""
Wrapper script to run ingest.py with SQLite fix for ChromaDB.
"""

import sys
import os

# Add SQLite workaround BEFORE importing chromadb
# Try to use pysqlite3 if available, otherwise try alternate approaches
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    # If pysqlite3 not available, try to patch at runtime
    try:
        import sqlite3
        original_sqlite3_connect = sqlite3.connect
        
        def patched_connect(*args, **kwargs):
            # This won't fix version issue, but we'll try anyway
            return original_sqlite3_connect(*args, **kwargs)
        
        sqlite3.connect = patched_connect
    except:
        pass

# Now import and run ingest
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from ingest import ingest_documents

if __name__ == "__main__":
    ingest_documents()
