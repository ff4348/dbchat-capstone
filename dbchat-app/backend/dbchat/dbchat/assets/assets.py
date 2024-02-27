from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from io import StringIO
import csv

# T2SQL model
def ask_chatgpt(q,llm):
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
    query_chain = question_prompt | llm
    response = query_chain.invoke({"question": q}).content
    final_response = response.replace('\n',' ')
    return final_response
    
# Function to execute SQL query for a single user question
def execute_query(db, sql_query):
    try:
        result = db.execute(text(sql_query))
        headers = list(result.keys())
        records = result.fetchall()
        num_records = len(records)
        records_as_dicts = [dict(zip(headers,row)) for row in records]
    # In case of error, return error message
    except Exception as e:
        print("Unable to query the database...", str(e))
        return {"description":'Unable to query the database... ' + str(e), "records_returned":0, "csv_download_link":''}

    # Prepare user-friendly description
    description = f"{num_records} record(s) returned."

    # Prepare CSV for download
    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=headers)
    csv_writer.writeheader()
    csv_writer.writerows(records_as_dicts)
    csv_content = csv_data.getvalue()

    # Return response with data and CSV download link
    return {
        "description": description,
        "records_returned": num_records,
        "csv_download_link": f"data:text/csv;charset=utf-8,{csv_content}"
    }