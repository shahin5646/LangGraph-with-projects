"""
LangGraph memory demo: short-term memory with checkpointers.

Shows:
  - In-memory checkpointer (history is lost when the program stops)
  - SQLite checkpointer (history survives restarts)
  - How thread_id keeps conversations separate

Requirements:
  pip install langgraph langchain-openai python-dotenv langgraph-checkpoint-sqlite
  .env file containing INMETECH_API_KEY
"""

import os
import sqlite3
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel


#  Setup 
load_dotenv()

api_key = os.getenv("INMETECH_API_KEY")
if not api_key:
    raise ValueError("INMETECH_API_KEY is missing from your .env file.")

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://api.inmetech.com/api/v1",
    api_key=api_key,
)


#  State 
class ChatState(BaseModel):
    # add_messages appends new messages to the history instead of replacing it
    messages: Annotated[list, add_messages]


#  Node 
def chat_bot(state: ChatState) -> dict:
    """Send the full conversation history to the LLM and return only the new reply."""
    reply = llm.invoke(state.messages)
    return {"messages": [reply]}


#  Build the graph (uncompiled) 
builder = StateGraph(ChatState)
builder.add_node("chat_bot", chat_bot)
builder.add_edge(START, "chat_bot")
builder.add_edge("chat_bot", END)


#  Helper to talk to a graph 
def ask(graph, text: str, thread_id: str) -> str:
    """Send one user message on a thread, print the question and the answer."""
    print(f"[{thread_id}] You: {text}")

    result = graph.invoke(
        {"messages": [HumanMessage(content=text)]},
        {"configurable": {"thread_id": thread_id}},
    )
    answer = result["messages"][-1].content

    print(f"[{thread_id}] AI : {answer}\n")
    return answer


#  Option A: in-memory checkpointer 
def demo_in_memory() -> None:
    print("=== In-memory checkpointer ===\n")
    graph = builder.compile(checkpointer=InMemorySaver())

    ask(graph, "My name is Prateek.", "thread-1")
    ask(graph, "What is my name?", "thread-1")   # same thread: remembers
    ask(graph, "What is my name?", "thread-2")   # new thread: doesn't know


#  Option B: SQLite checkpointer (persists to disk) 
def demo_sqlite() -> None:
    print("=== SQLite checkpointer ===\n")
    connection = sqlite3.connect("db.sqlite3", check_same_thread=False)
    graph = builder.compile(checkpointer=SqliteSaver(connection))

    ask(graph, "My name is Prateek.", "thread-A")
    ask(graph, "What is my name?", "thread-A")
    # Run the script again later and ask only "What is my name?" on "thread-A":
    # the history is loaded from db.sqlite3, so it still remembers.


if __name__ == "__main__":
    demo_in_memory()
    demo_sqlite()