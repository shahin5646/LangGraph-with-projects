"""
LangGraph human-in-the-loop demo: pause a graph and wait for the user.

Shows:
  - interrupt() pausing the graph to ask the user a question
  - Command(resume=...) continuing the graph with the user's answer
  - Why a checkpointer and a thread_id are required
  - Routing to different nodes based on the answer

Requirements:
  pip install langgraph pydantic
"""

from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel


# --- State ---
class PurchaseState(BaseModel):
    item: str = ""
    price: int = 0
    confirmed: bool = False
    status: str = ""


# --- Nodes ---
def show_order(state: PurchaseState) -> dict:
    """Print the order summary."""
    print(f"    Order summary: {state.item}, price {state.price}")
    return {"status": "awaiting confirmation"}


def ask_confirmation(state: PurchaseState) -> dict:
    """Pause the graph and wait for the user to answer yes or no."""
    # The graph stops here. The value inside interrupt() is shown to the caller.
    # When resumed, interrupt() returns whatever was passed to Command(resume=...).
    response = interrupt(
        {
            "question": (
                f"Confirm your purchase of {state.item} for {state.price}? "
                "Reply yes or no."
            )
        }
    )

    # Anything other than an explicit yes counts as no (safest default for payments).
    confirmed = str(response).strip().lower() in {"yes", "y"}
    return {"confirmed": confirmed}


def cancel_order(state: PurchaseState) -> dict:
    print("    Your order was cancelled. Thanks.")
    return {"status": "cancelled"}


def confirm_order(state: PurchaseState) -> dict:
    print("    Your order was placed successfully.")
    return {"status": "confirmed"}


# --- Routing function (not a node: it only chooses the next node) ---
def route_by_answer(state: PurchaseState) -> Literal["cancel", "confirm"]:
    return "confirm" if state.confirmed else "cancel"


# --- Build the graph ---
builder = StateGraph(PurchaseState)
builder.add_node("show_order", show_order)
builder.add_node("ask_confirmation", ask_confirmation)
builder.add_node("cancel", cancel_order)
builder.add_node("confirm", confirm_order)

builder.add_edge(START, "show_order")
builder.add_edge("show_order", "ask_confirmation")
builder.add_conditional_edges("ask_confirmation", route_by_answer)
builder.add_edge("cancel", END)
builder.add_edge("confirm", END)

# A checkpointer is required: it saves the paused graph so it can be resumed later.
graph = builder.compile(checkpointer=InMemorySaver())


# --- Helpers ---
def start_order(item: str, price: int, thread_id: str) -> None:
    """Run the graph until it pauses, then print the question it is asking."""
    print(f"[{thread_id}] Starting order: {item}, {price}")

    result = graph.invoke(
        {"item": item, "price": price},
        {"configurable": {"thread_id": thread_id}},
    )

    interrupts = result.get("__interrupt__")
    if interrupts:
        print(f"[{thread_id}] AI asks: {interrupts[0].value['question']}")
    else:
        print(f"[{thread_id}] Finished without pausing.")


def reply_to_order(answer: str, thread_id: str) -> None:
    """Resume the paused graph with the user's answer and print the result."""
    print(f"[{thread_id}] You: {answer}")

    result = graph.invoke(
        Command(resume=answer),
        {"configurable": {"thread_id": thread_id}},
    )

    print(f"[{thread_id}] Final status: {result['status']}\n")


# --- Demo ---
if __name__ == "__main__":
    print("=== User says no ===\n")
    start_order("Samsung S23", 12000, "order-1")
    reply_to_order("no", "order-1")

    print("=== User says yes ===\n")
    start_order("Samsung S23", 12000, "order-2")
    reply_to_order("yes", "order-2")
    
    
    
"""
?
How it works

interrupt() stops the graph. invoke returns early, and the question is available under result["__interrupt__"].
Command(resume="no") continues it. That value becomes the return value of interrupt() inside the node.
The same thread_id is essential. It tells LangGraph which paused run to resume. A different thread ID would start a fresh run.
The checkpointer is what makes pausing possible. Without one, there’s nowhere to save the paused state.

"""
