import os
from langgraph.graph import START, END, StateGraph
from typing_extensions import TypedDict
from typing import Literal, NotRequired
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

"""
how do you build a program whose branching logic depends on a probabilistic, non-deterministic model output, in a way that's still structured, debuggable, and extensible?

"""


# State 
class State(TypedDict):
    graph_int:NotRequired[int]
    graph_str:str
model_llm = ChatOpenAI(
    model="gpt-4o-mini",  # whichever chat model your gateway exposes
    base_url="https://api.inmetech.com/api/v1",
    api_key=os.getenv("INMETECH_API_KEY"),
)


# nodes
def node1(state: State) -> State:
    """take a state and ask our model to pick a number between 1 or 2"""
    model_response = model_llm.invoke("choose between 1 or 3 or 2. reply only with a number")

    if isinstance(int(model_response.content), int):
        return {"graph_int":int(model_response.content),
                "graph_str": state["graph_str"] + "passed by node 1"}
    return {"graph_int":0,
                "graph_str": state["graph_str"] + "passed by node 1"}

def node2(state: State) -> State:
    """take a state and ask our model to pick a number between 1 or 2"""
    return {"graph_int":state["graph_int"],
                "graph_str": state["graph_str"] + "passed by node 2"}

def node3(state: State) -> State:
    """take a state and ask our model to pick a number between 1 or 2"""
    return {"graph_int":state["graph_int"],
                "graph_str": state["graph_str"] + "passed by node 3"}

# create edges
def next_step(state: State) -> Literal["node2", "node3", END]:
    """check state and return which node to go"""
    number_state = state["graph_int"]
    if number_state == 2:
        return "node2"
    elif number_state == 3:
        return "node3"
    else:
        return END

# building graph
builder = StateGraph(State)

builder.add_node("node1", node1)
builder.add_node("node2", node2)
builder.add_node("node3", node3)

builder.add_edge(START, "node1")
builder.add_conditional_edges("node1", next_step)
builder.add_edge("node2", END)
builder.add_edge("node3", END)

graph = builder.compile()