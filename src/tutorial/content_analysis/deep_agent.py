"""
deep_agent.py — Deep Agent with URL Fetching and Memory

What it does:
    Creates a "deep agent" (multi-step, tool-using agent with sub-agent
    capabilities) that can fetch text from a URL, analyse the content, and
    answer structured questions about it.

How it works:
    1. Defines a `fetch_text_from_url` tool that downloads a document from a
       given URL and returns its text (truncated to 10,000 characters if too
       large).
    2. Configures a Gemini model and sets up an InMemorySaver checkpointer for
       conversation memory.
    3. Creates both a standard LangChain agent and a deep agent with the same
       tool and system prompt.
    4. Invokes the deep agent with a prompt that asks it to fetch a test file,
       count lines matching a substring, find the first occurrence of another
       substring, and produce a synopsis.
    5. Uses a unique thread_id per run (via uuid7) so memory does not carry over
       between executions.

Expected outcome:
    The agent fetches the remote text file, analyses its content using the tool
    results, and prints a structured answer with line counts, line numbers, and
    a two-sentence synopsis. If verification is not possible, it returns null
    for that field with an explanation.
"""

import urllib.error
import urllib.request

from deepagents import create_deep_agent
from langchain_core.utils.uuid import uuid7
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.tool import ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

#--------------------------------------------------------------------------------
# The system prompt defines your agent’s role and behavior. Keep it specific and 
# actionable

SYSTEM_PROMPT = """
    You are a literary data assistant.

    ## Capabilities
    - `fetch_text_from_url`: loads document text from a URL into the conversation.
    Do not guess line counts or positions—ground them in tool results from the saved file.
"""

#-----------------------------------------------------------------------------------
# Tools let a model interact with external systems by calling functions you define.

# Tools should be well-documented: their name, description, and argument names become 
# part of the model’s prompt.

@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"

    text = raw.decode("utf-8", errors="replace")
    if len(text) > 10000:
        text = text[:10000] + "\n\n[TRUNCATED - file too large]"
    return text


#----------------------
# Configure your model

print(f"Configure the model")
model = init_chat_model(
    "gemini-3.1-pro-preview",
    model_provider="google-genai",
    temperature=0.5,
    timeout=600,
    max_tokens=25000,
    streaming=True,
)

#------------
# Add memory

print(f"Add memory")
checkpointer = InMemorySaver()

#--------------------------
# Create and run the agent

# Add memory to your agent to maintain state across interactions. This allows the agent 
# to remember previous conversations and context.
model = "google_genai:gemini-2.5-flash"

print(f"Create agent")
agent = create_agent(
    model=model,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer
)

print(f"Create deep agent")
agent = create_deep_agent(
    model=model,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer
)

content = f"""
TXT test file
URL: https://example-files.online-convert.com/document/txt/example.txt

Answer as much as you can:

1) How many lines in the TXT test file contain the substring `Doe` (count 
   lines, not occurrences within a line, each line ends with a line break).
2) The 1-based line number of the first line in the file that contains `John Smith`.
3) A two-sentence neutral synopsis.

Do your best on (1) and (2). If at any point you realize you cannot **verify** an exact 
answer with your available tools and reasoning, do not fabricate numbers: use `null` for 
that field and spell out the limitation in `how_you_computed_counts`. If you encounter 
any errors please report what the error was and what the error message was.
"""

def print_result(agent_result: str) -> None:
    """Print the agent invoke result
    """
    for message in agent_result['messages']:
        print('-----------------------------------------------------------------------------')
        print(type(message))
        print('-----------------------------------------------------------------------------')
        
        if isinstance(message, HumanMessage):
            print(message.content)
            
        elif isinstance(message, AIMessage):
            if message.content:
                for content in message.content: 
                    if content['type']:
                        print("Type: " + str(content['type']) + "\n")

                    if content['text']:
                        print("Text: " + str(content['text']) + "\n")
                    
            if message.tool_calls:
                for tool in message.tool_calls:
                    print("Tool: " + str(tool) + "\n")

            if message.invalid_tool_calls:
                for tool in message.invalid_tool_calls:
                    print("Invalid Tool: " + str(tool) + "\n")
                
            if message.response_metadata:
                print("Response metadata: " + str(message.response_metadata) + "\n")
            
            if message.usage_metadata:
                print("Usage metadata: " + str(message.usage_metadata) + "\n")
                
        elif isinstance(message, ToolMessage):
            if message.name:
                print(f"Name: {message.name}\n")
                
            print(message.content)

print(f"Invoke agent")
agent_result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    },
    config = {
        "configurable": {
            "thread_id": str(uuid7())
        }
    }
)

print(f"Result available")
print_result(agent_result)

# print("\n")

# print(f"Invoke deep agent")
# deep_agent_result = agent.invoke(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": content
#             }
#         ]
#     },
#     config = {
#         "configurable": {
#             "thread_id": str(uuid7())
#         }
#     }
# )

# print(f"Result available")
# print_result(deep_agent_result)
