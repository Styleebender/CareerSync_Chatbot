
from sample_data import data
def process_linkedin_data(data):
    # Create copy to avoid modifying original data
    processed_data = data.copy()
    
    # Extract photo and background URLs first
    photo_url = None
    background_url = None
    
    if "person" in processed_data:
        person = processed_data["person"]
        # Get URLs before removing them
        photo_url = person.get("photoUrl")
        background_url = person.get("backgroundUrl")
    
    # Remove top-level keys
    for key in ["success", "credits_left", "rate_limit_left", "company"]:
        processed_data.pop(key, None)
    
    # Process person information
    if "person" in processed_data:
        person = processed_data["person"]
        # Remove specified person keys
        for key in ["linkedInIdentifier", "memberIdentifier", "photoUrl",
                   "backgroundUrl", "creationDate", "followerCount"]:
            person.pop(key, None)
    
    # Return both extracted URLs and cleaned data
    return photo_url, background_url, processed_data




def process_job_data(data):
    # Create copy to avoid modifying original data
    processed_data = data.copy()
    
    # Remove top-level keys
    for key in ["success", "credits_left", "rate_limit_left"]:
        processed_data.pop(key, None)
    
    # Process each job information
    if "job" in processed_data:
        # Remove specified keys
        for key in ["linkedinIdentifier", "companyLogo"]:
            processed_data['job'].pop(key, None)
    
    # Return both extracted URLs and cleaned data
    return processed_data


from typing import List, Dict, Any
def format_chat_data(messages: List[Any]) -> Dict[str, str]:
    # Handle empty messages case
    if not messages:
        return {
            "chat_history": "No chat history",
            "current_query": ""
        }

    # Extract current query from the last message
    current_query = messages[-1].content

    # Prepare chat history
    if len(messages) == 1:
        chat_history_str = "No chat history"
    else:
        # Process all messages except the last one
        formatted_messages = []
        for msg in messages[:-1]:
            # Format message without additional fields
            msg_type = msg.__class__.__name__
            content = repr(msg.content)  # Handles string escaping
            formatted_messages.append(f"{msg_type}(content={content})")

        # Create formatted chat history string
        chat_history_str = "[\n  " + ",\n  ".join(formatted_messages) + "\n]"

    return f"""
Previous Chat History: "{chat_history_str}
Current User Question (HumanMessage): {current_query}
"""

# photo, background, cleaned = process_linkedin_data(data)
# print("Extracted Photo URL:", photo)
# print("Extracted Background URL:", background)
# print("Cleaned Data Structure:", cleaned)

# import sample_data
# cleaned = process_job_data(sample_data.job_data2)
# print("Cleaned Data Structure:", cleaned)
