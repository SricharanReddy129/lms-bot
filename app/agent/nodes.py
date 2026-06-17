from langsmith import traceable
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from dotenv import load_dotenv

import contextvars
import jwt
from typing import Dict, Any
from langchain_core.messages import messages_from_dict, messages_to_dict

# Import your prompt template and state
from app.agent.prompt import agent_prompt
from app.agent.state import AgentState

# import the database fetch functions
from app.repositories.fetch_chat_history_repo import fetch_chat_history_from_mysql
from app.repositories.update_chat_history_repo import update_chat_history
from sqlalchemy.ext.asyncio import AsyncSession

# Import all individual tool files based on your directory structure
from app.agent.tools.leave_balance_tool import view_my_leave_balance, view_employee_leave_balance
from app.agent.tools.holiday_calendar_tool import view_holiday_calendar
from app.agent.tools.apply_leave_tool import apply_for_leave
from app.agent.tools.pending_leaves_tool import view_my_pending_leaves, view_team_pending_leaves
from app.agent.tools.approve_leaves_tool import approve_leave_requests
from app.agent.tools.reject_leaves_tool import reject_leave_requests
from app.agent.tools.view_approved_leaves_tool import view_my_approved_leaves, view_team_approved_leaves
from app.agent.tools.view_rejected_leaves_tool import view_my_rejected_leaves, view_team_rejected_leaves

load_dotenv()

# =========================================================
# 1. TOOL AGGREGATION & NODE SETUP
# =========================================================

tools = [
    view_my_leave_balance, view_employee_leave_balance, view_holiday_calendar,
    apply_for_leave, view_my_pending_leaves, view_team_pending_leaves,
    approve_leave_requests, reject_leave_requests, view_my_approved_leaves,
    view_team_approved_leaves, view_my_rejected_leaves, view_team_rejected_leaves
]

# The prebuilt node that natively executes the Python functions
tool_node = ToolNode(tools)

# =========================================================
# 2. LLM INITIALIZATION & BINDING
# =========================================================

# Initialize the Llama 3.3 70B model via Groq's high-speed LPU inference
# Temperature 0 ensures strict adherence to your tools, schemas, and cognitive framework
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
)

# Bind the tools so the model knows its schema capabilities
llm_with_tools = llm.bind_tools(tools)

# =========================================================
# 3. CONTEXT INTERCEPTION & STATE INITIALIZATION NODE
# =========================================================

async def initialize_context(state: dict) -> dict:
    """
    Node 1: Intercepts the request, decodes identity via keyless JWT, 
    fetches history, and perfectly deserializes database memory.
    """
    # Your existing context variable (set by your FastAPI middleware/dependency)
    auth_token_var: contextvars.ContextVar[str] = contextvars.ContextVar("auth_token")
    db_session_var: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar("db_session")

    # Step 1: Intercept the raw token securely
    try:
        token = auth_token_var.get()
    except LookupError:
        raise ValueError("Authentication token not found in request context.")

    # Step 2: Decode the keyless JWT for UX context
    try:
        decoded_payload = jwt.decode(token, key="", algorithms=["none"])
        
        user_data = {
            "employee_id": decoded_payload.get("id"),
            "employee_name": decoded_payload.get("name"),
            "role": decoded_payload.get("role")
        }
    except jwt.DecodeError:
        raise ValueError("Invalid token format or failed to decode payload.")

    # Step 3: Fetch long-term memory from MySQL using the newly decoded ID
    db_session = db_session_var.get()
    db_row = await fetch_chat_history_from_mysql(db_session=db_session, employee_id=user_data["employee_id"])

    # Step 4: Deserialize and prepare the state payload
    if db_row:
        # Extract the JSON array of dictionaries from your database row
        raw_message_dicts = db_row.get("recent_messages", [])
        
        # LangChain instantly converts the dictionaries back into their 
        # exact original classes (HumanMessage, ToolMessage, etc.)
        hydrated_messages = messages_from_dict(raw_message_dicts)
        

    # Return exactly what needs to be injected into the LangGraph state
    return {
        "user_context": user_data,
        "recent_history_slice": hydrated_messages
        }

# =========================================================
# 4. THE EXECUTION NODE
# =========================================================

async def call_model(state: AgentState) -> dict:
    """
    Node 2: The primary reasoning engine.
    Formats the segregated memory arrays, enforces strict identity extraction,
    and executes the tool-bound LLM.
    """
    # 1. Safely extract the memory dictionaries from the state
    user_ctx = state.get("user_context", {})
    memory = state.get("recent_history_slice", [])  # This is already a list of BaseMessage objects, ready for the prompt
    
    # 2. Strict Zero-Trust Extraction
    # Using direct bracket notation instead of .get() intentionally.
    # If the JWT token was somehow missing these claims, the graph execution 
    # will halt immediately with a KeyError, preventing an unauthenticated ghost-run.
    name = user_ctx["employee_name"]
    role = user_ctx["role"]
    id = user_ctx["id"]
    
    # 3. Dynamically construct the user context message
    context_string = f"Current Session Context:\nUser Name: {name}\nRole: {role}\nEmployee ID: {id}"
    context_message = SystemMessage(content=context_string)
    
    # 4. Map all variables exactly to the Prompt Template placeholders
    prompt_args = {
        # Wrapped in a list to satisfy the MessagesPlaceholder requirement
        "dynamic_user_context": [context_message], 
        
        # The database history array from Node 1 (falls back to empty list if new user)
        "history": memory["recent_history_slice"] if memory else [] ,
        
        # The active graph timeline (including the user's immediate question)
        "messages": state["messages"] 
    }
    
    # 5. Bind the secure HR tools to the LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # 6. Pipe the fully populated prompt into the tool-bound LLM
    chain = agent_prompt | llm_with_tools
    
    # 7. Execute the chain
    # Streaming tokens will be caught natively by your FastAPI astream_events router
    response = await chain.ainvoke(prompt_args)
    
    # 8. Return the partial state update
    # The 'add_messages' reducer will append this AIMessage to state["messages"]
    return {"messages": [response]}

# =========================================================
# 5. SAVE HISTORY NODE
# =========================================================

async def save_memory(state: AgentState) -> dict:
    """
    Node 5: The Persistence Engine.
    Enforces a strict 15-message sliding window and saves the raw history to MySQL.
    """
    # Your existing context variable (set by your FastAPI middleware/dependency)
    db_session_var: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar("db_session")
    
    # 1. Retrieve the database session injected by the FastAPI route
    db_session = db_session_var.get()
    
    # 2. Strict Zero-Trust Identity Extraction
    employee_id = state["user_context"]["employee_id"]
    
    # 3. Retrieve the complete timeline from the state
    all_messages = state["messages"]
    
    # 4. Enforce the 15-message sliding window
    if len(all_messages) > 15:
        # Keep only the most recent 15 messages
        recent_messages = all_messages[-15:]
    else:
        recent_messages = all_messages
        
    # 5. Serialize the LangChain objects back into a standard Python list of dicts
    # This automatically converts HumanMessage, AIMessage, and ToolMessage into JSON-safe dictionaries
    serialized_history = messages_to_dict(recent_messages)
    
    # 6. Execute the database update
    await update_chat_history(
        db=db_session, 
        employee_id=employee_id, 
        messages_json=serialized_history
    )
    
    # Node 4 handles side-effects only. Returning an empty dict means no state mutations.
    return {}