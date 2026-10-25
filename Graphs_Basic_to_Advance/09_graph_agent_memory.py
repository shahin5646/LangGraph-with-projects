from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

model_llm = ChatOpenAI(model="gpt-4o")


# tools
@tool
def multiply(nb1: int, nb2: int) -> int:
    """Multiply two numbers and return the product."""
    return nb1 * nb2


@tool
def addition(nb1: int, nb2: int) -> int:
    """Add two numbers and return the sum."""
    return nb1 + nb2


@tool
def subtraction(nb1: int, nb2: int) -> int:
    """Subtract the second number from the first and return the difference."""
    return nb1 - nb2


tools = [multiply, addition, subtraction]
model_llm_with_tools = model_llm.bind_tools(tools)

system_message = SystemMessage(
    content="You are a helpful math teacher. Use the tools for every calculation."
)


# nodes
def chat_with_tools(state: MessagesState) -> dict:
    # The system message goes first. It is not saved in state,
    # so we add it again on every call.
    messages = [system_message] + state["messages"]
    return {"messages": [model_llm_with_tools.invoke(messages)]}


# graph
builder = StateGraph(MessagesState)

builder.add_node("chat_with_tools", chat_with_tools)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chat_with_tools")
builder.add_conditional_edges("chat_with_tools", tools_condition)
builder.add_edge("tools", "chat_with_tools")

graph = builder.compile(checkpointer=InMemorySaver())


def ask(text: str, thread_id: str) -> str:
    """Send one user message on a thread and return the model's final answer."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"messages": [HumanMessage(content=text)]}, config)
    return result["messages"][-1].content


# Runs only when you execute this file directly, not when it is imported
# (for example by `langgraph dev`).
if __name__ == "__main__":
    print("Thread 1:", ask("Add 3 and 4.", "1"))
    print("Thread 1:", ask("Multiply that by 2.", "1"))  # remembers the 7
    print("Thread 2:", ask("Multiply that by 2.", "2"))  # new thread: no memory