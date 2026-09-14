import streamlit as st
from agent.agent import chat

st.set_page_config(
    page_title="NOVA-ASSIST",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 NOVA-ASSIST")
st.caption("NovaMart AI Customer Support")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Ask about orders, products, or returns...")

if user_message:

    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("NOVA-ASSIST is thinking..."):

            result = chat(
                user_message,
                st.session_state.conversation_id
            )

            st.session_state.conversation_id = (
                result["conversation_id"]
            )

            response = result["response"]

            st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })