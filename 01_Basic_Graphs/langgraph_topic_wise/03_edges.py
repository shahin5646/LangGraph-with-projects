import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


# --- 1. Graph State ---
class GraphState(TypedDict):
    input: str
    # Reducer appends each node's returned list to the existing one.
    execution_path: Annotated[list[str], operator.add]


# --- 2. Nodes ---
def node_a(state: GraphState) -> dict:
    print("Executing Node A...")
    return {"execution_path": ["node_a"]}


def node_b(state: GraphState) -> dict:
    print("Executing Node B...")
    return {"execution_path": ["node_b"]}


def node_c(state: GraphState) -> dict:
    """A node in the 'conditional' path."""
    print("Executing Node C...")
    return {"execution_path": ["node_c"]}


def node_d(state: GraphState) -> dict:
    """Another node in the 'conditional' path."""
    print("Executing Node D...")
    return {"execution_path": ["node_d"]}


# --- 3. Conditional Edge Function ---
# Returning node names directly (typed as Literal) means no path map is needed,
# and LangGraph can infer the possible destinations for visualization.
def should_continue(state: GraphState) -> Literal["node_c", "node_d"]:
    print("Evaluating conditional edge...")
    if "go_to_c" in state["input"]:
        print("-> Condition met: Routing to Node C.")
        return "node_c"
    print("-> Condition not met: Routing to Node D.")
    return "node_d"


# --- 4. Build and Compile ---
builder = StateGraph(GraphState)

builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("node_c", node_c)
builder.add_node("node_d", node_d)

builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_conditional_edges("node_b", should_continue)
builder.add_edge("node_c", END)
builder.add_edge("node_d", END)

graph = builder.compile()


# --- 5. Run ---
print("--- Example 1: Path is A -> B -> D ---")
final_state_1 = graph.invoke(
    {"input": "Hello, this is a message.", "execution_path": []}
)
print("\nFinal State (A->B->D):", final_state_1)

print("\n" + "=" * 50 + "\n")

print("--- Example 2: Path is A -> B -> C ---")
final_state_2 = graph.invoke(
    {"input": "Hello, go_to_c to continue.", "execution_path": []}
)
print("\nFinal State (A->B->C):", final_state_2)