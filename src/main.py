from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import os
import shutil

from config.config import UPLOAD_DIR
from src.document_processor import process_pdf
from src.vectorstore import save_vectorstore
from src.agent import ask_agent_stream
from src.logger import flush_logs_worker, log_event
from src.semantic_cache import semantic_cache

app = FastAPI(title="CV RAG Application")

class ChatRequest(BaseModel):
    session_id: str
    query: str

@app.on_event("startup")
async def startup_event():
    # Start the async queue flush loop
    asyncio.create_task(flush_logs_worker())

def sync_process_and_save(file_path: str):
    try:
        chunks = process_pdf(file_path)
        save_vectorstore(chunks)
    except Exception as e:
        print(f"Background processing error: {e}")

@app.post("/upload")
async def upload_cv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Queue the heavy embedding work in the background to return instantly
    background_tasks.add_task(sync_process_and_save, file_path)
    await log_event("CV_UPLOADED", {"filename": file.filename})
    
    return {"message": "CV upload received. Processing in background..."}

from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Check Semantic Cache first
        is_hit, cached_response, cache_item = await semantic_cache.check_cache(request.query)
        if is_hit:
            async def mock_stream():
                yield cached_response
            return StreamingResponse(mock_stream(), media_type="text/plain")
            
        # Stream the Agent Invocation
        return StreamingResponse(
            ask_agent_stream(request.session_id, request.query, cache_item), 
            media_type="text/plain"
        )
    except Exception as e:
        await log_event("ERROR", {"endpoint": "/chat", "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
