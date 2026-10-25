# imports
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# state
class State(TypedDict):
    graph_str: str


# nodes
def greeting(state: State) -> State:
    """This Function return a state with welcome message"""
    return {"graph_str": state["graph_str"]+"Welcome to LangGraph learning Journey!!!!!!!!!!!"}

# edges
# start -> greeting -> End
# putting graph together 
builder = StateGraph(State)

# add nodes
builder.add_node("greeting",greeting)

# add edges
builder.add_edge(START, "greeting")
builder.add_edge("greeting", END)

# creating a graph by cimpiling
graph = builder.compile()