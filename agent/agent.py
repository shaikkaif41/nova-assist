import os
import json

from dotenv import load_dotenv
from groq import Groq

from database.db import (
    create_conversation,
    save_message,
    get_conversation_messages,
    get_verification_state
)

from tools.tool_registry import execute_tool


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


SYSTEM_PROMPT = """
You are NOVA-ASSIST, an AI customer support agent for NovaMart.

You help customers with:
- Orders
- Products
- Returns
- Human escalation

RULES:

1. Never invent database information.
2. Never generate SQL.
3. Product searches do not require verification.
4. Order-specific information ALWAYS requires verification.
5. Verification requires order ID plus email OR phone last four digits.
6. Never reveal whether an order exists when verification fails.
7. Never expose full phone numbers or sensitive information.
8. Return requests require eligibility checking first.
9. If verification fails three times, escalate to human support.
10. Keep responses under 120 words.
"""


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "verify_customer",
            "description": "Verify customer using order ID and email or phone last four digits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "email": {"type": "string"},
                    "phone_last4": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get details about a verified order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_customer_orders",
            "description": "List orders belonging to a verified customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "integer"}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products by name, category, or description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string"}
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Check whether an order is eligible for return.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_return_request",
            "description": "Create a return request after eligibility is confirmed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "reason": {"type": "string"}
                },
                "required": ["order_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_escalation",
            "description": "Escalate a conversation to human support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "integer"},
                    "reason": {"type": "string"}
                },
                "required": ["conversation_id", "reason"]
            }
        }
    }
]


PROTECTED_TOOLS = {
    "get_order_details",
    "list_customer_orders",
    "check_return_eligibility",
    "create_return_request"
}


def chat(user_message, conversation_id=None):

    if conversation_id is None:
        conversation_id = create_conversation()

    save_message(
        conversation_id,
        "USER",
        user_message
    )

    history = get_conversation_messages(
        conversation_id
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for item in history:

        if item["role"] in ["user", "assistant"]:
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })

    state = get_verification_state(
        conversation_id
    )

    verified = state["verified"]
    verified_customer_id = state["customer_id"]
    verified_order_id = state["verified_order_id"]
    verification_failures = state["verification_failures"]

    for _ in range(6):

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.2
        )

        message = response.choices[0].message

        if not message.tool_calls:

            answer = message.content or "How can I help you?"

            save_message(
                conversation_id,
                "ASSISTANT",
                answer
            )

            return {
                "conversation_id": conversation_id,
                "response": answer
            }

        messages.append(message)

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            if tool_name == "verify_customer":

                result = execute_tool(
                    tool_name,
                    arguments,
                    conversation_id
                )

                verification = result.get(
                    "result",
                    {}
                )

                if verification.get("verified"):

                    verified = True

                    verified_customer_id = (
                        verification.get("customer_id")
                    )

                    verified_order_id = (
                        arguments.get("order_id")
                    )

                    verification_failures = 0

                else:

                    verification_failures += 1

                    if verification_failures >= 3:

                        escalation = execute_tool(
                            "create_escalation",
                            {
                                "conversation_id": conversation_id,
                                "reason": "Three failed customer verification attempts."
                            },
                            conversation_id
                        )

                        result = {
                            "success": False,
                            "escalated": True,
                            "message": (
                                "Verification failed three times. "
                                "The conversation has been escalated."
                            ),
                            "escalation": escalation
                        }

            elif tool_name in PROTECTED_TOOLS:

                requested_order_id = arguments.get(
                    "order_id"
                )

                if not verified:

                    result = {
                        "success": False,
                        "error": "Customer verification required."
                    }

                elif tool_name != "list_customer_orders" and (
                    requested_order_id != verified_order_id
                ):

                    result = {
                        "success": False,
                        "error": "Customer verification required for this order."
                    }

                elif tool_name == "list_customer_orders":

                    result = execute_tool(
                        tool_name,
                        {
                            "customer_id": verified_customer_id
                        },
                        conversation_id
                    )

                else:

                    result = execute_tool(
                        tool_name,
                        arguments,
                        conversation_id
                    )

            else:

                result = execute_tool(
                    tool_name,
                    arguments,
                    conversation_id
                )

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

    answer = "I’m unable to safely complete this request right now."

    save_message(
        conversation_id,
        "ASSISTANT",
        answer
    )

    return {
        "conversation_id": conversation_id,
        "response": answer
    }