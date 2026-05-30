"""
multi_agent.py — Multi-Agent Supervisor with Human-in-the-Loop

What it does:
    Demonstrates a supervisor pattern where a top-level agent orchestrates two
    specialized sub-agents (calendar and email) to fulfil complex multi-step
    user requests, with human approval required before executing sensitive
    actions.

How it works:
    1. Defines shared tools: `create_calendar_event`, `send_email`,
       `get_available_time_slots`, and `get_current_and_relative_date`.
    2. Creates a Calendar Agent that parses natural-language scheduling requests
       into ISO datetimes, checks availability, and creates events.
    3. Creates an Email Agent that composes and sends professional emails based
       on natural-language instructions.
    4. Wraps each sub-agent as a tool (`schedule_event`, `manage_email`) so the
       supervisor can invoke them.
    5. Creates a Supervisor Agent that breaks down user requests and delegates
       to the appropriate sub-agent tools.
    6. Uses `HumanInTheLoopMiddleware` to pause execution before creating
       calendar events or sending emails, allowing the user to approve, edit,
       or reject each action.
    7. Streams the supervisor's execution, collects human decisions (approve or
       edit), then resumes execution with a `Command(resume=...)`.

Expected outcome:
    The supervisor schedules a meeting via the calendar agent and sends a
    details email via the email agent. Both actions are paused for human
    review — the calendar event is approved as-is, while the email subject is
    edited before sending. Final confirmation messages are printed to stdout.
"""

import pprint
import uuid

from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command 

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

config = {
    "configurable": {
        "thread_id": str(uuid.uuid4())
    }
}
    
@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,          
    attendees: list[str],   # email addresses
    localtion: str = ""
) -> str:
    """Create a calendar event. Required exact ISO datetime format"""
    
    # This would call Google Calendar API, Outlook API, etc
    return f"Event created: {title} from {start_time} to {end_time} with {len(attendees)} attendees"

@tool
def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] = []
) -> str:
    """Send an email via email API. Required properly formatted addresses"""
    
    # This would call SendGrid, Gmail API, etc
    return f"Email sent to {', '.join(to)} - Subject: {subject}"

@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,
    duration_minute: int
) -> str:
    """Check calendar availability for given attendees on a specific date"""
    
    # This would query calendar APIs
    return ["09:00", "14:00", "16:00"]

@tool
def get_current_and_relative_date() -> str:
    """
    Returns the current date and day of the week. 
    
    Use this tool whenever the user asks for the current date, 
    or asks for relative dates like 'next Tuesday', 'tomorrow', 
    or 'last week' so you can compute the exact calendar day.
    """
    now = datetime.now()
    current_date_str = now.strftime("%Y-%m-%d")
    day_of_week = now.strftime("%A")
    
    return f"Today's date is {current_date_str} and the day of the week is {day_of_week}."

#-----------------------------------------------------------------------------------------
# The calendar agent understands natural language scheduling requests and translates them 
# into precise API calls. It handles date parsing, availability checking, and event creation.
CALENDAR_AGENT_PROMPT = (
    "You are a calendar scheduling assistant. "
    "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
    "into proper ISO datetime formats. "
    "Use get_available_time_slots to check availability when needed. "
    "If there is no suitable time slot, stop and confirm unavailability in your response. "
    "Use create_calendar_event to schedule events. "
    "Use get_current_and_relative_date to get the current or relative date. "
    "Always confirm what was scheduled in your final response."
)

calendar_agent = create_agent(
    model,
    tools = [get_current_and_relative_date, create_calendar_event, get_available_time_slots],
    system_prompt = CALENDAR_AGENT_PROMPT,
    middleware = [
        # Permit all response types (approve, edit, reject)
        HumanInTheLoopMiddleware(
            interrupt_on = {"create_calendar_event": True},
            description_prefix = "Calendar event pending approval" 
        )
    ]
)

query = """
    Schedule a team meeting next Tuesday at 2pm for 1 hour.
    Attendees are a@gmail.com and b@hotmail.com.
"""

# for step in calendar_agent.stream({"messages": [{"role": "user", "content": query}]}, config):
#     for update in step.values():
#         if update is not None:
#             if isinstance(update, tuple):
#                 for message in update:
#                     pprint.pprint(message)
#             else:
#                 for message in update.get("messages", []):
#                     message.pretty_print()

#-------------------------------------------------------------------------------------------- 
# The email agent handles message composition and sending. It focuses on extracting recipient
# information, crafting appropriate subject lines and body text, and managing email 
# communication.

EMAIL_AGENT_PROMPT = (
    "You are an email assistant. "
    "Compose professional emails based on natural language requests. "
    "Extract recipient information and craft appropriate subject lines and body text. "
    "Use get_current_and_relative_date to get the exact date. "
    "Use send_email to send the message. "
    "Always confirm what was sent in your final response."
)

email_agent = create_agent(
    model,
    tools = [get_current_and_relative_date, send_email],
    system_prompt = EMAIL_AGENT_PROMPT,
    middleware = [
        # Permit all response types (approve, edit, reject)
        HumanInTheLoopMiddleware(
            interrupt_on = {"send_email": True},
            description_prefix = "Outbound email pending approval" 
        )
    ]
)

query = """
    Send the design team a reminder about reviewing the new mockups now.
    Design team email address is c@outlook.com.
    The due date is next wednesday 1pm.
    Check the date.
    Mock the subject.
"""

# for step in calendar_agent.stream({"messages": [{"role": "user", "content": query}]}, config):
#     for update in step.values():
#         if update is not None:
#             if isinstance(update, tuple):
#                 for message in update:
#                     pprint.pprint(message)
#             else:
#                 for message in update.get("messages", []):
#                     message.pretty_print()

#-------------------------------------------------------------
# Wrap each sub-agent as a tool that the supervisor can invoke

# The tool descriptions help the supervisor decide when to use each tool, so make them clear
# and specific. We return only the sub-agent’s final response, as the supervisor doesn’t need
# to see intermediate reasoning or tool calls.

@tool
def schedule_event(
    request: str,
    runtime: ToolRuntime
) -> str:
    """Schedule calendar events using natural language.

        Use this when the user wants to create, modify, or check calendar appointments.
        Handles date/time parsing, availability checking, and event creation.

        Input: Natural language scheduling request (e.g., 'meeting with design team
        next Tuesday at 2pm')
    """
    
    # Pass additional conversational context to sub-agents
    original_user_message = next(
        message for message in runtime.state["messages"] if message.type == "human"
    )
    
    prompt = (
        "You are assisting with the following user inquiry:"
        f"{original_user_message.text}"
        "You are tasked with the following sub-request:"
        f"{request}"
    )
    
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })
    return result["messages"][-1].text


@tool
def manage_email(request: str) -> str:
    """Send emails using natural language.

        Use this when the user wants to send notifications, reminders, or any email
        communication. Handles recipient extraction, subject generation, and email
        composition.

        Input: Natural language email request (e.g., 'send them a reminder about
        the meeting')
    """
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

#------------------------------------------------------------
# Now create the supervisor that orchestrates the sub-agents

SUPERVISOR_PROMPT = (
    "You are a helpful personal assistant. "
    "You can schedule calendar events and send emails. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

supervisor_agent = create_agent(
    model,
    tools = [schedule_event, manage_email],
    system_prompt = SUPERVISOR_PROMPT,
    checkpointer = InMemorySaver() # This is required to pause and resume execution.
)

query = """
    Schedule a team standup for next Tuesday 9am for 1 hour.
    Attendees are a@gmail.com, b@hotmail.com.
    Send meeting details email to attendees.
    Mock the email subject and body.
"""

resume = {}

for step in supervisor_agent.stream({"messages":[{"role": "user", "content": query}]}, config):
    for update in step.values():
        if update is not None:
            if isinstance(update, tuple):
                for message in update:
                    for request in message.value["action_requests"]:
                        print("------------------------------------")
                        print(f"{message.id}\n")
                        print(f"{request['description']}\n")

                        # Specify decisions for each interrupt by referring to its ID using a `Command`
                        if request['name'] == 'send_email':
                            edited_action = request.copy()
                            edited_action['args']['subject'] = 'Edited: ' + edited_action['args']['subject']
                            
                            resume[message.id] = {
                                "decisions": [{
                                    "type": "edit",
                                    "edited_action": edited_action
                                }]
                            }
                        else:
                            resume[message.id] = {"decisions": [{"type": "approve"}]}
                        
            else:
                for message in update.get("messages", []):
                    message.pretty_print()

#------------------------------
# Add human-in-the-loop-review

for step in supervisor_agent.stream(
    Command(resume=resume),
    config,
):
    for update in step.values():
        if update is not None:
            if isinstance(update, tuple):
                for message in update:
                    pprint.pprint(message)
            else:
                for message in update.get("messages", []):
                    message.pretty_print()
