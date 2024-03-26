from openai import OpenAI
import streamlit as st

st.title("ChatGPT-like clone")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

db = st.sidebar.selectbox(
    'Select Database',
    ('A', 'B', 'C'))

st.sidebar.write('You selected:', db)

if db == 'A': 
    table = st.sidebar.selectbox(
    'Select table',
    ('A.1', 'A.2', 'A.3'))
if db == 'B': 
    table = st.sidebar.selectbox(
    'Select table',
    ('B.1', 'B.2', 'B.3'))
if db == 'C': 
    table = st.sidebar.selectbox(
    'Select table',
    ('C.1', 'C.2', 'C.3'))