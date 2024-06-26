import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
import requests
import json
import openai 


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

    if (details['table_output_msg'] != 'NA') or (details['table_preview'] != 'NA'):
        with st.expander("Table Preview"):
            st.write(f"{details['table_output_msg']}")
            st.dataframe(details['table_preview'], use_container_width=True)

    if (details['sql_code'] != 'NA'):
        # SQL Code Expander
        with st.expander("SQL Code"):
            st.code(details['sql_code'])

    if (details['csv_file_path'] != 'NA'):
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

def handle_user_input(prompt, model_selection):

    if len(prompt) > 200: 
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": 'Please shorten your prompt to less than 200 characters'})
    else:

        if model_selection == 'gpt4':
            response = json.loads(requests.post(url = "http://dbchat_backend:8000/query", data = json.dumps({"question":prompt})).text)
        elif model_selection == 'defog/sqlcoder':
            response = json.loads(requests.post(url = "http://dbchat_backend:8000/sqlcoder-query", data = json.dumps({"question":prompt})).text)
        elif model_selection == 'mistral-finetuned':
            response = json.loads(requests.post(url = "http://dbchat_backend:8000/mistral-query", data = json.dumps({"question":prompt})).text)
        else:
            response_details = {
                "user_friendly": "Unable to query using current model selection...",
                "table_output_msg": "NA",
                "table_preview": "NA",
                "sql_code": "NA",
                "csv_file_path": "NA"  # CSV file path for full data
            }

        if 'Unable to connect to the database' in response['user_friendly'].lower():
            response_details = {
                "user_friendly": response['user_friendly'],
                "table_output_msg": 'NA',
                "table_preview": 'NA',
                "sql_code": 'NA',
                "csv_file_path": 'NA'  # CSV file path for full data
            }

        elif 'Please try asking again' in response['user_friendly'].lower():
            response_details = {
                "user_friendly": response['user_friendly'],
                "table_output_msg": 'NA',
                "table_preview": 'NA',
                "sql_code": 'NA',
                "csv_file_path": 'NA'  # CSV file path for full data
            }

            
        elif response['csv_download_link'].strip() == '':
            response_details = {
                "user_friendly": response['user_friendly'],
                "table_output_msg": 'NA',
                "table_preview": 'NA',
                "sql_code": 'NA',
                "csv_file_path": 'NA'  # CSV file path for full data
            }

        else:
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

def reset_conversation():
  st.session_state.messages = []

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

def main():
    """
    The main entry point for the Streamlit application.
    This function sets up the Streamlit UI components, including the title, sidebar options,
    chat interface, and handles user input and feedback mechanisms.
    """

    tab1, tab2, tab3 = st.tabs(["DBChat", "User Guide", "Model Details"])
    with tab1:
        st.title("DBChat")
        st.subheader("Query your database using a chat bot")

        # Model selection
        model_selection = st.sidebar.selectbox("Please select the Text2SQL model",['gpt4','defog/sqlcoder', 'mistral-finetuned'])
        st.sidebar.write("You selected", model_selection)
        
        st.sidebar.markdown("---")
        
        database_or_csv = st.sidebar.radio("Select Data Source", ("Database", "CSV Upload"))
        
        if database_or_csv == "Database":
        
            # Clear the sidebar of any content related to CSV upload
            st.sidebar.empty()

            # schema information
            schema_info = requests.get(url = "http://dbchat_backend:8000/schema").json()
            databases = [database for database in sorted(list(schema_info['Databases'].keys()))]
            db = st.sidebar.selectbox("Please select the database",databases)
            st.sidebar.write('You selected:', db)

            tables = [tbl for tbl in schema_info['Databases'][db]['Tables'].keys()]
            table = st.sidebar.selectbox('Available tables',tables)

            columns_info = schema_info['Databases'][db]['Tables'][table]

            # Extracting column names and data types
            column_names = []
            data_types = []
            for col_info in columns_info:
                col_name, data_type = col_info.split('|')
                column_names.append(col_name.strip())
                data_types.append(data_type.strip())

            # Creating a DataFrame to display in a table
            data = {'Column Name': column_names, 'Data Type': data_types}
            df = pd.DataFrame(data)

            # Displaying the table in the sidebar
            st.sidebar.table(df)
        
        elif database_or_csv == "CSV Upload":
            # Display the CSV upload option in the sidebar
            uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
                st.write(f"Table name: {uploaded_file.name}")

                # Extracting column names and data types from the uploaded CSV file
                column_names = df.columns.tolist()
                data_types = df.dtypes.tolist()

                # Creating a DataFrame to display in a table
                data = {'Column Name': column_names, 'Data Type': data_types}
                df_info = pd.DataFrame(data)

                # Displaying the column information in the sidebar
                st.sidebar.table(df_info)

        st.sidebar.markdown("---")

        st.button('Reset Chat', on_click=reset_conversation)

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
        if prompt: 
            handle_user_input(prompt, model_selection)
            # Rerun the app to ensure new messages are displayed immediately
            st.rerun()
    with tab2: 
        st.header('About', divider='grey')
        st.markdown('DBChat allows you to query databases using natural language without writing any SQL. Leveraging a state of the art GPT-4, SQLCoder, and Mistral 7B language models, DBChat converts your natural language into an efficient SQL query and returns the result in an easy to read format. Additionally, you can view the query itself and download the result as a CSV for further analysis.')
        st.header('Tips for writing effective prompts: ', divider='grey')
        st.markdown("- Avoid vague, incomplete, or open-ended statements (ex. Tell me about our users).")
        st.markdown("- Include filtering criteria (ex. date) to reduce the size of the result.")
        st.markdown("- Ensure your question can actually be answered by the available database by inspecting the available tables and columns.")
        #st.markdown("- Use the clear chat button to initialize a new line of questioning. This helps the model understand if you are asking a follow up question or not.")
    with tab3: 
        st.header('About the models', divider='grey')
        st.markdown("GPT-4 is a large language model with strong performance across SQL evaluation datasets. Our tests have shown a 17 percentage point difference in performance when compared to other top models such as Defog's SQLCoder and Mistral. Defog's SQLCoder is a state-of-the-art LLM for converting natural language questions to SQL queries. SQLCoder is a 15B parameter model that slightly outperforms gpt-3.5-turbo for natural language to SQL generation tasks on our sql-eval framework, and significantly outperforms all popular open-source models. It also significantly outperforms text-davinci-003, a model that's more than 10 times its size. SQLCoder is fine-tuned on a base StarCoder model. Lastly, we also provide a finetuned version of the Mistral 7B model, which has roughly 100x fewer parameters compared to GPT-4. For certain queries, this can be a more cost-effective choice.") 

if __name__ == "__main__":
    main()