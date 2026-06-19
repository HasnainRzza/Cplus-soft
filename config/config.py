import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "faiss_index")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Cache & Logging configs
CACHE_SIMILARITY_THRESHOLD = 0.85
CACHE_FREQ_THRESHOLD = 3
LOG_FLUSH_INTERVAL_SEC = 60
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.jsonl")
