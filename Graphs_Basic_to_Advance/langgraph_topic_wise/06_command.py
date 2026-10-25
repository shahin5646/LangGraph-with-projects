from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# 1. Define the state
class GraphState(TypedDict):
    temperature: int
    status_messages: str
    warning_sent: bool
    final_action_performed: str

# 2. Define the Command-enabled node

def check_temp_node(state: GraphState) -> Command[Literal["warn_user", "success"]]:
    """
    A node that uses Command to both update state and route conditionally.
    
    The return type must be annotated with Command and a Literal list
    of all possible destination nodes.
    """
    temp = state["temperature"]
    print(f"Executing 'check_temp_node': Current Temp is {temp}degrees")

    # If temperature is high, send a warning and route to 'warn_user'
    if temp > 90:
        print("--- ALERT: Temp too high! Issuing command to warn user --- ")

        return Command(
            update= {
                "status_message": "Routing to warning handler...",
                "warning_sent": True
            },
            goto="warn_user"
        )
    # If temperature is safe, route directly to 'success'
    else:
        print("--- OK: Temp is ok. Issuing command to route to 'success'")
        return Command(
            update={
                "status_message": "Routing to Success Handler..."
            },
            goto="success"
        )
    
# 3. Define your action nodes

def warn_user(state: GraphState):
    print(f"Executing 'warn_user': Warning successfully sent at {state['temperature']}°C.")

    return {
        "final_action_performed": "Warning Notification sent"
    }

def success(state: GraphState):
    print("Executing success_node: Process completed successfully.")
    return {
        "final_action_performed": "Temperate Safety Confirmed"
    }

# 4. Build Graph

builder = StateGraph(GraphState)

builder.add_node(check_temp_node)
builder.add_node(warn_user)
builder.add_node(success)

builder.add_edge(START, "check_temp_node")
# You don't need to explictly declare edges to the nodes you route to with Command
# You also don't need to terminate them at END

graph = builder.compile()

"""Testing the Graph"""

# Test 1: High Temperature

high_temp_initial_state = {
    "temperature": 100
}

final_state_1 = graph.invoke(high_temp_initial_state)

print("High Temperature Final State:")
print(final_state_1)
print("="* 50)
print()

# Test 2: Low Temperature
low_temp_initial_state = {
    "temperature": 40
}

final_state_2 = graph.invoke(low_temp_initial_state)

print("Low Temperature Final State:")
print(final_state_2)