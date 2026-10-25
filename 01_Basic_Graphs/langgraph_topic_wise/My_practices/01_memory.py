import os
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Annotated, List
from dotenv import load_dotenv

load_dotenv()

#  Setup 
load_dotenv()

api_key = os.getenv("INMETECH_API_KEY")
if not api_key:
    raise ValueError("INMETECH_API_KEY is missing from your .env file.")

llm = ChatOpenAI(
    model="gpt-4.1-nano",
    base_url="https://api.inmetech.com/api/v1",
    api_key=api_key,
)


# state
class ChatState(BaseModel):
    """  """
    messages: Annotated[list, add_messages]

# nodes
def chat_node(state: ChatState)-> dict:
    """Send The full conversation history to the llm and get a new reply """
    reply = llm.invoke(state.messages)
    return {
        "messages": [reply]
    }

# building graph without compiling
builder = StateGraph(ChatState)

builder.add_node("chat_node", chat_node)

builder.add_edge(START,"chat_node")
builder.add_edge("chat_node", END)


# Helper to talk to a graph 
def ask(graph, thread_id: str, text: str) -> str:
    """send one user message to a thread and answer the questions"""
    print(f"[Thread_id = {thread_id}], You: {text}")
    
    result = graph.invoke({
        {"messages": [HumanMessage(content=text)]},
        {"configurable":{"thread_id": thread_id}}
    })
    
    answer = result["messages"][-1].content
    print(f"[{thread_id}], AI: {answer}\n")
    
    return answer
    
    