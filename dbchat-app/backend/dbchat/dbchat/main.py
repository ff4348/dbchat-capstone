import re
import os
from joblib import load
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from langchain_openai import ChatOpenAI
from assets.assets import ask_chatgpt, execute_query

# Instantiate model using LangChain integration
@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialize variables
    openai_api_key = ""
    config = {
    'host': '172.17.0.2',
    'port': 3306,
    'usr': 'newuser',
    'pwd': 'newpassword',
    'db': 'sakila'
    }
    connection_str = f"mysql+pymysql://{config.get('usr')}:{config.get('pwd')}@{config.get('host')}:{config.get('port')}/{config.get('db')}"

    # Instantiate model using LangChain
    global llm
    llm = ChatOpenAI(openai_api_key=openai_api_key)
    print('Model used:', llm.model_name)

    # Define your SQLAlchemy engine and session
    global engine
    global SessionLocal
    engine = create_engine(connection_str)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield

    # Clean up the ML models and release the resources
    print("All done!")




app = FastAPI(lifespan=lifespan)
# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)



# Define API input and responses using Pydantic models
class UserQuestion(BaseModel):
    """Data model to define the user question"""
    model_config = ConfigDict(extra="forbid")
    question: str

class QueryResult(BaseModel):
    """Data model to define query result output"""
    model_config = ConfigDict(extra="forbid")
    description: str
    records_returned: int
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
    sql_query = ask_chatgpt(user_question.question,llm)

    try:
        db = SessionLocal()
        return execute_query(db, sql_query)
    except Exception as e:
        print("Unable to connect to the database...",str(e))
        return {'description':'Unable to connect to the database... ' + str(e), 'records_returned':0, 'csv_download_link':''}
    finally:
        db.close()

@app.post("/queries", response_model=QueryResults)
async def bulk_query_database(user_questions: UserQuestions):
    sql_queries = [ask_chatgpt(user_question.question,llm) for user_question in user_questions]

    try:
        db = SessionLocal()
        return [execute_query(db, sql_query) for sql_query in sql_queries]
    except Exception as e:
        print("Unable to connect to the database...",str(e))
        return [{'description':'Unable to connect to the database... ' + str(e), 'records_returned':0, 'csv_download_link':''}]
    finally:
        db.close()

    
@app.get("/health")
async def health():
    return {"status": "healthy"}
# sanity check
@app.get("/hello")
async def hello(name: str):
    return {"message": f"Hello {name}"}
