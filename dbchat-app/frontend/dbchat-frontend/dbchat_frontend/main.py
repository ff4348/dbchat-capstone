import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
import requests
import json

def display_response_with_details(details):
    """
    Display detailed response information from a dictionary.

    This function organizes and displays information about a DataFrame, including its shape,
    a preview of the data, and SQL code for a sample query. It also provides
    a download button to download a CSV file for the data.
    Args:
    details (dict): A dictionary containing detailed information about the data,
                    including the table summary, preview, SQL code, and CSV file path.
    """
    st.markdown(details['user_friendly'])

    with st.expander("Table Preview"):
        st.write(f"{details['table_output_msg']}")
        st.dataframe(details['table_preview'], use_container_width=True)

    # SQL Code Expander
    with st.expander("SQL Code"):
        st.code(details['sql_code'])

    # Download CSV Button
    with open(details['csv_file_path'], "rb") as file:
        st.download_button("Download full data as CSV", data=file, file_name="full_data.csv",key=datetime.now().strftime("%Y%m%d_%H%M%S_%f"))


def generate_tab_output(csv_data):
    # Convert the CSV data string into a DataFrame
    df = pd.read_csv(StringIO(csv_data.split(",",1)[1]))
    
    # Your existing logic
    if df.size == 1:
        output_msg = "The result consists of a single record:"
        output_table = df

    elif len(df) <= 20:
        output_msg = f"The result is a table with {len(df)} rows and {len(df.columns)} columns:"
        output_table = df

    else:
        output_msg = f"The result is a large table with {len(df)} rows and {len(df.columns)} columns. Displaying the first 20 rows and the table summary:"
        output_table = df.head(20)

    # Save the full DataFrame to a CSV file
    csv_file_path = "full_data.csv"
    df.to_csv(csv_file_path, index=False)

    return output_msg, output_table, csv_file_path

def handle_user_input(prompt):
    response = json.loads(requests.post(url = "http://dbchat_backend:8000/query", data = json.dumps({"question":prompt})).text)
    output_msg, display_df, csv_file_path = generate_tab_output(response['csv_download_link'])

    
    # Response details dictionary updated with the CSV path
    response_details = {
        "user_friendly": response['user_friendly'],
        "table_output_msg": output_msg,
        "table_preview": display_df,
        "sql_code": response['query'],
        "csv_file_path": csv_file_path  # CSV file path for full data
    }

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response_details})


def display_feedback_options(idx):
    """
    Display feedback options (like/dislike) for each assistant's response.
    This function creates UI components for feedback on the assistant's responses,
    including like and dislike buttons and a text input for detailed feedback.

    Args:
        idx (int): The index of the response message for which feedback is being given.
    """
    # Define keys for like, dislike and feedback
    like_key = f"like_{idx}"
    dislike_key = f"dislike_{idx}"
    feedback_key = f"feedback_{idx}"
    submit_key = f"submit_{idx}"

    # Initialize the feedback status if it doesn't exist
    if feedback_key not in st.session_state or not isinstance(st.session_state[feedback_key], dict):
        st.session_state[feedback_key] = {"status": None, "text": ""}

    # Place Like and Dislike buttons next to each other
    cols = st.columns([1, 1, 8])  # Adjusting the ratio to bring buttons closer
    with cols[0]:
        if st.button("👍", key=like_key):
            # Handle like action
            st.session_state[feedback_key]["status"] = "liked"
            st.session_state[feedback_key]["text"] = ""  # Clear any existing feedback

    if st.session_state[feedback_key].get("status") == "liked": # moved outside of original if statement so message doesn't align within columns
        st.success("Thank you for the positive feedback!")


    with cols[1]:
        if st.button("👎", key=dislike_key):
            # Handle dislike action
            st.session_state[feedback_key]["status"] = "disliked"

    # Show feedback input only if "Dislike" has been clicked
    if st.session_state[feedback_key].get("status") == "disliked":
        # Text input for feedback
        feedback_text = st.text_input(
            "Please share more details to help us improve DBChat:", 
            key=f"feedback_text_{idx}"
        )
        st.session_state[feedback_key]["text"] = feedback_text
        
        # Submit button for feedback
        if st.button("Submit Feedback", key=submit_key):
            # You can process the feedback here
            st.session_state[feedback_key]["status"] = "submitted"  # Update status to prevent resubmission
            st.success("Your feedback has submitted and is greatly appreciated. Thank you!")

            ##### SEND TO DATABASE (single database to store user feedback) HERE ########

# Function that will hit backend API to get schema information to populate tables
def get_schema():
    response = requests.post(url = "http://dbchat_backend:8000/schema").json()
    print(response)
    return response

    

def main():
    """
    The main entry point for the Streamlit application.
    This function sets up the Streamlit UI components, including the title, sidebar options,
    chat interface, and handles user input and feedback mechanisms.
    """

    st.title("DBChat")
    st.subheader("Query your database using natural language")

    schema_info = get_schema()

    db = st.sidebar.selectbox(
        "Please select the database:",
    ("products", "sales", "inventory"))

    st.sidebar.write('You selected:', db)

    if db == 'products': 
        table = st.sidebar.selectbox(
        'Select table',
        ('A.1', 'A.2', 'A.3'))
    if db == 'sales': 
        table = st.sidebar.selectbox(
        'Select table',
        ('B.1', 'B.2', 'B.3'))
    if db == 'inventory': 
        table = st.sidebar.selectbox(
        'Select table',
        ('C.1', 'C.2', 'C.3'))

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all messages
    for idx, message in enumerate(st.session_state.messages, start=1):
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            if isinstance(content, str):
                st.markdown(content)
            else:  # Assume it's a detailed response
                display_response_with_details(content)
            if role == "assistant":
                display_feedback_options(idx)

    # User input
    prompt = st.chat_input("Type your question here...")
    if prompt:  # If a non-empty string is entered by the user
        handle_user_input(prompt)
        # Rerun the app to ensure new messages are displayed immediately
        st.rerun()

if __name__ == "__main__":
    main()