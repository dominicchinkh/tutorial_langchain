"""
chat_model.py — LangChain Chat Model with Messages and Tool Binding

What it does:
    Demonstrates how to initialise a LangChain chat model, send a multi-turn
    conversation (including multi-modal content), and bind a tool for function
    calling.

How it works:
    1. Loads environment variables from a .env file.
    2. Initializes a Gemini 2.5 Flash Lite chat model with configurable
       temperature, max tokens, timeout, and retry settings.
    3. Constructs a conversation with a SystemMessage (persona), prior messages,
       and a multi-modal HumanMessage containing both text and an image URL.
    4. Invokes the model and prints the AI response.
    5. Defines a `get_weather` function, binds it as a tool to the model, then
       invokes the model with a weather query. The model returns a tool_call
       which is executed locally to retrieve the answer.

Expected outcome:
    - First invocation: prints the model's conversational reply (as a 5-year-old
      girl persona) to "What is LLM?" with image context.
    - Second invocation: prints the weather result for Sydney ("raining") by
      executing the tool call returned by the model.
"""

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage, SystemMessage

# Load variables from .env into the system environment
load_dotenv()

model = init_chat_model(
    # The name or identifier of the specific model you want to use with a provider. 
    model="google_genai:gemini-2.5-flash-lite",

    # Controls the randomness of the model’s output. A higher number makes responses 
    # more creative; lower ones make them more deterministic.
    temperature=0.5,

    # Limits the total number of tokens in the response, effectively controlling how 
    # long the output can be.
    max_tokens=1000,

    # The maximum time (in seconds) to wait for a response from the model before canceling 
    # the request.
    timeout=30,

    # The maximum number of attempts the system will make to resend a request if it fails 
    # due to issues like network timeouts or rate limits.
    max_retries=3
)

messages = [
    # An initial set of instructions that primes the model’s behavior
    SystemMessage("You are a 5 years old girl"),

    HumanMessage("Good morning~"),

    # The output of a model invocation
    AIMessage("How can I help you?"),

    # User input and interactions. They can contain text, images, audio, 
    # files, and any other amount of multi-modal content
    HumanMessage(
        content=[
            {"type": "text",  "text": "What is LLM?"},
            {"type": "image", "url":  "https://pixelplex.io/wp-content/uploads/2024/01/llm-applications-main.jpg"}
        ],

        # Optional: identify different users
        name="Alice",

        # Optional: unique identifier for tracing
        id="message_123"
    )
]

response = model.invoke(messages)
print(response)

def get_weather(location: str) -> str:

    weather = {
        "Sydney"   : "raining",
        "Canberra" : "sunny",
        "Melbourne": "cloudy"
    }

    return weather.get(location, "unknown")

model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("What is the weather in Sydney?")

for tool_call in response.tool_calls:
    print(globals()[tool_call['name']](tool_call['args']['location'])) 
