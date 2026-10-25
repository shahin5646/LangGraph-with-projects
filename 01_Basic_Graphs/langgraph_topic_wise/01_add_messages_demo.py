import os
from langgraph.graph import START, END, StateGraph
from typing import  List, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("INMETECH_API_KEY")

if not api_key:
    raise ValueError("INMETECH_API_KEY is missing from your .env file.")

llm = ChatOpenAI(
    model="gpt-4o",
    base_url="https://api.inmetech.com/api/v1",
    api_key=api_key,
)


# Define State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Define the LLM node

def chat_node(state: AgentState) -> dict:
    """A node that invokes the llm to get a response"""

    conversation_history = state["messages"]

    # Give the LLM the full conversation history
    response = llm.invoke(conversation_history)

    # Return the updated conversation history
    return {
        "messages": response # add_messages will figure this out
    }

# Build the Graph

agent_graph = StateGraph(AgentState)

agent_graph.add_node("chat_node", chat_node)

agent_graph.add_edge(START, "chat_node")
agent_graph.add_edge("chat_node", END)

agent = agent_graph.compile()

"""
---- Running Conversational Turns ----
"""

# Send your first messsage
message1 = HumanMessage(content="Hello there! My name is FK")

# Invoke the graph to get the final state (resulting state)
turn1_state = agent.invoke({
    "messages": message1
})

print("--- Graph State after first turn ---")
print(turn1_state)
print("-"* 30)

# Send your second messsage
message2 = HumanMessage(content="What is your favorite color?")

# Invoke the graph with the current conversation history + the new message
turn2_state = agent.invoke({
    "messages": turn1_state["messages"] + [message2]
})

print("--- Graph State after second turn ---")
print(turn2_state)
print("-"* 30)