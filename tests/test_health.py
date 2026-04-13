import pytest
import requests

def test_health(base_url):
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
