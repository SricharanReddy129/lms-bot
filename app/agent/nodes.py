from langsmith import traceable
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from dotenv import load_dotenv

import contextvars
import jwt
from typing import Dict, Any
from langchain_core.messages import messages_from_dict

# Import your prompt template and state
from app.agent.prompt import agent_prompt
from app.agent.state import AgentState

# import the database fetch functions
from app.repositories.fetch_chat_history_repo import fetch_chat_history_from_mysql
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
        
        conversation_summary = db_row.get("conversation_summary", "No prior history.")
    else:
        # Handle the case where this is the employee's very first thread
        hydrated_messages = []
        conversation_summary = "New user. No prior history."

    # Return exactly what needs to be injected into the LangGraph state
    return {
        "user_context": user_data,
        "long_term_memory": {
            "conversation_summary": conversation_summary,
            "recent_history_slice": hydrated_messages
        }
    }

# =========================================================
# 4. THE EXECUTION NODE
# =========================================================

@traceable
async def call_model(state: AgentState):
    """The primary node that injects the system prompt and calls the LLM."""
    
    # Pipe the messages into the prompt template, then into the LLM.
    # The ChatPromptTemplate automatically handles the MessagesPlaceholder.
    chain = agent_prompt | llm_with_tools
    
    # The LLM reads the formatted messages. 
    # Network auth is completely invisible here (handled by contextvars).
    response = await chain.ainvoke({"messages": state["messages"]})
    
    return {"messages": [response]}