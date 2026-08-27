from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    token = client.post('/api/v1/auth/login', json={'username':'admin@jaldrishti.local','password':'Admin@12345'}).json()['data']['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    run = client.post('/api/v1/nowcasts', headers=headers, json={'horizon_min': 60}).json()['data']['run_id']
    assert client.get(f'/api/v1/map/risk?run_id={run}', headers=headers).status_code == 200
    route = client.post('/api/v1/routes', headers=headers, json={'run_id':run,'origin':{'latitude':18.52,'longitude':73.856},'destination':{'latitude':18.559,'longitude':73.786}})
    assert route.status_code == 201
    assert client.get(f'/api/v1/shelters/recommendations?latitude=18.52&longitude=73.856&run_id={run}', headers=headers).status_code == 200
    assert client.get('/api/v1/alerts', headers=headers).status_code == 200
    print({'run_id': run, 'route_status': route.json()['data']['route_status']})
