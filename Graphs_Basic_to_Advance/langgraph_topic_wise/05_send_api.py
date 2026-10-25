from typing import TypedDict, Annotated, List
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# 1. Create the main State for the Graph
class OverallState(TypedDict):
    topic: str
    subtopics: List[str] #Unknow size of sub-topics
    research_results: Annotated[List[str], add] # Accumulates all the mapped operations
    final_report: str # Final synthesized result

# 2. Private state for the mapped nodes
class ResearchState(TypedDict):
    subtopic: str # state variable to recieve input from Send
    research_results: List[str] # Same as in main state for private state to append its results

# 3. Create the node that generates the subtopics to research
def generate_subtopics(state: OverallState):
    """Generate subtopics to research"""

    topic = state["topic"]

    # Create a dummy list of subtopics
    subtopics = [
        f"{topic} - History",
        f"{topic} - Current Trends", 
        f"{topic} - Future Outlook"
    ]

    return {
        "subtopics": subtopics
    }

# 4. Create the node that will act as the worker node operating on each subtopic
def research_subtopic(state: ResearchState):
    """Research a single subtopic - runs in parallel"""
    subtopic = state['subtopic']

    # Simulate research
    result = f"Research findings on '{subtopic}': [detailed analysis, data, insights...]"

    # Return results to matching field name to append to the list
    return {
        "research_results": [result]
    }

# 5. Create the node that compiles all the results
def compile_report(state: OverallState):
    """Combine all research into final report"""
    results = state['research_results']

    report = "=" * 50 + "\n"
    report += "COMPREHENSIVE RESEARCH REPORT\n"
    report += "=" * 50 + "\n\n"

    for i, result in enumerate(results, 1):
        report += f"{i}. {result}\n\n"

    return {
        "final_report": report
    }

# 6. Write the conditional edge that performs the mapping to multiple instances of the worker node
def continue_to_research(state: OverallState):
    """Create parallel research tasks via Send"""

    return [
        Send("research_subtopic", {"subtopic": s}) 
        for s in state["subtopics"]
    ]

"""Build the Graph"""
builder = StateGraph(OverallState)

builder.add_node("generate_subtopics", generate_subtopics)
builder.add_node("research_subtopic", research_subtopic)
builder.add_node("compile_report", compile_report)

# Generate the subtopics
builder.add_edge(START, "generate_subtopics")
# Add the conditional edge that will map to multiple worker nodes
builder.add_conditional_edges("generate_subtopics", continue_to_research)
# Compile all results
builder.add_edge("research_subtopic", "compile_report")
builder.add_edge("compile_report", END)

graph = builder.compile()

"""Run the Graph"""

result = graph.invoke({
    "topic": "Artificial Intelligence",
    "subtopics": [],
    "research_results": [],
    "final_report": ""
})

print(result['final_report'])