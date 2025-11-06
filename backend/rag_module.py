# backend/rag_module.py
"""
Minimal RAG placeholder. For now, we provide simple text extraction
from PDFs and a naive substring search to return context snippets.

Replace with LangChain + Chroma/FAISS or LlamaIndex for semantic search.
"""

import os
from typing import List

DOCS_DIR = os.path.join(os.path.dirname(__file__), "../company_docs")

def extract_text_from_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = []
        for p in reader.pages:
            t = p.extract_text() or ""
            text.append(t)
        return "\n".join(text)
    except Exception:
        return ""

# Build simple in-memory index (filename -> text)
_index = None
def _ensure_index():
    global _index
    if _index is None:
        _index = {}
        if not os.path.exists(DOCS_DIR):
            return
        for fname in os.listdir(DOCS_DIR):
            if fname.lower().endswith(".pdf"):
                fpath = os.path.join(DOCS_DIR, fname)
                _index[fname] = extract_text_from_pdf(fpath)

def query_rag(query: str, k: int = 3) -> str:
    """
    Naive substring matching: returns up to k matching snippets across docs.
    """
    _ensure_index()
    if not query:
        return ""
    query_lower = query.lower()
    snippets = []
    for fname, text in _index.items():
        idx = text.lower().find(query_lower)
        if idx != -1:
            start = max(0, idx - 200)
            end = min(len(text), idx + 200)
            snippets.append(text[start:end].strip().replace("\n", " "))
        # stop early if we have enough
        if len(snippets) >= k:
            break
    return "\n\n".join(snippets[:k])
