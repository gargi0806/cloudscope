from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_live_and_ready():
    assert client.get('/health/live').json() == {'status': 'alive'}
    assert client.get('/health/ready').status_code == 200


def test_status_has_real_runtime_fields():
    response = client.get('/api/v1/status')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'operational'
    assert body['uptime_seconds'] >= 0
    assert body['environment']
    assert body['timestamp'].endswith('+00:00')


def test_metrics_exposed():
    res = client.get('/metrics')
    assert res.status_code == 200
    assert 'cloudscope_http_requests_total' in res.text
    assert 'cloudscope_http_request_duration_seconds' in res.text


def test_security_headers_and_homepage():
    response = client.get('/')
    assert response.status_code == 200
    assert 'CloudScope' in response.text
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'


def test_404_is_json():
    response = client.get('/not-a-route')
    assert response.status_code == 404
    assert response.json() == {'error': 'not_found'}
