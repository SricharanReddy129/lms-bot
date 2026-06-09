from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'add_messages' ensures new messages are appended to the list, not overwritten
    messages: Annotated[list[BaseMessage], add_messages]
    
    # This is where the token will live during the graph execution
    auth_token: str