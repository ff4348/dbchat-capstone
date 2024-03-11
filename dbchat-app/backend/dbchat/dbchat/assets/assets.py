from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from io import StringIO
import csv

# T2SQL model
def ask_chatgpt(q,llm):
    print("ASK CHATGPT!")
    # Table metadata is currently hardcoded
    # use sql alchemy inspect to extract 
    prompt_str = f"""Given the tables, columns and types mentioned below, return a SQL query that answers the question: {{question}}.
    If you can't give an answer based on the table's information, respond "I can't answer with the given information. Please refine the question or tell me which tables and columns I should use to answer.", else return ONLY the query.

    Tables, columns and types: 
    category table with columns [('category_id',int),('name',str),('last_update',datetime)]
    customer table with columns [('customer_id', int), ('store_id', int), ('first_name', str), ('last_name',str),('email',str),('address_id', int),('active',int),('create_date',datetime),('last_update',datetime)]
    language table with columns [('language_id, int),('name',str),('last_update',datetime)] 
    """
    question_prompt = ChatPromptTemplate.from_template(prompt_str)
    print("Question prompt created...")
    query_chain = question_prompt | llm
    print("Query chain created...")
    response = query_chain.invoke({"question": q}).content
    print("Response received...")
    final_response = response.replace('\n',' ')
    print("Final SQL query:",final_response)
    return final_response
    
# Function to execute SQL query for a single user question
def execute_query(db, sql_query):
    print("EXECUTE QUERY!")
    try:
        if "answer with the given information. Please refine the question or tell me" in sql_query:
            print("Unable to create SQL query")
            return {'query':'No query generated...', 'user_friendly':sql_query.replace("\\",""),'csv_download_link':''}
        print("SQL query to be executed:",sql_query)
        result = db.execute(text(sql_query))
        print("Query executed...")
        headers = list(result.keys())
        print("Result headers:",headers)
        records = result.fetchall()
        print("Fetch result...",records)
        num_records = len(records)
        records_as_dicts = [dict(zip(headers,row)) for row in records]
        print("Turn records into dictionary object....")
    # In case of error, return error message
    except Exception as e:
        print("Unable to query the database...", str(e))
        return {"query":'No query generated... ' + str(e), "user_friendly":"**ERROR: " + str(e), "csv_download_link":''}

    # Prepare user-friendly description
    description = f"{num_records} record(s) returned."

    # Prepare CSV for download
    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=headers)
    csv_writer.writeheader()
    print("get ready to..")
    csv_writer.writerows(records_as_dicts)
    print("Write data as csv...")
    csv_content = csv_data.getvalue()
    print("CSV content obtained....")

    # Return response with data and CSV download link
    return {
        "query": sql_query,
        "user_friendly": description,
        "csv_download_link": f"data:text/csv;charset=utf-8,{csv_content}"
    }