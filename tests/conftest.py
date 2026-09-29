import os
os.environ["DATABASE_URL"]="sqlite:///./test_restaurant.db"
os.environ["OPENAI_API_KEY"]=""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import engine, SessionLocal
from app.database.models import Base
from app.database.seed import seed_orders

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    db=SessionLocal(); seed_orders(db); db.close()
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client():
    with TestClient(app) as c: yield c
