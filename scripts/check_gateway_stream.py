from api.main import app
from fastapi.testclient import TestClient
import json

# Setup a temporary testing DB and override get_db dependency like tests do
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/eaimos_test"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database.session import get_db
from api.models import Base

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if missing
Base.metadata.create_all(bind=engine)

def _get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _get_db

client = TestClient(app)

print("== GET /api/v1/ai/models/")
res = client.get("/api/v1/ai/models/")
print(res.status_code)
try:
    print(json.dumps(res.json(), indent=2)[:4000])
except Exception as e:
    print("failed to json", e)

print('\n== CREATE conversation')

# If unauthenticated, register and login a test user
if res.status_code == 401:
    print('\n== Attempting to register a test user and login')
    email = f'test-cli-{int(__import__("time").time())}@example.com'
    pw = 'TestPassword123!'
    reg = client.post('/api/v1/auth/register', json={'email': email, 'password': pw, 'full_name': 'Test CLI'})
    print('register', reg.status_code)
    login = client.post('/api/v1/auth/login', data={'username': email, 'password': pw})
    print('login', login.status_code)
    try:
        tokens = login.json()
        access = tokens.get('access_token')
    except Exception:
        access = None
    headers = {}
    if access:
        headers['Authorization'] = f'Bearer {access}'
    # retry models with auth
    res = client.get('/api/v1/ai/models/', headers=headers)
    print('models after auth', res.status_code)
    try:
        print(json.dumps(res.json(), indent=2)[:4000])
    except Exception:
        pass

    create = client.post('/api/v1/chat/conversations/', json={'title': 'test-cli', 'model_name': 'openai/gpt-oss-120b', 'provider_name': 'groq'}, headers=headers)
    print('create', create.status_code)
    try:
        print(create.json())
    except Exception:
        print('create no json')
    conv_id = create.json().get('id') if create.status_code == 201 else None
else:
    create = client.post('/api/v1/chat/conversations/', json={'title': 'test-cli', 'model_name': 'openai/gpt-oss-120b', 'provider_name': 'groq'})
    print(create.status_code)
    print(create.json())
    conv_id = create.json().get('id')

if conv_id:
    print('\n== POST stream')
    # Ensure we include organization header when calling stream
    org_id = create.json().get('organization_id') if create is not None else None
    if org_id:
        headers['X-Organization-ID'] = org_id

    resp = client.post(f'/api/v1/chat/conversations/{conv_id}/stream', json={
        'content': 'Hello from test',
        'model_name': 'openai/gpt-oss-120b',
        'prompt_id': None,
        'system_prompt': None,
        'rag_enabled': False
    }, headers=headers)
    print('status', resp.status_code)
    text = resp.text or ''
    print('body snippet:', text[:2000])
else:
    print('no conv id')
