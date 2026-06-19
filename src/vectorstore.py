from langchain_community.vectorstores import FAISS
from src.embeddings import get_embedding_model
from config.config import FAISS_INDEX_PATH
import os

def save_vectorstore(chunks):
    embedding_model = get_embedding_model()
    vectorstore = FAISS.from_documents(chunks, embedding_model)
    vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore

def load_vectorstore():
    if not os.path.exists(FAISS_INDEX_PATH):
        return None
    embedding_model = get_embedding_model()
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH, 
        embedding_model, 
        allow_dangerous_deserialization=True
    )
    return vectorstore

def get_retriever():
    vectorstore = load_vectorstore()
    if vectorstore is None:
        return None
    return vectorstore.as_retriever(search_kwargs={"k": 3})
