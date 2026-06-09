from langchain.messages import AIMessage, HumanMessage, ToolMessage

{
    "messages": [
        HumanMessage(
            content="Find out what year the Golden Gate Bridge opened by searching the web. Then, write a QuickJS script to calculate the 10th Fibonacci number and multiply it by that year.",
            additional_kwargs={},
            response_metadata={},
            id="1e6ac5b9-e9bb-47ae-8574-95779157194d",
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "search_web",
                    "arguments": '{"query": "what year did the golden gate bridge open"}',
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019eac0c-d495-7192-82eb-41a99a8b2ab1-0",
            tool_calls=[
                {
                    "name": "search_web",
                    "args": {"query": "what year did the golden gate bridge open"},
                    "id": "0a074e19-8a63-4320-abb0-ff976889e0bf",
                    "type": "tool_call",
                }
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6815,
                "output_tokens": 22,
                "total_tokens": 6837,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="The Golden Gate Bridge officially opened on May 27, 1937.",
            name="search_web",
            id="feb311ca-71f8-4f8a-8f50-1c42dda35d92",
            tool_call_id="0a074e19-8a63-4320-abb0-ff976889e0bf",
        ),
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "eval",
                    "arguments": '{"code": "let goldenGateBridgeYear = 1937;\\nlet a = 0, b = 1, temp;\\nfor (let i = 0; i < 9; i++) {\\n    temp = a + b;\\n    a = b;\\n    b = temp;\\n}\\nlet fibonacci10 = b;\\nconsole.log(fibonacci10 * goldenGateBridgeYear);"}',
                }
            },
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019eac0c-db55-7860-8c85-959b6115b5d1-0",
            tool_calls=[
                {
                    "name": "eval",
                    "args": {
                        "code": "let goldenGateBridgeYear = 1937;\nlet a = 0, b = 1, temp;\nfor (let i = 0; i < 9; i++) {\n    temp = a + b;\n    a = b;\n    b = temp;\n}\nlet fibonacci10 = b;\nconsole.log(fibonacci10 * goldenGateBridgeYear);"
                    },
                    "id": "5603a251-0de0-46cd-8cbe-05cb61ef73f2",
                    "type": "tool_call",
                }
            ],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 6869,
                "output_tokens": 101,
                "total_tokens": 6970,
                "input_token_details": {"cache_read": 0},
            },
        ),
        ToolMessage(
            content="<stdout>\n106535\n</stdout>\n<result>null</result>",
            name="eval",
            id="73cf123d-62e1-470a-8d83-7fb6ceea1231",
            tool_call_id="5603a251-0de0-46cd-8cbe-05cb61ef73f2",
        ),
        AIMessage(
            content="The Golden Gate Bridge opened in 1937. The 10th Fibonacci number is 55. When multiplied by the year, the result is 106535.",
            additional_kwargs={},
            response_metadata={
                "finish_reason": "STOP",
                "model_name": "gemini-2.5-flash-lite",
                "safety_ratings": [],
                "model_provider": "google_genai",
            },
            id="lc_run--019eac0c-e2e1-73e0-a158-1aeef266d831-0",
            tool_calls=[],
            invalid_tool_calls=[],
            usage_metadata={
                "input_tokens": 7004,
                "output_tokens": 41,
                "total_tokens": 7045,
                "input_token_details": {"cache_read": 0},
            },
        ),
    ],
    "files": {},
}
