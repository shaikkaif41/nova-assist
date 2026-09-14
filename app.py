from flask import Flask, render_template, request, jsonify
from agent.agent import chat
from database.db import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():

    try:
        data = request.get_json() or {}

        message = data.get("message", "").strip()
        conversation_id = data.get("conversation_id")

        if not message:
            return jsonify({
                "error": "Message cannot be empty."
            }), 400

        result = chat(
            message,
            conversation_id
        )

        return jsonify(result)

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify({
            "error": "Something went wrong while processing your request."
        }), 500


@app.route("/api/conversations")
def conversations():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            c.conversation_id,
            c.customer_id,
            c.started_at,
            c.ended_at,
            COUNT(m.message_id) AS message_count
        FROM conversations c
        LEFT JOIN messages m
            ON c.conversation_id = m.conversation_id
        GROUP BY c.conversation_id
        ORDER BY c.conversation_id DESC
        """
    ).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.route("/api/conversations/<int:conversation_id>")
def conversation_details(conversation_id):

    conn = get_connection()

    messages = conn.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY message_id
        """,
        (conversation_id,)
    ).fetchall()

    tools = conn.execute(
        """
        SELECT
            tool_name,
            input_data,
            output_data,
            success,
            created_at
        FROM tool_call_log
        WHERE conversation_id = ?
        ORDER BY tool_call_id
        """,
        (conversation_id,)
    ).fetchall()

    escalations = conn.execute(
        """
        SELECT
            escalation_id,
            reason,
            status,
            created_at
        FROM escalations
        WHERE conversation_id = ?
        ORDER BY escalation_id
        """,
        (conversation_id,)
    ).fetchall()

    conn.close()

    return jsonify({
        "conversation_id": conversation_id,
        "messages": [dict(x) for x in messages],
        "tools": [dict(x) for x in tools],
        "escalations": [dict(x) for x in escalations]
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Route not found."
    }), 404


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )