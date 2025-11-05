# backend/rag_module.py

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma

def setup_rag():
    loader = PyPDFLoader("company_docs/nfpa_standards.pdf")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model="llama3")
    db = Chroma.from_documents(chunks, embeddings, persist_directory="chroma_db")
    db.persist()
    return db

def query_rag(db, query):
    results = db.similarity_search(query, k=3)
    return "\n\n".join([r.page_content for r in results])
