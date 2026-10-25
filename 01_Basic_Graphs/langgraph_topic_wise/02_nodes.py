# Demonstrates creating nodes , the arguments they can
# accept, and how they update the state.

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime


#  1. Graph State 
class GraphState(TypedDict, total=False):
    """Shared data structure for the graph."""
    # Initial input provided to the graph.
    input: str
    # Reducer (operator.add) appends each node's output instead of overwriting.
    results: Annotated[list[str], operator.add]


#  2. Runtime Context (optional) 
# Immutable per-run data passed via invoke(context=...). Not stored in state.
@dataclass
class ContextSchema:
    user_id: str


#  3. Nodes 
# Node A: takes only the state.
def plain_node(state: GraphState) -> dict:
    print("Executing plain_node...")
    return {"results": [f"Hello, {state['input']}!"]}


# Node B: also receives the RunnableConfig.
def node_with_config(state: GraphState, config: RunnableConfig) -> dict:
    print("Executing node_with_config...")
    thread_id = config.get("configurable", {}).get("thread_id")
    # Note: without a checkpointer, thread_id is only readable here;
    # it doesn't persist any state.
    print(f"-> thread_id from config: {thread_id}")
    return {"results": ["Config access successful."]}


# Node C: also receives the Runtime, which carries the typed context.
def node_with_runtime(state: GraphState, runtime: Runtime[ContextSchema]) -> dict:
    print("Executing node_with_runtime...")
    user_id = runtime.context.user_id  # typed attribute access
    print(f"-> user_id from runtime context: {user_id}")
    return {"results": [f"Runtime access successful (user: {user_id})."]}


#  4. Build the Graph 
def build_graph() -> CompiledStateGraph:
    builder = StateGraph(GraphState, context_schema=ContextSchema)

    builder.add_node("plain_node", plain_node)
    builder.add_node("config_node", node_with_config)
    builder.add_node("runtime_node", node_with_runtime)

    builder.add_edge(START, "plain_node")
    builder.add_edge("plain_node", "config_node")
    builder.add_edge("config_node", "runtime_node")
    builder.add_edge("runtime_node", END)

    return builder.compile()


if __name__ == "__main__":
    app = build_graph()

    initial_state: GraphState = {"input": "World", "results": []}
    run_config: RunnableConfig = {"configurable": {"thread_id": "user-1234"}}

    print(" Invoking the graph ")
    final_state = app.invoke(
        initial_state,
        config=run_config,
        context=ContextSchema(user_id="shahin_ad"),
    )

    print("\n Final State of the Graph ")
    print(final_state)