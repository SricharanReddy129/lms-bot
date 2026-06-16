from typing import Annotated, TypedDict, Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class LongTermMemory(TypedDict):
    """
    Structured long-term memory fetched from the database 
    at the start of the execution loop.
    """
    # A concise semantic summary of all conversations prior to this thread
    conversation_summary: str
    
    # The last 4-5 raw messages from the previous session to preserve immediate context
    recent_history_slice: List[BaseMessage]

class AgentState(TypedDict):
    # Short-term working memory for the *current* live execution loop
    messages: Annotated[list[BaseMessage], add_messages]
    
    # The decoded identity payload (e.g., {"employee_name": "Vikram", "role": "Manager"})
    user_context: Dict[str, Any]
    
    # The newly structured long-term memory architecture
    long_term_memory: LongTermMemory