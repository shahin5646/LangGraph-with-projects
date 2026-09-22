# importing our lib
from langgraph.graph import StateGraph, START, END

# State
# using plain str as the graph state

# nodes
def greeting(state: str) -> str:
    """this function greets people to ACL"""
    return state + "welcome to AI Career Lab!"

# edges
# start -> greeting -> end

# langGraph putting our graph together
builder = StateGraph(str)

# add nodes to our graph
builder.add_node("greeting", greeting)

# add edges
builder.add_edge(START, "greeting")
builder.add_edge("greeting", END)

# compile the graph
graph = builder.compile()