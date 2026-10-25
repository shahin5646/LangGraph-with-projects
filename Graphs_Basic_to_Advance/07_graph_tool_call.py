from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()

model_llm = ChatOpenAI(model="gpt-4o")

@tool
def multiply(nb1: int, nb2: int) -> int:
    """This tool is used for multiplying 2 numbers and returning the product"""
    return nb1*nb2

model_llm_with_tool = model_llm.bind_tools([multiply])

# nodes
def chat_with_tool(state: MessagesState) -> MessagesState:
    return {"messages": [model_llm_with_tool.invoke(state["messages"])]}

builder = StateGraph(MessagesState)

builder.add_node("chat_with_tool", chat_with_tool)
builder.add_node("tools", ToolNode([multiply]))

builder.add_edge(START, "chat_with_tool")
builder.add_conditional_edges("chat_with_tool", tools_condition)
builder.add_edge("tools",END)

graph = builder.compile()



"""
def tool_node(state: MessagesState) -> MessagesState:
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    response = multiply.invoke(tool_call["args"])

    return {"messages": [ToolMessage(content=str(response),
                                      tool_call_id=tool_call["id"])]}


# creating condinial edges logic
def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:

    last_message = state["messages"][-1]

    # Did the LLM request a tool?
    if last_message.tool_calls:
        return "tool_node"

    return "__end__"
"""