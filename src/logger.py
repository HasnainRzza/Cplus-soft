import asyncio
import json
from datetime import datetime
from config.config import LOG_FLUSH_INTERVAL_SEC, LOG_FILE_PATH

# Built-in async queue acting as our message broker
log_queue = asyncio.Queue()

async def log_event(event_type: str, details: dict):
    """Pushes a JSON log event to the async queue instantly without blocking."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details
    }
    await log_queue.put(log_entry)

async def flush_logs_worker():
    """Background worker that flushes the queue to a file every 1 minute."""
    while True:
        await asyncio.sleep(LOG_FLUSH_INTERVAL_SEC)
        
        batch = []
        while not log_queue.empty():
            try:
                batch.append(log_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        if batch:
            # Write to JSONL file
            with open(LOG_FILE_PATH, mode="a", encoding="utf-8") as f:
                for entry in batch:
                    f.write(json.dumps(entry) + "\n")
            print(f"[Logger] Flushed {len(batch)} structured JSON logs to disk.")
