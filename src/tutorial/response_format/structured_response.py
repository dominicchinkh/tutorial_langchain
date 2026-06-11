"""
AI-Powered Weather Reporter with Structured Output.

What It Does
------------
This script automates the process of fetching and structuring real-time 
weather information for a requested location (specifically Canberra, Australia, 
in this configuration). It bridges the gap between raw web search data and 
strongly-typed Python data structures.

How It Does It
--------------
1. Environment Setup: It loads API credentials for the Tavily search engine 
   using `python-dotenv`.
2. Tool Definition: It wraps the Tavily Client in a Python function 
   (`internet_search`) to allow the AI agent to interact with the live internet.
3. Schema Enforcement: It defines a strict Pydantic model (`WeatherReport`) 
   specifying exactly what data fields are required (e.g., temperature, 
   humidity, wind speed) and their data types.
4. Agent Initialization: It instantiates a DeepAgent using the 
   `gemini-2.5-flash-lite` model via `deepagents.graph`. The agent is explicitly 
   bound to the `WeatherReport` response format and granted access to the 
   search tool.
5. Execution: The agent is invoked with a natural language query. It recognizes 
   it needs real-time data, calls the `internet_search` tool, parses the search 
   results, maps them perfectly to the Pydantic schema, and returns the result.

Expected Outcome
----------------
The script prints an instantiated `WeatherReport` Pydantic object containing 
validated, real-time weather data for Canberra. 

Example Output:
    location='Canberra' temperature=11.4 condition='Partly cloudy' humidity=94 wind_speed=4.0 forecast='The forecast for the next 24 hours is partly cloudy with a chance of rain.'
"""
import os

from deepagents.graph import create_deep_agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tavily import TavilyClient
from typing import Literal

load_dotenv()

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        topic=topic,
        include_raw_content=include_raw_content,
    )

class WeatherReport(BaseModel):
    """A structured weather report with current conditions and forecast."""
    location:      str = Field(description="The location for this weather report")
    temperature: float = Field(description="Current temperature in Celsius")
    condition:     str = Field(description="Current weather condition (e.g., sunny, cloudy, rainy)")
    humidity:      int = Field(description="Humidity percentage")
    wind_speed:  float = Field(description="Wind speed in km/h")
    forecast:      str = Field(description="Brief forecast for the next 24 hours")
    
agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash-lite",
    response_format=WeatherReport,
    tools=[internet_search]
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in Canberra?"
            }
        ]
    }
)

print(result["structured_response"])
