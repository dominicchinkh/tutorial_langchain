"""
Deep Agent Memory Injection and File Querying Demonstration.

This script demonstrates how to instantiate a stateful Deep Agent, inject external 
file data directly into its working memory context, and query the agent about 
the contents of those files within a specific conversation thread.

What it does:
    It downloads a markdown file (`AGENTS.md`) from a remote GitHub repository 
    and feeds it into a Gemini-powered agent's file system memory layer. It then 
    asks the agent to inspect its memory files and describe the contents of that 
    specific document.

How it does it:
    1. Remote Data Fetching: Uses standard library `urllib.request.urlopen` to 
       fetch the raw text of `AGENTS.md` asynchronously/synchronously from GitHub.
    2. Checkpointer State Management: Initializes a LangGraph `MemorySaver()` 
       to act as an in-memory checkpointer. This allows the agent to maintain 
       conversation state, history, and context across a specific `thread_id`.
    3. Agent Configuration: Uses `create_deep_agent` to assemble a 
       `gemini-2.5-flash-lite` model instance. It pre-registers `/AGENTS.md` 
       in its `memory` array configuration parameter, signaling that this file path 
       is bound to the agent's contextual workspace.
    4. Payload Execution & Virtual Filesystem: When `agent.invoke` is executed, 
       the script passes the raw text wrapped via `create_file_data(agents_md)` 
       under the matching payload key `"/AGENTS.md"`. This maps the local file data 
       directly into the agent's prompt/context window for that invocation thread.
    5. Threaded Isolation: Passes a `config` dictionary specifying `thread_id: "123456"`. 
       This tells the checkpointer to save this file memory state specifically 
       to this conversation thread.

Expected Outcome:
    The agent will read the provided file data from its context window and print 
    out a summary or structured description of the technical specifications or markdown 
    headers contained within the `AGENTS.md` file. The final output printed to the 
    console will be the model's textual analysis response payload.
"""

from urllib.request import urlopen

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

with urlopen(
    "https://raw.githubusercontent.com/langchain-ai/deepagents/refs/heads/main/examples/text-to-sql-agent/AGENTS.md"
) as response:
    agents_md = response.read().decode("utf-8")
    
checkpointer = MemorySaver()

model="google_genai:gemini-2.5-flash"

#---------------
# State backend

agent = create_deep_agent(
    model = model,
    memory=[
        "/AGENTS.md"
    ],
    checkpointer=checkpointer
)

#---------------
# Store backend

# store = InMemoryStore()
# file_data = create_file_data(agents_md)
# store.put(
#     namespace=("filesystem",),
#     key='/AGENTS.md',
#     value=file_data
# )

# agent = create_deep_agent(
#     model=model,
#     backend=StoreBackend(namespace=lambda _rt: ("filesystem",)),
#     store=store,
#     memory=["/AGENTS.md"],
# )

#---------------------
# File system backend

# agent = create_deep_agent(
#     model=model,
#     backend=FilesystemBackend(
#         root_dir="../skills/text-to-sql",
#         virtual_mode=True
#     ),
#     memory=[
#         "./AGENTS.md"
#     ],
#     interrupt_on={
#         "write_file": True,  # Default: approve, edit, reject
#         "read_file": False,  # No interrupts needed
#         "edit_file": True,   # Default: approve, edit, reject
#     },
#     checkpointer=checkpointer
# )
#
# result = agent.invoke(
#     {"messages": [{"role": "user", "content": "Please tell me what's the safety rules in your memory files."}]},
#     config={"configurable": {"thread_id": "12345"}},
# )

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Please tell me what's the safety rules in your memory files."
            }
        ],
        "files": {
            "/AGENTS.md": create_file_data(agents_md)
        }
    },
    config={
        "configurable": {
            "thread_id": "123456"
        }
    }
)

print(result)
