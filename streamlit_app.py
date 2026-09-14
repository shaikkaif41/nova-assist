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

with st.form("chat_form"):
    user_message = st.text_input(
        "Message",
        placeholder="Ask about orders, products, or returns..."
    )

    submitted = st.form_submit_button("Send")

if submitted and user_message.strip():

    user_message = user_message.strip()

    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):

        with st.spinner("NOVA-ASSIST is thinking..."):

            try:
                result = chat(
                    user_message,
                    st.session_state.conversation_id
                )

                st.session_state.conversation_id = (
                    result["conversation_id"]
                )

                response = result["response"]

            except Exception as e:
                response = f"Error: {e}"

            st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })