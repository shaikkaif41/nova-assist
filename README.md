# NOVA-ASSIST

## AI Customer Support Agent with Integrated Order Database

NOVA-ASSIST is an AI-powered customer support system for NovaMart.

It allows customers to interact with an AI agent for:

- Order status
- Order details
- Product search
- Return eligibility
- Return requests
- Human escalation

The project demonstrates how an AI agent can interact with a relational database through controlled backend tools.

---

# Architecture

```text
Customer
   |
   v
Web Chat
   |
   v
Flask API
   |
   v
NOVA-ASSIST AI Agent
   |
   v
Tool Router
   |
   +----------------------+
   |                      |
   v                      v
Database Tools       Tool Logging
   |                      |
   v                      v
SQLite Database      Conversations
                     Messages
                     Escalations