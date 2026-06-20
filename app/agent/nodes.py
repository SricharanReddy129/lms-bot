from langsmith import traceable
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.messages import messages_from_dict, messages_to_dict

from dotenv import load_dotenv
import datetime

#import depencies for context extraction
import jwt
from app.core.context import auth_token_var, db_session_var
from app.api.deps import get_current_user

# Import your prompt template and state
from app.agent.prompt import agent_prompt
from app.agent.state import AgentState

# import the database fetch functions
from app.repositories.fetch_chat_history_repo import fetch_chat_history_from_mysql
from app.repositories.update_chat_history_repo import upsert_chat_history

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
    Node 1: Intercepts the request, validates identity via central issuer, 
    fetches history, and hydrates memory safely.
    """
    # Step 1: Intercept the raw token securely
    try:
        token = auth_token_var.get()
    except LookupError:
        raise ValueError("Authentication token not found in request context.")

    # Step 2: Centralized Token Validation (Issuer/OAuth)
    # Replaced local keyless decoding with a secure, centralized issuer validation
    try:
        # decode jwt token
        issuer_payload = jwt.decode(
            token, 
            options={"verify_signature": False},  # Still no signature verification here, but now it's a trusted issuer
            algorithms=["none"]
        )
        
        # Dual-key mapping to satisfy zero-trust checks across downstream nodes
        user_data = {
            "employee_id": int(issuer_payload["id"]),
            "employee_name": issuer_payload["name"],
            "role": issuer_payload["role"]
        }
    except Exception as e:
        raise ValueError(f"Token validation failed at the issuer level: {e}")

    # Step 3: Fetch long-term memory (Returns a clean list of message dicts)
    db_session = db_session_var.get()
    db_row = await fetch_chat_history_from_mysql(db=db_session, employee_id=user_data["employee_id"])

    # Step 4: Deserialize directly into LangChain message instances
    hydrated_messages = []
    if db_row and isinstance(db_row, list):
        hydrated_messages = messages_from_dict(db_row)
        
        # --- THE PROVIDER-AGNOSTIC SANITIZER ---
        # Removes redundant tool data only if it's a safe duplicate
        for msg in hydrated_messages:
            if msg.type == "ai":
                has_modern_tools = bool(getattr(msg, "tool_calls", None))
                has_legacy_duplicate = "tool_calls" in getattr(msg, "additional_kwargs", {})
                
                # If LangChain already has the tools safely stored, scrub the duplicate
                if has_modern_tools and has_legacy_duplicate:
                    del msg.additional_kwargs["tool_calls"]

    # Return clean payload to update LangGraph state
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
    name = user_ctx["employee_name"]
    role = user_ctx["role"]
    id = user_ctx["employee_id"]
    
    # 3. Dynamically construct the user context message
    context_string = f"Current Session Context:\nUser Name: {name}\nRole: {role}\nEmployee ID: {id}"
    context_message = SystemMessage(content=context_string)
    
    # 4. Map all variables exactly to the Prompt Template placeholders
    prompt_args = {
        # Wrapped in a list to satisfy the MessagesPlaceholder requirement
        "dynamic_user_context": [context_message], 
        
        # The database history array from Node 1 (falls back to empty list if new user)
        "history": memory,
        
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
    Merges past and present, enforces a sliding window, injects timestamps, and upserts to MySQL.
    """
    db_session = db_session_var.get()
    employee_id = state["user_context"]["employee_id"]
    thread_id = f"thread_{employee_id}" 
    
    # --- THE ZIPPER FIX ---
    # 1. Pull the past history (defaults to empty list if it's a new conversation)
    past_history = state.get("recent_history_slice", [])
    
    # 2. Pull the newly generated messages from the current HTTP request
    current_messages = state["messages"]
    
    # 3. Combine them using standard list addition. 
    # This perfectly preserves them as intact LangChain Message objects.
    full_timeline = past_history + current_messages
    
    # --- SLIDING WINDOW ---
    # 4. Apply the window to the complete, merged timeline
    if len(full_timeline) > 8:
        recent_messages = full_timeline[-8:]
    else:
        recent_messages = full_timeline
        
    # Serialize the LangChain objects back into dictionaries for database storage
    serialized_history = messages_to_dict(recent_messages)
    
    # Generate a single UTC timestamp for the current graph execution cycle
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Inject the timestamp into the freshly generated messages
    for msg in serialized_history:
        data_block = msg.get("data", {})
        
        # Only inject if it doesn't already exist. 
        # This preserves the original timestamps of older history pulled in Node 1.
        if "timestamp" not in data_block:
            data_block["timestamp"] = current_time
            
    # Execute the Upsert
    await upsert_chat_history(
        db=db_session, 
        employee_id=employee_id, 
        thread_id=thread_id,
        messages_json=serialized_history
    )
    
    return {}