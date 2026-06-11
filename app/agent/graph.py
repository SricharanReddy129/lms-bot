from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langsmith import traceable

from app.agent.state import AgentState

# 1. Import all the individual tool files based on your directory structure
from app.agent.tools.leave_balance_tool import view_my_leave_balance, view_employee_leave_balance
from app.agent.tools.holiday_calendar_tool import view_holiday_calendar
from app.agent.tools.apply_leave_tool import apply_for_leave
from app.agent.tools.pending_leaves_tool import view_my_pending_leaves, view_team_pending_leaves
from app.agent.tools.approve_leaves_tool import approve_leave_requests
from app.agent.tools.reject_leaves_tool import reject_leave_requests
from app.agent.tools.view_approved_leaves_tool import view_my_approved_leaves, view_team_approved_leaves
from app.agent.tools.view_rejected_leaves_tool import view_my_rejected_leaves, view_team_rejected_leaves
# =========================================================
# SYSTEM CONFIGURATION
# =========================================================

LEAVE_ASSISTANT_PROMPT = """
You are an intelligent, professional HR Leave Management Assistant.
Your primary job is to help employees and managers handle time-off requests.
Always use the provided tools to check balances, view history, or take action.

CRITICAL RULES:
1. Never guess or hallucinate leave balances or system data. Always fetch it.
2. If a tool returns an error (like a 403 Forbidden or 404 Not Found), politely apologize to the user and explain the exact reason given by the system.
3. Be concise and professional in your responses.
"""

# =========================================================
# LLM & TOOL INITIALIZATION
# =========================================================

# Initialize the local Llama 3.1 model via Ollama
# Temperature 0 ensures strict, analytical adherence to your Pydantic schemas
llm = ChatOllama(
    model="llama3.1",
    temperature=0,
)

# Bundle tools and bind them to the LLM
tools = [
    view_my_leave_balance, view_employee_leave_balance, view_holiday_calendar,
    apply_for_leave, view_my_pending_leaves, view_team_pending_leaves,
    approve_leave_requests, reject_leave_requests, view_my_approved_leaves,
    view_team_approved_leaves, view_my_rejected_leaves, view_team_rejected_leaves
]

llm_with_tools = llm.bind_tools(tools)

# =========================================================
# GRAPH NODES
# =========================================================

@traceable
async def call_model(state: AgentState):
    """The primary node that injects the system prompt and calls the LLM."""
    messages = state["messages"]
    
    # Inject the system prompt if it is not already the first message
    if messages and not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=LEAVE_ASSISTANT_PROMPT)] + messages
        
    # The LLM reads the messages and the state invisibly holds the auth_token
    response = await llm_with_tools.ainvoke(messages)
    
    return {"messages": [response]}

# LangGraph's pre-built node automatically handles tool execution and error catching
tool_node = ToolNode(tools)

# =========================================================
# COMPILATION
# =========================================================

workflow = StateGraph(AgentState)

# Add the two core nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set the entry point
workflow.set_entry_point("agent")

# Use the pre-built conditional edge directly
# tools_condition automatically routes to "tools" if a tool call exists, or "__end__" if not
workflow.add_conditional_edges("agent", tools_condition)

# After tools execute, loop back to the agent
workflow.add_edge("tools", "agent")

# Compile the graph into an executable application
agent_app = workflow.compile()