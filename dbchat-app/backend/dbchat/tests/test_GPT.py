from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from dbchat.assets.assets import get_schema
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Instantiate model using LangChain

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4")
db_name = os.getenv("PRIM_DB_NAME")
connection_str = f"mysql+pymysql://{os.getenv('PRIM_DB_USER')}:{os.getenv('PRIM_DB_PWD')}@{os.getenv('PRIM_DB_HOST')}:{os.getenv('PRIM_DB_PORT')}/{db_name}"

engine = create_engine(connection_str, connect_args={'init_command': 'SET SESSION max_execution_time=20000'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("SQL Alchemy engine and session defined...")


schema_info, schema_dict = get_schema(engine)
question = 'How many customers do we have?'

prompt_str = f"""Given the tables, columns and types mentioned below, return a SQL query
(make sure you alias all columns) that answers the following question: {question}.
If you can't generate a SQL query based on the table's information, respond "I can't answer with the given information. 
Please refine the question or tell me which tables and columns I should use to answer.".
If you can generate a SQL query, ONLY return the SQL query. Do not include any natural language.  

You are using sakila database.
Tables, primary keys, and columns (column name and type) for the database: 
{schema_info}

"""
print(prompt_str,end="\n\n")

