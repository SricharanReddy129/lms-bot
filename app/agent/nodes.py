from langsmith import traceable
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from dotenv import load_dotenv

# Import your prompt template and state
from app.agent.prompt import agent_prompt
from app.agent.state import AgentState

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
# 3. THE EXECUTION NODE
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