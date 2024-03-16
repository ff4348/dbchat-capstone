import re
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
from dbchat.assets.assets import t2SQL_gpt, execute_query, get_schema

# Instantiate model using LangChain integration
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize variables
    openai_api_key = ""
    config = {
    'host': '172.18.0.3',
    'port': 3306,
    'usr': 'newuser',
    'pwd': 'newpassword',
    'db': 'sakila'
    }
    global db_name
    db_name = config.get('db')
    connection_str = f"mysql+pymysql://{config.get('usr')}:{config.get('pwd')}@{config.get('host')}:{config.get('port')}/{config.get('db')}"

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
    schema_info = get_schema(engine)

    yield

    # Clean up the ML models and release the resources
    print("All done!")




app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "localhost:3000"
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
