from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from io import StringIO
import pandas as pd
import csv
from sqlvalidator import parse
from transformers import pipeline
from dotenv import load_dotenv
import json
import os 
import re
import time

def remove_before_select(input_text):
    # Find the position of the first occurrence of "SELECT"
    select_pos = input_text.upper().find("SELECT")
    # If "SELECT" is found, return everything from that position onwards; otherwise, return the original text
    if select_pos != -1:
        return input_text[select_pos:]
    else:
        return input_text

def format_basic_prompt(q, schema, prompt, db_type='mysql', test=False):
  """Create prompt for inference - NO query included"""
  prompt_fmt = prompt.format(
      db_type=db_type,
      question=q,
      db_schema=schema,
  ).strip()
  if test:
    prompt_fmt = '[INST] \n' + prompt_fmt + ' [/INST]\n'
    return re.sub(r'\n\n\n+', '\n\n', prompt_fmt).strip()
  prompt_fmt = '<s> [INST] \n' + prompt_fmt + ' </s>'
  # prompt_fmt = re.sub(r'\s+', ' ', prompt_fmt).strip()
  prompt_fmt = re.sub(r'\n\n\n+', '\n\n', prompt_fmt).strip()
  return re.sub(r'### ANSWER', '### ANSWER [/INST]', prompt_fmt).strip()

def t2sql_mistralFT(llm_pipe, question, db_schema='CREATE TABLE customer (customer_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,store_id TINYINT UNSIGNED NOT NULL,first_name VARCHAR(45) NOT NULL,last_name VARCHAR(45) NOT NULL,email VARCHAR(50) DEFAULT NULL,address_id SMALLINT UNSIGNED NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,create_date DATETIME NOT NULL,last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,PRIMARY KEY  (customer_id),KEY idx_fk_store_id (store_id),KEY idx_fk_address_id (address_id),KEY idx_last_name (last_name),CONSTRAINT fk_customer_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,CONSTRAINT fk_customer_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;', db_type='sql lite'):
    basic_prompt_template = """
    ### INSTRUCTIONS
    You are a tool to generate a {db_type} SQL statement based on the given question and database schema.
    Your answer should ONLY be a SQL statement, and strictly no other content. If you can't generate an answer with the given schema, return "NOT SURE" only.

    ### SCHEMA
    {db_schema}

    ### QUESTION
    {question}

    ### ANSWER
    """

    prompt_str = format_basic_prompt(question,db_schema,basic_prompt_template)
    print("prompt:")
    print(prompt_str)

    print('starting model inference...')
    start_time = time.time()
    print(start_time)
    gen_queries = llm_pipe(prompt_str)
    print('gen_queries:',gen_queries)
    final_query = gen_queries[0]['generated_text'].strip().split('[/INST]')[-1].strip()
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    print('final query:',final_query)
    return final_query

def t2SQL_sqlcoder(runtime, user_question = 'how many customers do we have?', table_metadata_string_DDL_statements = 'CREATE TABLE customer (customer_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,store_id TINYINT UNSIGNED NOT NULL,first_name VARCHAR(45) NOT NULL,last_name VARCHAR(45) NOT NULL,email VARCHAR(50) DEFAULT NULL,address_id SMALLINT UNSIGNED NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,create_date DATETIME NOT NULL,last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,PRIMARY KEY  (customer_id),KEY idx_fk_store_id (store_id),KEY idx_fk_address_id (address_id),KEY idx_last_name (last_name),CONSTRAINT fk_customer_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,CONSTRAINT fk_customer_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'):
    print("Text2SQL using sqlcoder2")
    db_type = 'mysql'
    prompt = f'''
    ### INSTRUCTIONS
    Your task is convert a question into a SQL query, given a {db_type} database schema.
    Adhere to these rules:
    - **Deliberately go through the question and database schema word by word** to appropriately answer the question
    - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
    - When creating a ratio, always cast the numerator as float

    ### INPUT
    Generate a SQL query that answers the question: `{user_question}`.
    This query will run on a database whose schema is represented in this string:
    {table_metadata_string_DDL_statements}

    ### RESPONSE
    [SQL]
    '''

    # hyperparameters for model
    parameters = {
        "temperature": 0.07, # controls randomness of generated text
        "max_new_tokens": 200 # limits length of generated text
    }

    # Invoke the endpoint using the `invoke_endpoint` method of the SageMaker runtime client object
    try:
        load_dotenv()
        response = runtime.invoke_endpoint(EndpointName=os.getenv('SQLCODER_ENDPOINT'),
                                    ContentType='application/json',
                                    Body=json.dumps({"inputs": prompt,
                                                        "parameters": parameters})
                                    )
    except Exception as e:
        print("Unable to hit sqlcoder endpoint!")
        return "No SQL query generated..."

    # Parse the output data returned by the endpoint
    output_data = json.loads(response['Body'].read().decode())[0]['generated_text']
    sql_query = output_data.split('\n')[-1].strip()
    sql_query = sql_query.replace('NULLS LAST','')
    print("GENERATED SQL QUERY!!!!",sql_query)
    return sql_query


# GPT T2SQL model
def t2SQL_gpt(q,llm,schema_info,db_name):
    print("Text2SQL using",llm.model_name,'!')
    db_type='mysql'
    prompt_str = f"""
    ### INSTRUCTIONS
    You are a tool to generate a {db_type} SQL statement based on the given question and database schema.
    Your answer should ONLY be a SQL statement, and strictly no other content. If you can't generate an answer with the given schema, return "NOT SURE" only.

    ### SCHEMA
    {schema_info}

    ### QUESTION
    {q}    

    ### ANSWER
    Your answer should ONLY be a SQL statement, and strictly no other content. If you can't generate an answer with the given schema, return "NOT SURE" only.
    """
    print(prompt_str)
    question_prompt = ChatPromptTemplate.from_template(prompt_str)
    print("Question prompt created...")
    query_chain = question_prompt | llm
    print("Query chain created...")
    response = query_chain.invoke({"question": q, 'db_name':db_name, 'schema_info':schema_info}).content
    print("Response received...")
    final_response = response.replace('\n',' ').replace('\t',' ')
    print("Final SQL query:",final_response)
    print("GENERATED SQL QUERY!!!!",final_response)
    return final_response


def get_schema(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = Inspector.from_engine(engine)
    tbl_info_str = ''
    tbl_info_dict = {"Databases":{}}
    load_dotenv()
    acceptable_databases = list(os.getenv('ALLOWED_DBS').split(":"))
    db_list = list(set(inspector.get_schema_names()).intersection(set(acceptable_databases)))

    for database_name in db_list:
        tbl_info_dict["Databases"][database_name] = {"Tables": {}}
        database_tables = inspector.get_table_names(schema=database_name)
        
        for table_name in database_tables:
            full_table_name = f"{database_name}.{table_name}"
            tbl_info_str += f'Table - {full_table_name}: '
            #print(f"Table - {full_table_name}")
            tbl_info_dict["Databases"][database_name]["Tables"][table_name] = []
            
            for column in inspector.get_columns(table_name, schema=database_name):
                column_name = column['name']
                column_type = column['type']
                tbl_info_dict["Databases"][database_name]["Tables"][table_name].append(f"{column_name}|{column_type}")
                tbl_info_str += f"Column: {column_name}, Type: {column_type} "
                #print(f"Column: {column_name}, Type: {column_type}")
            
            tbl_info_dict["Databases"][database_name]["Tables"][table_name].sort()
            
            pk_constraint = inspector.get_pk_constraint(table_name, schema=database_name)
            pk_columns = pk_constraint['constrained_columns']
            tbl_info_str += f"Primary Key(s) for {full_table_name}: {pk_columns} "
            #print(f"Primary Key(s) for {full_table_name}: {pk_columns}")

    return tbl_info_str, tbl_info_dict

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
        num_rows, num_columns = df.shape
        return "We’re thrilled to present you with data that comprehensively addresses your question. However, summarizing its extensive volume, which includes {num_rows} rows and {num_columns} columns, concisely is quite a task. But worry not! We’ve attached a comprehensive CSV table for your perusal. Feel free to dive in and explore all the insights it has to offer!"



# Function to execute SQL query for a single user question
# Returns user friendly response, sql query executed, and data
def execute_query(db, sql_query, question, llm):
    print("EXECUTE QUERY!")
    try:
        if "NOT SURE" in sql_query:
            print("Unable to create SQL query")
            return {'query':'No query generated...', 'user_friendly':"I'm unable to answer your question. Please try asking again...",'csv_download_link':''}

        sql_query = remove_before_select(sql_query)

        # SQL Validation
        parsed_sql = parse(sql_query)
        print("parsed_sql",parsed_sql)
        print("is valid?",parsed_sql.is_valid())
        if not parsed_sql.is_valid():
            print("SQL syntax error:", parsed_sql.errors)
            return {'query': 'Invalid SQL syntax...', 'user_friendly': "I'm unable to answer your question. Please try asking again...", 'csv_download_link': ''}
        
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
        return {"query":'No query generated... ' + str(e), "user_friendly":"I'm unable to answer your question. Please try again...", "csv_download_link":''}

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