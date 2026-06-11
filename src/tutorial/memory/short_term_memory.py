"""
LangGraph Agent with Dynamic State Management and Memory Summarization.

What it does:
    This script initializes an autonomous agent configured with permanent thread
    checkpointing (`InMemorySaver`), state-bound variables (`CustomAgentState`), 
    and automated window summarization. The agent is designed to dynamically capture 
    the user's name during natural conversation, save it out-of-band inside the 
    graph checkpoint state via tool calls, and automatically enforce a structural 
    linguistic constraint requiring the model to address the user by name once 
    it has been captured.

How it works:
    1. State Management: Extends the baseline `AgentState` into a `CustomAgentState` 
       containing an explicit `user_name` string property. This property is tracked 
       and persisted across individual graph invocations using the `InMemorySaver` 
       keyed to a specific `thread_id`.
    
    2. State Interception (Dynamic Prompting): Registers a `@dynamic_prompt` 
       interceptor (`dynamic_system_prompt`) inside the agent's middleware chain. 
       On every inference pass, it inspects the state schema. If a `user_name` exists, 
       it modifies the system instruction set in real-time to append a strict directive: 
       "You must address the user as [Name] at least once in every response."
    
    3. Context Truncation & Compression: Utilizes LangChain's `SummarizationMiddleware`. 
       When the conversation history reaches 5 messages, the oldest messages are 
       automatically compressed by a background LLM process into a single Markdown-structured 
       summary block (`## SUMMARY`), prepended as a `HumanMessage` at index 0. 
       The raw history window is safely managed via a `keep=10` history buffer.

EXPECTED OUTCOME:
    - Turn 1: The user introduces themselves ("Hi! my name is Bob."). The agent detects 
      this, triggers the `update_user_name` tool, updates the state, and responds normally.
      
    - Turn 2 & 3: The user shifts topics (asking for poems about cats/dogs). The message 
      counter crosses 5, triggering summarization. Bob's name is saved inside the text summary 
      markdown block while raw old turns are cleaned.
      
    - Turn 4 & 5: The user asks "What is my name?". Despite the original introduction 
      being truncated out of the immediate message buffer, the agent reads its active 
      state context and the text summary, responding confidently with "Bob".
      
    - Output Profile: The final history log contains a structured summary `HumanMessage` 
      at the top and a series of balanced conversational text turns.
    
"""
import inspect

from dotenv import load_dotenv
from langchain_core.utils.uuid import uuid7
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model, before_model, dynamic_prompt, ModelRequest, SummarizationMiddleware
from langchain.messages import RemoveMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime
from langgraph.types import Command
# from langgraph.checkpoint.postgres import PostgresSaver 

load_dotenv()

@tool
def get_user_name(
    runtime: ToolRuntime
) -> str:
    """Look up user info."""
    user_name = runtime.state.get("user_name", None)
    return f"User name is {user_name}" if user_name is not None else "Unknown user"

# AI will still occasionally fail to update the name

# 1. LLMs suffer from "loss in the middle"- when your history grows toward 10 messages, instructions
#    buried deep in the middle of a system prompt or an early message block get ignored.
# 2. If the model's primary focus is answering the user's immediate question (like writing a cat 
#    poem), it will de-prioritize the background task of parsing the markdown summary block to 
#    check for a missing state sync.

@tool
def update_user_name(
    user_name: str,
    runtime: ToolRuntime
) -> Command: 
    """Update user name."""
    
    print(f"Successfully updated user name to {user_name}")
    
    return Command(
        update={
            "user_name": user_name,
            "messages": [
                ToolMessage(
                    f"Successfully updated user name to {user_name}",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )

#----------------
# Dynamic prompt

@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    if "user_name" in request.state:
        return f"You must address the user as {request.state['user_name']} at least once in every response."
    else:
        return ""

#--------------------------
# Customizing agent memory

class CustomAgentState(AgentState):
    user_name: str
    preferences: dict

#--------------------------
# Trim messages

@before_model
def trim_messages(state: CustomAgentState, runtime: Runtime) -> dict[str, any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]
    
    if len(messages) <= 3:
        return None
    
    first_message = messages[0]
    recent_messages = messages[-2:]
    new_messages = [first_message] + recent_messages

    return {
        "messages": [
            
            # To remove specific message
            # RemoveMessage(id=m.id) for m in messages[:2]

            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
        
        # I do not have to manually set user_name and preferences inside `trim_messages` modifier
        # function unless I am intentionally trying to change their values
        
        # When an agent modifier (like @before_model or a tool) returns a dictionary, LangGraph 
        # treats it as a partial update (a patch)
        #   * If I return {"messages": [...]}, LangGraph updates only the messages key
        #   * It automatically preserves the existing user_name and preferences in the background
    }

#--------------------------
# Delete messages

@after_model
def delete_old_messages(state: CustomAgentState, runtime:Runtime) -> dict[str, any] | None:
    """Remove old messages to keep conversation manageable."""
    messages = state["messages"]
    
    if len(messages) > 2:
        
        print("Remove the earliest two messages")
        
        # remove the earliest two messages
        return {
            "messages": [
                RemoveMessage(id=m.id) for m in messages[:2]
            ]
        }
    
    return None

@after_model
def print_last_messages(state: CustomAgentState, runtime:Runtime) -> None:
    """Print last message"""
    message = state["messages"][-1]
    message.pretty_print()
    
    return None

model = "google_genai:gemini-2.5-flash-lite"

# System prompt that tells the model how to read its own summary
base_prompt = inspect.cleandoc("""
    You are a helpful assistant. 
    
    1. Listen closely for when the user introduces themselves (e.g., "Hi, I'm Bob", "My name 
       is Alice", "Call me Jack").
    2. As soon as a name is provided, immediately call the tool `update_user_name` using the 
       extracted name as the argument.
    3. You have a summarization middleware active. If the conversation history gets too long, 
       the oldest messages are compressed into a "summary" text block inside a HumanMessage 
       at the very beginning of the chat log. 
    4. Always read the '## SUMMARY' section of that message carefully. It contains context 
       from deleted turns, including user names or preferences.
""")

agent = create_agent(
    model=model,
    system_prompt=base_prompt,
    tools=[update_user_name],
    # middleware=[delete_old_messages],
    # middleware=[trim_messages],
    middleware = [
        dynamic_system_prompt,
        SummarizationMiddleware(
            model=model,
            trigger=(
                # Trigger summarization when 5 messages is reached
                ("messages", 5)

                # Trigger summarization when 3000 tokens is reached
                # ("tokens", 200)

                # Trigger summarization either when 80% of model's max input tokens
                # is reached or when 5 messages is reached (whichever comes first)
                # [("fraction", 0.8), ("messages", 5)]
            ),
            
            # Make sure that the `keep` is more than the `trigger`
            #   Otherwise if `keep`` was equal to `trigger``, it left the summarization logic with a 
            #   zero-buffer window. To squeeze everything into exactly 4 messages, it had to slice deep 
            #   into the conversation, entirely wiping out the first turn (where Bob introduced himself)
            #   before the model could even capture the name "Bob" in the text summary.
            keep=("messages", 10)
        )
    ],
    # The line `checkpointer=InMemorySaver()` is setting up a checkpointer for the agent using an
    # `InMemorySaver`.
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver()
)

#---------------------------------------------------------
# In production, use a checkpointer backed by a database:
#
# DB_URI = "postgresql://postgres:password@localhost:5432/postgres?sslmode=disable"
#
# with PostgresSaver.from_conn_string(DB_URI) as check_pointer:
#     check_pointer.setup() 
#
#     agent = create_agent(
#         model=model,
#         tools=[get_user_info],
#         checkpointer=check_pointer,
#     )
#
#---------------------------------------------------------

thread_config = {
    "configurable": {
        "thread_id": str(uuid7())
    }
}

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            # "My name is Bob" does not work
            "content": "Hi! my name is Bob."
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            "content": "Write a short poem about cats"
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            "content": "Now do the same but for dogs"
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            "content": inspect.cleandoc("""
                While sitting on a riverbank, Alice spots a talking White Rabbit in a waistcoat.
                Following her curiosity, she tumbles down a rabbit hole into "Wonderland". There,
                she navigates a bizarre, shifting landscape where she constantly changes size. 
                She encounters a variety of eccentric characters, including the mysterious 
                Cheshire Cat, the hookah-smoking Caterpillar, and the tyrannical Queen of Hearts.
                Her journey culminates in a nonsensical trial before she suddenly wakes up on 
                the riverbank, realizing her bizarre adventure was just a dream.
            """)
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            "content": "What is my name?"
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

response = agent.invoke(
    input={
        "messages":[{
            "role": "user",
            "content": "Bye!"
        }],
        "preferences": {"theme": "dark"}
    },
    config=thread_config
)

# Fetch the final snapshot of the conversation state
final_state = agent.get_state(thread_config)

print("\n=== Inspecting Message History ===")
for msg in final_state.values.get("messages", []):
    # Print the class name and a preview of the content
    print(f"[{type(msg).__name__}]: {repr(msg.content)}")
