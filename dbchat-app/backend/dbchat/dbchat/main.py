import re
from dotenv import load_dotenv
import os
from joblib import load
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from langchain_openai import ChatOpenAI
from dbchat.assets.assets import t2SQL_gpt, t2SQL_sqlcoder, execute_query, get_schema
import boto3

# Instantiate model using LangChain integration
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize Secerts
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print("Fetched OPENAI_API_KEY")
    global db_name
    db_name = os.getenv("MYSQL_DB")
    print("Fetched MYSQL_DB:",db_name)
    connection_str = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_UPASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{db_name}"
    print("Connection string created...")
    # Create a SageMaker runtime client object using your IAM role ARN
    global runtime
    runtime = boto3.client('sagemaker-runtime',
                       aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                       aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                       region_name=os.getenv("AWS_REGION"))
    print("AWS Sagemaker runtime established...")

    # Instantiate model using LangChain
    global llm
    llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-4", temperature=0)
    print('Model used:', llm.model_name,)
    print(os.path.dirname(os.path.realpath(__file__)))

    # Define your SQLAlchemy engine and session
    global engine
    global SessionLocal
    engine = create_engine(connection_str, connect_args={'init_command': 'SET SESSION max_execution_time=20000'})
    print("Engine created!")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("SQL Alchemy engine and session defined...")

    # Retrieve database schema
    global schema_info
    global schema_dict
    schema_info, schema_dict = get_schema(engine)
    print("Fetched schema")

    yield

    # Clean up the ML models and release the resources
    print("All done!")




app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Define API input and responses using Pydantic models
class UserQuestion(BaseModel):
    """Data model to define the user question"""
    model_config = ConfigDict(extra="forbid")
    question: str

class QueryResult(BaseModel):
    """Data model to define query result output"""
    model_config = ConfigDict(extra="forbid")
    query: str
    user_friendly: str
    csv_download_link: str

class UserQuestions(BaseModel):
    """Data model to define user questions in bulk"""
    model_config = ConfigDict(extra="forbid")
    questions: List[UserQuestion]

class QueryResults(BaseModel):
    """Data model to define query results in bulk"""
    model_config = ConfigDict(extra="forbid")
    results: List[QueryResult]

@app.post("/query", response_model=QueryResult)
async def query_database(user_question: UserQuestion):
    print('question asked:',user_question)
    sql_query = t2SQL_gpt(user_question.question,llm,schema_info,db_name)

    try:
        db = SessionLocal()
        print("SessionLocal called...")
        return execute_query(db, sql_query, user_question.question, llm)
    except Exception as e:
        print("Unable to connect to the database...",str(e))
        return {'query':'No query generated...' + str(e), 'user_friendly':'**ERROR: Unable to connect to the database... ', 'csv_download_link':''}
    finally:
        db.close()


@app.post("/sqlcoder-query", response_model=QueryResult)
async def query_database(user_question: UserQuestion):
    print('question asked:',user_question)
    sql_query = t2SQL_sqlcoder(runtime,user_question,schema_info)

    try:
        db = SessionLocal()
        print("SessionLocal called...")
        return execute_query(db, sql_query, user_question.question, llm)
    except Exception as e:
        print("Unable to connect to the database...",str(e))
        return {'query':'No query generated...' + str(e), 'user_friendly':'**ERROR: Unable to connect to the database... ', 'csv_download_link':''}
    finally:
        db.close()

@app.get("/schema")
async def query_database():
    print(schema_dict)
    return schema_dict

@app.get("/health")
async def health():
    return {"status": "healthy"}

