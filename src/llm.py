from langchain_groq import ChatGroq
from config.config import GROQ_API_KEY

_LLM_CLIENT = None

def get_llm():
    global _LLM_CLIENT
    if _LLM_CLIENT is None:
        _LLM_CLIENT = ChatGroq(
            api_key=GROQ_API_KEY,
            # Using a model highly capable of tool calling
            model="qwen/qwen3.6-27b",
            temperature=0,
            max_retries=2,
        )
    return _LLM_CLIENT
