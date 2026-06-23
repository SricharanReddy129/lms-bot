from typing import Annotated, TypedDict, Dict, Any, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # Short-term working memory for the *current* live execution loop
    messages: Annotated[list[BaseMessage], add_messages]
    
    # The decoded identity payload (e.g., {"employee_name": "Vikram", "role": "Manager"})
    user_context: Dict[str, Any]
    
    # The newly structured long-term memory architecture
    recent_history_slice: List[BaseMessage]