from langchain_core.tools.retriever import create_retriever_tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from src.llm import get_llm
from src.vectorstore import get_retriever
from src.memory import get_session_history

from langchain_core.runnables import RunnableLambda

def create_rag_agent():
    llm = get_llm()
    retriever = get_retriever()
    
    tools = []
    if retriever:
        cv_tool = create_retriever_tool(
            retriever,
            "search_cv",
            "Searches and returns excerpts from the user's uploaded CV/Resume. Use this tool whenever the user asks questions about their CV, experience, skills, or background."
        )
        tools.append(cv_tool)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. You have access to the user's CV via a tool. If the user asks about their CV or experience, use the search_cv tool. Provide professional answers."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    if tools:
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    else:
        # Fallback if no CV is uploaded yet
        # Ensure we return a proper Runnable with 'output' key
        def map_output(msg):
            return {"output": msg.content}
            
        # We must omit agent_scratchpad if we aren't using an agent executor
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Provide professional answers."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        agent_executor = fallback_prompt | llm | RunnableLambda(map_output)
    
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="output",
    )
    
    return agent_with_chat_history

async def ask_agent_stream(session_id: str, query: str, cache_item: dict):
    agent_with_chat_history = create_rag_agent()
    
    # Enforce conversation memory up to 10 messages
    history = get_session_history(session_id)
    if len(history.messages) > 10:
         history.messages = history.messages[-10:]
         
    full_response = ""
    
    # Stream events to only catch LLM generation chunks (skips tool invisible thoughts)
    async for event in agent_with_chat_history.astream_events(
        {"input": query},
        config={"configurable": {"session_id": session_id}},
        version="v1"
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if isinstance(content, str) and content:
                full_response += content
                yield content
                
    # Save the aggregated response to the cache item
    from src.semantic_cache import semantic_cache
    semantic_cache.save_response(cache_item, full_response)
