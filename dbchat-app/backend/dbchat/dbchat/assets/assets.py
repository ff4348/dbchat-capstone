from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from io import StringIO
import pandas as pd
import csv
from sqlvalidator import parse
import json

def t2SQL_sqlcoder15B(runtime, user_question = 'how many customers do we have?', table_metadata_string_DDL_statements = 'CREATE TABLE customer (customer_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,store_id TINYINT UNSIGNED NOT NULL,first_name VARCHAR(45) NOT NULL,last_name VARCHAR(45) NOT NULL,email VARCHAR(50) DEFAULT NULL,address_id SMALLINT UNSIGNED NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,create_date DATETIME NOT NULL,last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,PRIMARY KEY  (customer_id),KEY idx_fk_store_id (store_id),KEY idx_fk_address_id (address_id),KEY idx_last_name (last_name),CONSTRAINT fk_customer_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,CONSTRAINT fk_customer_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'):
    print("Text2SQL using sqlcoder2")
    prompt = f'''
    ### Task
    Generate a SQL query to answer [QUESTION]{user_question}[/QUESTION]
    -- Make sure to use aliases for all columns extracted
    --- If you do not know how to answer the question only answer with 'I cannot answer the question. Please try again.'

    ### Database Schema
    The query will run on a database with the following schema:
    {table_metadata_string_DDL_statements}

    ### Answer
    [SQL]
    '''

    # hyperparameters for model
    parameters = {
        "temperature": 1, # controls randomness of generated text
        "max_new_tokens": 200 # limits length of generated text
    }

    # Invoke the endpoint using the `invoke_endpoint` method of the SageMaker runtime client object
    response = runtime.invoke_endpoint(EndpointName='huggingface-pytorch-tgi-inference-2024-03-26-22-59-39-877',
                                   ContentType='application/json',
                                   Body=json.dumps({"inputs": prompt,
                                                    "parameters": parameters})
                                   )

    # Parse the output data returned by the endpoint
    output_data = json.loads(response['Body'].read().decode())[0]['generated_text']
    sql_query = output_data.split('\n')[-1].strip()
    return sql_query


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