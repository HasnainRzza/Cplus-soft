from langchain_groq import ChatGroq
from config.config import GROQ_API_KEY

def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        # Using a model highly capable of tool calling
        model="qwen/qwen3.6-27b",
        temperature=0,
        max_retries=2,
    )
