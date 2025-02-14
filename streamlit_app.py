import streamlit as st
import asyncio
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv
from linkedin_scraper import ScrapinAPI, get_profile_data, get_Job_data
from langchain_core.messages import AIMessage, HumanMessage
from astream_events_handler import invoke_our_graph   # Utility function to handle events from astream_events from graph
load_dotenv()

# app config
st.set_page_config(page_title="CareerSync Chatbot", page_icon="🤖")
st.title(":rainbow[_CareerSync_] :blue[Chatbot]")
st.markdown("*Your AI-Powered LinkedIn and Career Strategist!*")

# Functions to validate respective URL
def is_valid_linkedin_profile_url(url):
    if not url.startswith("https://www.linkedin.com/in/"):
        return False
    return True

def is_valid_linkedin_job__url(url):
    if not url.startswith("https://www.linkedin.com/jobs/"):
        return False
    return True

# Initialize session state
if "messages" not in st.session_state:
    # Default initial message to render in message state
    st.session_state["messages"] = [AIMessage(content="Hi! 👋 I’m your AI career assistant. I can optimize your LinkedIn profile, analyze job fit, generate personalized cover letters, career recommendations and networking opportunities & events. Share your profile or a job link to get started!")]


# Disable chat input until response is received.
# if "chat_input" not in st.session_state:
#     st.session_state.chat_input = False
# def disable_callback():
#     st.session_state.chat_input = True
# disabled=st.session_state.chat_input, on_submit=disable_callback


# Loop through all messages in the session state and render them as a chat on every st.refresh mech
for msg in st.session_state.messages:
    # https://docs.streamlit.io/develop/api-reference/chat/st.chat_message
    # we are storing them as AIMessage and HumanMessage as its easier to send to LangGraph
    if type(msg) == AIMessage:
        st.chat_message("assistant").write(msg.content)
    if type(msg) == HumanMessage:
        st.chat_message("user").write(msg.content)

# Takes new input in chat box from user and invokes the graph
if prompt := st.chat_input():
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    # Process the AI's response and handles graph events using the callback mechanism
    with st.chat_message("assistant"):
        # create a placeholder container for streaming and any other events to visually render here
        placeholder = st.container()
        response = asyncio.run(invoke_our_graph(st.session_state.messages, placeholder))
        st.write(response)
        st.session_state.messages.append(AIMessage(content=str(response)))
        

