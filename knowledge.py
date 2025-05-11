# ---------- knowledge.py ----------
from langchain_huggingface import HuggingFaceEmbeddings  # New import path
from langchain_community.vectorstores import FAISS

policies = [
    "Returns accepted within 30 days",
    "Electronics must be unopened",
    "Free returns for premium members"
]

def build_rag():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"  # Explicit model
    )
    return FAISS.from_texts(policies, embeddings)