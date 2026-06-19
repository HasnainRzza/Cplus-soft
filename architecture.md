# Cplus-soft RAG Architecture

This diagram maps out the complete flow of your RAG application, detailing both synchronous user interactions and background asynchronous tasks. 

```mermaid
graph TD
    %% Define User and Endpoints
    User((User))
    API_Upload["POST /upload"]
    API_Chat["POST /chat"]
    
    %% User Interactions
    User -- "Uploads CV (PDF)" --> API_Upload
    User -- "Sends Query" --> API_Chat
    
    %% Background Upload Flow
    subgraph Async Upload Processing
        API_Upload -- "Returns 200 instantly" --> User
        API_Upload -. "Handoff to BackgroundTasks" .-> PDFLoader[PyPDFLoader & Splitter]
        PDFLoader --> EmbeddingModel["SentenceTransformers\n(all-MiniLM-L6-v2)"]
        EmbeddingModel --> FAISS_DB[("FAISS Vector Store\n(Persistent)")]
    end
    
    %% Chat Flow
    subgraph Conversational RAG Pipeline
        API_Chat --> CacheCheck{"Semantic Cache\n(Cosine Sim > 0.85)"}
        
        %% Cache Hit Flow
        CacheCheck -- "Freq >= 3 (Hit)" --> StreamReturn["Stream Cached Response"]
        StreamReturn --> User
        
        %% Cache Miss Flow
        CacheCheck -- "Miss / Low Freq" --> AgentExecutor["LangChain Agent\n(10 Msg Memory)"]
        AgentExecutor <--> GroqAPI(("Groq API\n(qwen3.6-27b)"))
        
        AgentExecutor -- "Invokes Tool" --> ToolCall["search_cv()"]
        ToolCall <--> FAISS_DB
        
        AgentExecutor -- "Streams Tokens" --> StreamReturn
    end

    %% Background Queue & Logging
    subgraph Async Logging & Telemetry
        AsyncQueue[("asyncio.Queue\n(Memory Buffer)")]
        WorkerTask["Background Worker\n(Every 60s)"]
        LogFile[("app.jsonl\n(Disk)")]
        
        API_Upload -. "Log: CV_UPLOADED" .-> AsyncQueue
        CacheCheck -. "Log: CACHE_HIT/MISS" .-> AsyncQueue
        
        AsyncQueue -. "Consumes batch" .-> WorkerTask
        WorkerTask -. "Flushes JSON" .-> LogFile
    end

    classDef fastAPI fill:#009688,stroke:#00796B,stroke-width:2px,color:#fff
    classDef bgTasks fill:#FF9800,stroke:#F57C00,stroke-width:2px,color:#fff
    classDef storage fill:#2196F3,stroke:#1976D2,stroke-width:2px,color:#fff
    
    class API_Upload,API_Chat,StreamReturn fastAPI
    class PDFLoader,WorkerTask bgTasks
    class FAISS_DB,AsyncQueue,LogFile storage
```

### Breakdown of the Components:

> [!TIP]
> **Endpoints**
> - **`POST /upload`**: Receives PDF. Pushes heavy processing to a background thread to return immediately.
> - **`POST /chat`**: The main interface. Expects a `session_id` and `query` string. Returns a streamed text response.

> [!NOTE]
> **Semantic Cache**
> Evaluates all queries as they enter `/chat` using `numpy`. If a user asks a similar question 3 times, the LLM is completely bypassed, zeroing out API costs and cutting latency to roughly zero.

> [!IMPORTANT]
> **Tool Calling Agent**
> Your agent decides autonomously if it needs to use the `search_cv` tool to lookup the FAISS database, or if it can answer entirely from its internal memory/parameters.

> [!TIP]
> **Telemetry (Logging)**
> Events don't block user requests. They are instantly pushed into a non-blocking queue. Every 60 seconds, a background daemon safely writes them to `app.jsonl`.
