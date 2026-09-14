from database.db import get_connection


def verify_customer(order_id, email=None, phone_last4=None):
    conn = get_connection()

    query = """
        SELECT c.customer_id, c.full_name, c.email
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_id = ?
          AND (
              c.email = ?
              OR substr(c.phone, -4) = ?
          )
    """

    row = conn.execute(
        query,
        (order_id, email, phone_last4)
    ).fetchone()

    conn.close()

    if not row:
        return {
            "verified": False,
            "message": "Identity verification failed."
        }

    return {
        "verified": True,
        "customer_id": row["customer_id"],
        "name": row["full_name"]
    }


def get_order_details(order_id):
    conn = get_connection()

    query = """
        SELECT
            o.order_id,
            o.order_date,
            o.status,
            o.total_amount,
            o.expected_delivery,
            o.delivered_on,
            o.courier_name,
            o.tracking_ref,
            o.shipping_city
        FROM orders o
        WHERE o.order_id = ?
    """

    order = conn.execute(query, (order_id,)).fetchone()

    if not order:
        conn.close()
        return {"found": False}

    items_query = """
        SELECT
            p.name,
            p.category,
            oi.quantity,
            oi.unit_price
        FROM order_items oi
        JOIN products p
            ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """

    items = conn.execute(
        items_query,
        (order_id,)
    ).fetchall()

    conn.close()

    return {
        "found": True,
        "order": dict(order),
        "items": [dict(item) for item in items]
    }


def list_customer_orders(customer_id):
    conn = get_connection()

    query = """
        SELECT
            order_id,
            order_date,
            status,
            total_amount,
            expected_delivery
        FROM orders
        WHERE customer_id = ?
        ORDER BY order_date DESC
    """

    rows = conn.execute(
        query,
        (customer_id,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def search_products(search_term):
    conn = get_connection()

    query = """
        SELECT
            product_id,
            name,
            category,
            description,
            price,
            stock_quantity,
            is_returnable
        FROM products
        WHERE LOWER(name) LIKE LOWER(?)
           OR LOWER(category) LIKE LOWER(?)
           OR LOWER(description) LIKE LOWER(?)
        ORDER BY name
    """

    pattern = f"%{search_term}%"

    rows = conn.execute(
        query,
        (pattern, pattern, pattern)
    ).fetchall()

    conn.close()

    results = []

    for row in rows:
        product = dict(row)

        if product["stock_quantity"] == 0:
            product["stock_band"] = "Out of stock"
        elif product["stock_quantity"] <= 5:
            product["stock_band"] = "Low stock"
        else:
            product["stock_band"] = "In stock"

        results.append(product)

    return results


def check_return_eligibility(order_id):
    conn = get_connection()

    query = """
        SELECT
            o.order_id,
            o.status,
            o.delivered_on,
            p.product_id,
            p.name,
            p.is_returnable
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        JOIN products p
            ON oi.product_id = p.product_id
        WHERE o.order_id = ?
    """

    rows = conn.execute(
        query,
        (order_id,)
    ).fetchall()

    conn.close()

    if not rows:
        return {
            "eligible": False,
            "reason": "Order not found."
        }

    order = rows[0]

    if order["status"] != "DELIVERED":
        return {
            "eligible": False,
            "reason": "Order has not been delivered."
        }

    if not all(row["is_returnable"] for row in rows):
        return {
            "eligible": False,
            "reason": "One or more products are not returnable."
        }

    return {
        "eligible": True,
        "order_id": order_id,
        "products": [
            row["name"]
            for row in rows
        ]
    }


def create_return_request(order_id, reason):
    eligibility = check_return_eligibility(order_id)

    if not eligibility["eligible"]:
        return {
            "created": False,
            "reason": eligibility["reason"]
        }

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT return_id
        FROM return_requests
        WHERE order_id = ?
        AND status NOT IN ('REJECTED', 'COMPLETED')
        """,
        (order_id,)
    ).fetchone()

    if existing:
        conn.close()

        return {
            "created": False,
            "reason": "An active return request already exists."
        }

    from datetime import datetime

    cursor = conn.execute(
        """
        INSERT INTO return_requests
        (order_id, reason, status, requested_at, resolution_note)
        VALUES (?, ?, 'REQUESTED', ?, NULL)
        """,
        (
            order_id,
            reason,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    return_id = cursor.lastrowid

    conn.close()

    return {
        "created": True,
        "return_id": return_id,
        "status": "REQUESTED"
    }


def create_escalation(conversation_id, reason):
    from datetime import datetime

    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO escalations
        (conversation_id, reason, status, created_at)
        VALUES (?, ?, 'OPEN', ?)
        """,
        (
            conversation_id,
            reason,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    escalation_id = cursor.lastrowid

    conn.close()

    return {
        "created": True,
        "escalation_id": escalation_id,
        "status": "OPEN"
    }