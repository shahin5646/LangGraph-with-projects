"""
LangGraph agent demo: a chatbot that can call tools.

Shows:
  - Defining tools with @tool
  - Binding tools to the LLM
  - The loop: chat_bot -> tools -> chat_bot -> ... until no more tool calls
  - Memory across turns with a checkpointer

Requirements:
  pip install langgraph langchain langchain-openai python-dotenv
  .env file containing INMETECH_API_KEY
"""

import ast
import operator
import os
from typing import Annotated

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel


# --- Setup ---
load_dotenv()

api_key = os.getenv("INMETECH_API_KEY")
if not api_key:
    raise ValueError("INMETECH_API_KEY is missing from your .env file.")

llm = ChatOpenAI(
    model="gpt-4.1-nano",
    base_url="https://api.inmetech.com/api/v1",
    api_key=api_key,
)


# --- Tools ---
@tool
def weather_tool(city: str) -> str:
    """Get the current temperature in Celsius for a city.

    Args:
        city: City name, for example "rajshahi".
    """
    # Mock data. Replace with a real weather API call.
    data = {"dhaka": 32, "sylhet": 38, "rajshahi": 36}

    temp = data.get(city.strip().lower())
    if temp is None:
        return f"No weather data available for {city}."
    return f"{temp}°C"


# Only these math operations are allowed (no eval, which can run arbitrary code).
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    """Recursively evaluate a parsed math expression using only safe operations."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("Exponent too large")
        return SAFE_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression, for example '4 * 4 - 4'.

    Args:
        expression: Arithmetic using numbers and + - * / % ** only.
    """
    try:
        result = _safe_eval(ast.parse(expression, mode="eval").body)
        return str(result)
    except Exception:
        return "Please provide a valid math expression."


# --- State ---
class AgentState(BaseModel):
    messages: Annotated[list, add_messages]


# --- Nodes ---
tools = [weather_tool, calculate]
llm_with_tools = llm.bind_tools(tools)


def chat_bot(state: AgentState) -> dict:
    """Ask the LLM what to do next: answer directly or call a tool."""
    reply = llm_with_tools.invoke(state.messages)
    return {"messages": [reply]}


tool_node = ToolNode(tools)


# --- Build the graph ---
builder = StateGraph(AgentState)
builder.add_node("chat_bot", chat_bot)
builder.add_node("tools", tool_node)

builder.add_edge(START, "chat_bot")
# If the LLM requested a tool, go to "tools". Otherwise go to END.
builder.add_conditional_edges("chat_bot", tools_condition)
# After running a tool, go back to the LLM so it can use the result.
builder.add_edge("tools", "chat_bot")

# Swap InMemorySaver for SqliteSaver if you want history to survive restarts.
graph = builder.compile(checkpointer=InMemorySaver())


# --- Helper to talk to the agent ---
def ask(text: str, thread_id: str) -> str:
    """Send one message, print the question, any tool activity, and the answer."""
    print(f"[{thread_id}] You: {text}")

    result = graph.invoke(
        {"messages": [HumanMessage(content=text)]},
        {"configurable": {"thread_id": thread_id}},
    )
    messages = result["messages"]

    # Show only what happened during this turn (after the latest user message)
    last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
    for m in messages[last_human + 1:]:
        if isinstance(m, AIMessage) and m.tool_calls:
            for call in m.tool_calls:
                print(f"    tool call   : {call['name']}({call['args']})")
        elif isinstance(m, ToolMessage):
            print(f"    tool result : {m.content}")

    answer = messages[-1].content
    print(f"[{thread_id}] AI : {answer}\n")
    return answer


# --- Demo ---
if __name__ == "__main__":
    print("=== Single tool call ===\n")
    ask("What is the temperature in rajshahi?", "demo-1")

    print("=== Calculator tool ===\n")
    ask("What is 4 * 4 - 4?", "demo-1")

    print("=== Two tools in one question ===\n")
    ask("What is the temperature in sylhet, and what is that multiplied by 2?", "demo-1")

    print("=== Memory: follow-up on the same thread ===\n")
    ask("And what about dhaka?", "demo-1")

    print("=== No tool needed ===\n")
    ask("Say hello in one short sentence.", "demo-2")