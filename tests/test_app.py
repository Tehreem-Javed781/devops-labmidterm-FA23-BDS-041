"""Tests run by Jenkins after every retrain."""
import hashlib
import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
CONFIG = json.loads(Path('config.json').read_text())
DATASET = Path('dataset/train.csv')


def test_health_ok():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_metrics_has_required_fields():
    m = client.get('/metrics').json()
    for key in ['student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha']:
        assert key in m, f'missing {key}'
    assert m['student_id'] == CONFIG['student_id']


def test_metrics_match_latest_dataset():
    m = client.get('/metrics').json()
    assert m['training_rows'] == len(pd.read_csv(DATASET))
    assert m['model_version'] == hashlib.sha256(DATASET.read_bytes()).hexdigest()[:12]


def test_model_is_accurate_enough():
    assert client.get('/metrics').json()['accuracy'] >= 0.60


def test_predict_returns_valid_output():
    record = {feature: 0.5 for feature in CONFIG['features']}
    r = client.post('/predict', json={'records': [record, record]})
    assert r.status_code == 200
    body = r.json()
    assert len(body['predictions']) == 2
    assert all(p in (0, 1) for p in body['predictions'])
    assert all(0.0 <= p <= 1.0 for p in body['probabilities'])


def test_predict_rejects_empty_request():
    r = client.post('/predict', json={'records': []})
    assert r.status_code == 422
