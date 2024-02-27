import random
from fastapi.testclient import TestClient
from dbchat.main import app

client = TestClient(app)

def test_query_basic():
    data = {
        "question": "How many people are younger than 43?"
    }
    response = client.post(
        "/query",
        json=data,
    )
    assert response.status_code == 200


def test_query_extra_feature():
    data = {
        "question": "How many people are younger than 43?",
        "q": "How many people are younger than 43?"
    }

    response = client.post(
        "/query",
        json=data,
    )
    assert response.status_code == 422

def test_query_bad_type():
    data = {
        "MedInc": 1
    }

    response = client.post(
        "/query",
        json=data,
    )
    assert response.status_code == 422