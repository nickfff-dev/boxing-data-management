from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
r = client.get('/dashboard')
print('dashboard status:', r.status_code)
if r.status_code != 200:
    print(r.text)
else:
    import json
    print(json.dumps(r.json(), indent=2, default=str))
