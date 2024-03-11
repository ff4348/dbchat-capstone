import random
from fastapi.testclient import TestClient
from dbchat.main import app

client = TestClient(app)


def test_bulk_queries_basic():
    data = [{
      "question": "How many people are younger than 43?"
    },
    {
      "question": "How many people are older than 20?"
    }]
    response = client.post(
        "/queries",
        json={"questions": data}
    )
    assert response.status_code == 200

def test_bulk_queries_extra_feature():
    data = [{
      "question": "How many people are younger than 43?",
      "question2": "How many heads of the departments are older than 56 ?"
    },
    {
        "question": "How many heads of the departments are older than 56 ?"
    }]

    response = client.post(
        "/queries",
        json={"questions": data}
    )
    assert response.status_code == 422


def test_bulk_queries_missing_feature():
    data = [{
        "MedInc": "How many departments are there?",
    },
    {
        "question": "How many heads of the departments are older than 56 ?"
    }]

    response = client.post(
        "/queries",
        json={"questions": data}
    )
    assert response.status_code == 422


def test_bulk_queries_bad_type():
    data = [{
        "question": 1,
    },
    {
        "question": "2"
    }]

    response = client.post(
        "/queries",
        json={"questions":data}
    )
    assert response.status_code == 422

def test_bulk_queries_bad_parameters():
    data = [{
        "question": None
    }]
    response = client.post(
        "/queries",
        json={"questions":data}
    )
    assert response.status_code == 422
    