from tools.db_tools import (
    verify_customer,
    get_order_details,
    list_customer_orders,
    search_products,
    check_return_eligibility,
    create_return_request,
    create_escalation
)

from database.db import log_tool_call


TOOLS = {
    "verify_customer": verify_customer,
    "get_order_details": get_order_details,
    "list_customer_orders": list_customer_orders,
    "search_products": search_products,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
    "create_escalation": create_escalation
}


def execute_tool(tool_name, arguments, conversation_id=None):

    if tool_name not in TOOLS:
        result = {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }

        if conversation_id:
            log_tool_call(
                conversation_id,
                tool_name,
                arguments,
                result,
                False
            )

        return result

    try:
        result = TOOLS[tool_name](**arguments)

        response = {
            "success": True,
            "result": result
        }

        if conversation_id:
            log_tool_call(
                conversation_id,
                tool_name,
                arguments,
                result,
                True
            )

        return response

    except Exception as e:

        response = {
            "success": False,
            "error": str(e)
        }

        if conversation_id:
            log_tool_call(
                conversation_id,
                tool_name,
                arguments,
                response,
                False
            )

        return response