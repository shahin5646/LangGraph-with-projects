from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
import random

# 1. Define the state
class WeatherState(TypedDict):
    city: str
    temperature: float
    conditions: str

# 2. Simulate an API error that can be raised
class APIError(Exception):
    """Simulated API Error""" 
    pass

# 3. Create a node that makes an API request with a 70% chance of failing
def fetch_weather(state: WeatherState) -> WeatherState:
    """
    Simulates calling an external weather API
    Will randomly fail to demonstrate retry behavior
    """
    city = state['city']

    # Simulate the failure
    if random.random() < 0.7:
        print(f"❌ API call failed for {city}") # The number of times this message prints is the number of times the request failed
        raise APIError(f"Weather API timeout for {city}")
    

    # Success case
    print(f"✅ Successfully fetched weather for {city}")

    # Simulate API response
    temp = round(random.uniform(15, 30), 1)
    conditions = random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"])

    return {
        "temperature": temp,
        "conditions": conditions
    }

# 4. Create another node to present the result
def format_result(state: WeatherState):
    """Format the weather data"""
    print(f"\n🌤️ Weather Report for {state['city']}:")
    print(f"Temperature: {state['temperature']} degrees")
    print(f"Conditions: {state['conditions']}")

    return state

"""Build the Graph"""

builder = StateGraph(WeatherState)

# 5. Add notes
# Add a retry policy to the node that makes API requests
builder.add_node(
    "fetch_weather", 
    fetch_weather, 
    retry_policy=RetryPolicy(
        max_attempts=5,
        initial_interval=1.0,
        backoff_factor=2.0,
        max_interval=10.0,
        jitter=True,
        retry_on=APIError
    )
)

builder.add_node("format_result", format_result)

# 6. Add Edges
builder.add_edge(START, "fetch_weather")
builder.add_edge("fetch_weather", "format_result")
builder.add_edge("format_result", END)

graph = builder.compile()

"""Test out the Graph"""
# Use try...except just in case all attempts failed
try:
    result = graph.invoke({
        "city": "San Francisco",
        "temperature": 0.0,
        "conditions": ""
    })

    print(f"\n✨ Final Result: {result}")

except Exception as e:
    print(f"\n💥 All retry attempts exhausted: {e}")