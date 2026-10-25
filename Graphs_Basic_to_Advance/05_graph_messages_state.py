# check Mural for Messages state explenation
from langgraph.graph import StateGraph, START, END, MessagesState
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from typing import List, Annotated
from langgraph.graph.message import add_messages #hover over to see it merges 2 arrays
from langchain_openai import ChatOpenAI

"""
# state 
class MessagesState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
"""
model_llm = ChatOpenAI(model="gpt-4o")

# nodes
def chat(state: MessagesState) -> MessagesState:
    return {"messages": [model_llm.invoke(state["messages"])]}

# edges

# create our graph
builder = StateGraph(MessagesState)

builder.add_node("chat", chat)

builder.add_edge(START, "chat")
builder.add_edge("chat", END)

graph = builder.compile()
