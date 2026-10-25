from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

# 1. Define the State
class GraphState(TypedDict):
    input : str
    result: str

# 2. Define the Runtime Context Schema
@dataclass
class MyGraphContext:
    """Schema for Runtime data"""

    # Non-default properties must be defined first
    # Define a field without a default (A Required field)
    # An error will be thrown if a value is not provided at invocation time
    user_agent: str

    docs_url: str = "https://docs.langchain.com/"
    db_connection: str = "mysql://user:password@localhost:3306/my_db"

    

# 3. Define a node that accesses our runtime context information
def context_access_node(state: GraphState, runtime: Runtime[MyGraphContext]) -> dict:
    print("--- Executing Context Node ---")
    db_string = runtime.context.db_connection
    docs_url = runtime.context.docs_url
    user_agent = runtime.context.user_agent

    print(f"Current DB Connection: {db_string}")
    print(f"Documentation URL: {docs_url}")
    print(f"User Agent: {user_agent}")

    # Return update to state
    return {
        "result": f"Context accessed. DB: {db_string.split('//')[0]}..."
    }

# 4. Build the Graph by passing both state and context schemas
builder = StateGraph(GraphState, context_schema=MyGraphContext)

builder.add_node("context_node", context_access_node)

builder.add_edge(START, "context_node")
builder.add_edge("context_node", END)

graph = builder.compile()

# 5. Run Graph

initial_state = {"input": "Start Process"}

# Example 1
print("="* 50)
print("Running Example 1: Using Context Defaults (DB connection is default)")
print("="* 50)

final_state_1 = graph.invoke(
    input=initial_state,
    context= {"user_agent": "Default-Run"}
)

print(f"\nFinal State 1: {final_state_1}")

# Example 2
print("\n\n" + "=" * 50)
print("Running Example 2: Overriding Context (DB connection is new)")
print("=" * 50)

final_state_2 = graph.invoke(
    input=initial_state,
    context={
        "user_agent": "Override-Run",
        # Override the defautl db connection for this run
        "db_connection": "postgres://new_user@remote_host:5432/production"
    }
)

print(f"\nFinal State 2: {final_state_2}")