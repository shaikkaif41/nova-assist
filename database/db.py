import sqlite3
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nova_assist.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_conversation(customer_id=None):
    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO conversations
        (customer_id, started_at)
        VALUES (?, ?)
        """,
        (customer_id, datetime.now().isoformat())
    )

    conn.commit()
    conversation_id = cursor.lastrowid
    conn.close()

    return conversation_id


def save_message(conversation_id, role, content):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO messages
        (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_conversation_messages(conversation_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY message_id
        """,
        (conversation_id,)
    ).fetchall()

    conn.close()

    return [
        {
            "role": row["role"].lower(),
            "content": row["content"]
        }
        for row in rows
    ]


def log_tool_call(
    conversation_id,
    tool_name,
    input_data,
    output_data,
    success=True
):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO tool_call_log
        (
            conversation_id,
            tool_name,
            input_data,
            output_data,
            success,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            conversation_id,
            tool_name,
            json.dumps(input_data),
            json.dumps(output_data),
            int(success),
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_verification_state(conversation_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            input_data,
            output_data
        FROM tool_call_log
        WHERE conversation_id = ?
        AND tool_name = 'verify_customer'
        ORDER BY tool_call_id
        """,
        (conversation_id,)
    ).fetchall()

    conn.close()

    failures = 0
    verified = False
    customer_id = None
    verified_order_id = None

    for row in rows:
        try:
            inputs = json.loads(row["input_data"])
            output = json.loads(row["output_data"])
        except Exception:
            continue

        if output.get("verified") is True:
            verified = True
            customer_id = output.get("customer_id")
            verified_order_id = inputs.get("order_id")
            failures = 0
        else:
            failures += 1

    return {
        "verified": verified,
        "customer_id": customer_id,
        "verified_order_id": verified_order_id,
        "verification_failures": failures
    }