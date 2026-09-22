from langgraph.graph import START, END, StateGraph
from typing_extensions import TypedDict
from typing import Literal

"""
-a node is a function or an LLM call that transforms your state and moves your graph forward, 
-while edges are the arrows in a flowchart — without them a node has nowhere to send its results.
-So the rule of thumb is: nodes do work, edges decide where the work goes next.
_____SOURCE: medium blog

"""


# state
class State(TypedDict):
    graph_str:str

# nodes
def node1(state: State)->State:
    """this node greet our user"""
    return {"graph_str": state["graph_str"] + "welcome to AI Carrer Lab"}

def node2(state: State)->State:
    """this node greet our user"""
    return {"graph_str": state["graph_str"] + "I am in Node 2"}
    

def node3(state: State)->State:
    """this node greet our user"""
    return {"graph_str": state["graph_str"] + "I am in Node 3"}

# edges
def next_step(state: State) -> Literal["node2", "node3"]:
    """guide the state/graph to next node"""
    state_str = state["graph_str"]
    array_state_str = state_str.split(" ")

    if array_state_str[0] == "hello":
        return "node2"

    return "node3"


# putting the groph together
builder = StateGraph(State)

builder.add_node("node1",node1)
builder.add_node("node2",node2)
builder.add_node("node3",node3)

builder.add_edge(START, "node1")
builder.add_conditional_edges("node1", next_step)
builder.add_edge("node2", END)
builder.add_edge("node3", END)

graph = builder.compile()