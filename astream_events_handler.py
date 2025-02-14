from langchain_core.messages import AIMessage
import streamlit as st
from graph import format_chat_data, graph_runnable


async def invoke_our_graph(st_messages, st_placeholder):
    st_messages = format_chat_data(st_messages)
    """
    Asynchronously processes a stream of events from the graph_runnable and updates the Streamlit interface.

    Args:
        st_messages (list): List of messages to be sent to the graph_runnable.
        st_placeholder (st.beta_container): Streamlit placeholder used to display updates and statuses.

    Returns:
        AIMessage: An AIMessage object containing the final aggregated text content from the events.
    """
    # Set up placeholders for displaying updates in the Streamlit app
    container = st_placeholder  # This container will hold the dynamic Streamlit UI components
    thoughts_placeholder = container.container()  # Container for displaying status messages
    thinking_text = ""  # Will store the accumulated text from the model's response
    final_output = "" # Will store the final output from on_chain_end
    status = None
    # Stream events from the graph_runnable asynchronously
    async for event in graph_runnable.astream_events({"user_query": st_messages, "output": "No outputs yet"}, version="v2"):
        kind = event["event"]  # Determine the type of event received
        if status is None:
            status = thoughts_placeholder.status("Thinking & Actions...", expanded=True)
        if kind == "on_chat_model_stream":  
            # The event corresponding to a stream of new content (tokens or chunks of text)
            addition = event["data"]["chunk"].content  # Extract the new content chunk
            thinking_text += addition  # Append the new content to the accumulated text
            if addition:
                # st.write(thinking_text + "done --\n\n")
                status.write(f"Generating: {thinking_text}")
                status.update(label="Thinking & Actions...", state="running", expanded=True)

        if kind == "on_tool_start":
            # The event signals that a tool is about to be called
            with thoughts_placeholder:
                status_placeholder = st.empty()  # Placeholder to show the tool's status
                with status_placeholder.status("Calling Tool...", expanded=True) as s:
                    st.write("Called ", event['name'])  # Show which tool is being called
                    st.write("Tool input: ")
                    st.code(event['data'].get('input'))  # Display the input data sent to the tool
                    st.write("Tool output: ")
                    output_placeholder = st.empty()  # Placeholder for tool output that will be updated later below
                    s.update(label="Completed Calling Tool!", expanded=False)  # Update the status once done

        elif kind == "on_tool_end":
            # The event signals the completion of a tool's execution
            with thoughts_placeholder:
                # We assume that `on_tool_end` comes after `on_tool_start`, meaning output_placeholder exists
                if 'output_placeholder' in locals():
                    output_placeholder.code(event['data'].get('output'))  # Display the tool's output

        elif kind == "on_chain_end":
            # Final output is in the last message
            # Ensure 'data' and 'output' exist in the event
            if 'output' in event['data']:
                output_data = event['data']['output']
                # Process only if 'output' is a dictionary and contains 'messages'
                if isinstance(output_data, dict) and 'messages' in output_data:
                    messages = output_data['messages']
                    if messages:  # Ensure it's not an empty list
                        final_output = messages[0].content

    # Update the status to complete and collapse it
    if status:
        status.update(label="Thoughts & Actions...", state="complete", expanded=False)
    # Update the status to complete and collapse it
    
    # Return the final aggregated message after all events have been processed
    return final_output