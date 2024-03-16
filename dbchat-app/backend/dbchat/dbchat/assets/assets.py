from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from io import StringIO
import pandas as pd
import csv
from sqlvalidator import parse

# GPT T2SQL model
def t2SQL_gpt(q,llm,schema_info,db_name):
    print("Text2SQL using",llm.model_name,'!')
    prompt_str = f"""Given the tables, columns and types mentioned below, return a SQL query that answers the question: {{question}}.
    If you can't give an answer based on the table's information, respond "I can't answer with the given information. 
    Please refine the question or tell me which tables and columns I should use to answer.", else return ONLY the query.

    You are using {db_name}.
    Tables, primary keys, and columns (column name and type) for the database: 
    {{schema_info}}
    
    """
    print(prompt_str)
    question_prompt = ChatPromptTemplate.from_template(prompt_str)
    print("Question prompt created...")
    query_chain = question_prompt | llm
    print("Query chain created...")
    response = query_chain.invoke({"question": q, 'db_name':db_name, 'schema_info':schema_info}).content
    print("Response received...")
    final_response = response.replace('\n',' ')
    print("Final SQL query:",final_response)
    return final_response


def get_schema(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = Inspector.from_engine(engine)
    tbl_info_str = ''
    for table_name in inspector.get_table_names():
        tbl_info_str += f'Table - {table_name}: '
        print(f"Table - {table_name}")
        
        for column in inspector.get_columns(table_name):
            column_name = column['name']
            column_type = column['type']
            tbl_info_str += f"Column: {column_name}, Type: {column_type}"
            print(f"Column: {column_name}, Type: {column_type}")
        
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint['constrained_columns']
        tbl_info_str += f"Primary Key(s) for {table_name}: {pk_columns}"
        print(f"Primary Key(s) for {table_name}: {pk_columns}")

    return tbl_info_str

def outputmodel(records_as_dicts, q, llm):
    print("Preparing user output...")
    df = pd.DataFrame(records_as_dicts)
    if df.size < 20:
        print("df.size < 20")
        prompt_str = f"Generate an answer in couple sentences based on question and record that shows the answer. Don’t mention I provided you record. Question: {{question}}. Record: {{records_as_dicts}}."
        output_prompt = ChatPromptTemplate.from_template(prompt_str)
        print("Output prompt created...")
        output_chain = output_prompt | llm
        print("Output chain created...")
        response = output_chain.invoke({"question": q, 'records_as_dicts':records_as_dicts}).content
        print("Response received...")
        final_response = response.replace('\n','')
        return final_response
    elif 20 <= df.size < 100:
        print("20 <= df.size < 100")
        prompt_str = f"Generate an answer in a paragraph based on question and record that shows the answer. Don’t mention I provided you record. Question: {{question}}. Record: {{records_as_dicts}}."
        output_prompt = ChatPromptTemplate.from_template(prompt_str)
        print("Output prompt created...")
        output_chain = output_prompt | llm
        print("Output chain created...")
        response = output_chain.invoke({"question": q, 'records_as_dicts':records_as_dicts}).content
        print("Response received...")
        final_response = response.replace('\n','')
        return final_response
    else:
        print("df.size >= 100")
        return "Regrettably, we are unable to generate a concise summary of the data due to its extensive volume. Please refer to the attached table in csv format for a comprehensive overview."



# Function to execute SQL query for a single user question
def execute_query(db, sql_query, question, llm):
    print("EXECUTE QUERY!")
    try:
        if "Please refine the question or tell me which tables and columns I should use to answer" in sql_query:
            print("Unable to create SQL query")
            return {'query':'No query generated...', 'user_friendly':sql_query.replace("\\",""),'csv_download_link':''}

        # SQL Validation
        parsed_sql = parse(sql_query)
        print("parsed_sql",parsed_sql)
        print("is valid?",parsed_sql.is_valid())
        if not parsed_sql.is_valid():
            print("SQL syntax error:", parsed_sql.errors)
            return {'query': 'Invalid SQL syntax...', 'user_friendly': "SQL Syntax Error. Please try asking again..." + str(parsed_sql.errors), 'csv_download_link': ''}
        
        print("SQL query to be executed:",sql_query)
        result = db.execute(text(sql_query))
        print("Query executed...")
        headers = list(result.keys())
        print("Result headers:",headers)
        records = result.fetchall()
        print("Fetch result...")
        records_as_dicts = [dict(zip(headers,row)) for row in records]
        print("Turn records into dictionary object....")
        user_friendly = outputmodel(records_as_dicts, question, llm)
        print("Create user friendly response...")
    # In case of error, return error message
    except Exception as e:
        print("Unable to query the database...", str(e))
        return {"query":'No query generated... ' + str(e), "user_friendly":"**ERROR: " + str(e), "csv_download_link":''}

    # Prepare CSV for download
    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=headers)
    csv_writer.writeheader()
    csv_writer.writerows(records_as_dicts)
    print("Write data as csv...")
    csv_content = csv_data.getvalue()
    print("CSV content obtained....")

    # Return response with data and CSV download link
    return {
        "query": sql_query,
        "user_friendly": user_friendly,
        "csv_download_link": f"data:text/csv;charset=utf-8,{csv_content}"
    }