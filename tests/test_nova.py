from tools.db_tools import (
    search_products,
    get_order_details,
    verify_customer,
    check_return_eligibility,
    create_return_request
)

from tools.tool_registry import execute_tool


print("\n==============================")
print(" NOVA-ASSIST SYSTEM TEST")
print("==============================\n")


# 1. PRODUCT SEARCH
print("TEST 1: Product Search")

products = search_products("Laptop")

assert isinstance(products, list)

print("PASS ✅")


# 2. ORDER DETAILS
print("\nTEST 2: Order Details")

order = get_order_details(1)

assert order["found"] is True
assert "order" in order
assert "items" in order

print("PASS ✅")


# 3. INVALID ORDER
print("\nTEST 3: Invalid Order")

order = get_order_details(99999)

assert order["found"] is False

print("PASS ✅")


# 4. CUSTOMER VERIFICATION
print("\nTEST 4: Customer Verification")

valid = verify_customer(
    1,
    email="wrong@example.com",
    phone_last4="0000"
)

assert valid["verified"] is False

print("PASS ✅")


# 5. TOOL ROUTER
print("\nTEST 5: Tool Router")

result = execute_tool(
    "search_products",
    {
        "search_term": "Laptop"
    }
)

assert result["success"] is True
assert "result" in result

print("PASS ✅")


# 6. UNKNOWN TOOL
print("\nTEST 6: Unknown Tool Protection")

result = execute_tool(
    "delete_database",
    {}
)

assert result["success"] is False

print("PASS ✅")


# 7. RETURN ELIGIBILITY
print("\nTEST 7: Return Eligibility")

result = check_return_eligibility(1)

assert "eligible" in result

print("PASS ✅")


print("\n==============================")
print(" ALL TESTS PASSED 🎉")
print("==============================\n")