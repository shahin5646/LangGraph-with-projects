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
    model="gpt-4.1-nano",
    base_url="https://api.inmetech.com/api/v1",
    api_key=api_key,
)


# state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# node for gwtting response from the llm
def chat_node(state: AgentState) -> dict:
    """It will invoke the llm to get a response """
    chat_history = state["messages"]
    response = llm.invoke(chat_history)
    
    # return the updated chat history to the llm
    return {
        "messages": response
    }

# builder
agent_graph = StateGraph(AgentState)

# coonecting nodes and 
agent_graph.add_node("chat_node", chat_node)

agent_graph.add_edge(START, "chat_node")
agent_graph.add_edge("chat_node", END)

# compile the graph
agent = agent_graph.compile()

# First turn of the messages
message1 = HumanMessage(content="Hi, I am Shahin and I am an AI Engineer")

# invoke the graph to get the resulting state
turn1_state = agent.invoke({
    "messages": message1
})

# Show the results
print("--- Graph State after first turn ---")
print(turn1_state)
print("-"* 30)

# Second message
message2 = HumanMessage(content="What was my name and my profession ?")

# invoke state and previous history plus present new message
turn2_state = agent.invoke({
    "messages": turn1_state["messages"] + [message2]
})


print("--- Graph State after second turn ---")
print(turn2_state)
print("-"* 30)
