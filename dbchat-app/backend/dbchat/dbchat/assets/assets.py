from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.reflection import Inspector
from io import StringIO
import csv
from sqlvalidator import parse


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


# Function to execute SQL query for a single user question
def execute_query(db, sql_query):
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