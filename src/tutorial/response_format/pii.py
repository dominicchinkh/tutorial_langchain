"""
LangChain Agent PII (Personally Identifiable Information) Protection and Redaction Demonstration.

What it does:
    This script demonstrates how to securely process user inputs containing sensitive data 
    by passing them through an automated privacy pipeline using LangChain `PIIMiddleware`. 
    
    It intercepts the user's raw message, scans for specific patterns of Personally Identifiable 
    Information (PII) - such as email addresses, credit cards, URLs, and IP addresses, and 
    sanitizes them using varying privacy strategies before the text ever reaches the LLM.

How it works:
    1. Middleware Chain Configuration: A lightweight agent (`gemini-2.5-flash-lite`) is wrapped with an 
       array of `PIIMiddleware` layers. Each layer executes a sequential transformation policy:
       - "email" & "url" -> 'redact': Completely replaces the data with a generic token placeholder.
       - "credit_card"   -> 'mask': Obfuscates characters (e.g., converting digits to asterisks or fixed formats).
       - "ip"            -> 'hash': Cryptographically hashes the value to maintain reference identity without exposure.
       - (Optional) "api_key" -> 'block': Uses a regex detector to halt execution entirely if triggered.
       
    3. Message Interception: The input prompt is fed into `agent.invoke()`. The middleware stack transforms 
       the contents *in-flight*, sending only sanitized text to the language model.
       
    4. Output Inspection: The response loop prints the underlying message objects, allowing verification 
       of the sanitized conversation history.

Expected outcome:
    - The script successfully sanitizes the sensitive user message before handing it to the model.
    
    - Printing the conversation state will show modified input text where:
        * "john.doe@example.com" becomes a token like `<REDACTED_EMAIL>`.
        * "5105-1051-0510-5100" appears masked like `****-****-****-5100`.
        * "https://example.com" is rewritten as a generic URL token like `[REDACTED_URL]`.
        * "127.0.0.1" is replaced with an cryptographic hash string (e.g. `<ip_hash:12ca17b4>`).
        
    - Because the API key blocking middleware is commented out, the mock API key passes through 
      unaltered unless captured by another rule. If uncommented, it throws a `PIIDetectionError`.
"""

from dotenv import load_dotenv

from langchain_core.utils.uuid import uuid7
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain.agents.middleware._redaction import PIIDetectionError

# Load variables from .env into the system environment
load_dotenv()

# Redact all emails in user input
agent = create_agent(
    model="google_genai:gemini-2.5-flash-lite",
    middleware=[
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("credit_card", strategy="mask"),
        PIIMiddleware("url", strategy="redact"),
        PIIMiddleware("ip", strategy="hash"),
        # PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block"), # throw PIIDetectionError
    ],
)

# When user provides PII, it will be handled according to the strategy
try:
    result = agent.invoke({
        "messages": [
            {
                "role": "user", 
                "content": 
                    "My email is john.doe@example.com and card is 5105-1051-0510-5100."
                    "Visit me at https://example.com. The IP address is 127.0.0.1."
                    "Use the API key sk-HMq2CNm2g1DSOWnU9We7oUEqc0SUc5EZ"
            }
        ]
    })
    
    for message in result["messages"]:
        print(message.pretty_print())

except PIIDetectionError:
    print("PIIDetectionError thrown")
