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
from dbchat.assets.assets import t2SQL_gpt, t2SQL_sqlcoder15B, execute_query, get_schema
import boto3

# Instantiate model using LangChain integration
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize Secerts
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    global db_name
    db_name = os.getenv("PRIM_DB_NAME")
    connection_str = f"mysql+pymysql://{os.getenv('PRIM_DB_USER')}:{os.getenv('PRIM_DB_PWD')}@{os.getenv('PRIM_DB_HOST')}:{os.getenv('PRIM_DB_PORT')}/{db_name}"

    # Create a SageMaker runtime client object using your IAM role ARN
    global runtime
    runtime = boto3.client('sagemaker-runtime',
                       aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                       aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                       region_name=os.getenv("AWS_REGION"))

    # Instantiate model using LangChain
    global llm
    llm = ChatOpenAI(openai_api_key=openai_api_key)
    print('Model used:', llm.model_name)
    print(os.path.dirname(os.path.realpath(__file__)))

    # Define your SQLAlchemy engine and session
    global engine
    global SessionLocal
    engine = create_engine(connection_str, connect_args={'init_command': 'SET SESSION max_execution_time=20000'})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("SQL Alchemy engine and session defined...")

    # Retrieve database schema
    global schema_info
    global schema_dict
    schema_info, schema_dict = get_schema(engine)

    yield

    # Clean up the ML models and release the resources
    print("All done!")




app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:8501",
    "https://localhost:8501"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    sql_query = t2SQL_sqlcoder15B(runtime,user_question,schema_info)

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

# @app.post("/queries", response_model=QueryResults)
# async def bulk_query_database(user_questions: UserQuestions):
#     try:
#         db = SessionLocal()
#         # Use model to translate question to a SQL query
#         sql_queries = [t2SQL_gpt(user_question.question, llm, schema_info, db_name) for user_question in user_questions.questions]
        
#         # Execute queries and gather results
#         query_results = [execute_query(db, sql_query, question, llm) for sql_query in sql_queries]

#         # Return the results as a QueryResults object
#         return QueryResults(results=query_results)
#     except Exception as e:
#         print("Unable to connect to the database...", str(e))
#         raise HTTPException(status_code=500, detail="An error occurred while processing the request. Please try again later.")
#     finally:
#         db.close()

@app.get("/health")
async def health():
    return {"status": "healthy"}
@app.get("/hello")
async def hello(name: str):
    return {"message": f"Hello {name}"}
