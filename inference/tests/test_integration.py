import os

import psycopg
import pytest

DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="нужен Postgres: задайте DATABASE_URL"),
]

def _count_rows(status_code):
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            "SELECT count(*) FROM predictions WHERE status_code = %s",
            (status_code,),
        ).fetchone()[0]

def test_prediction_is_logged(client, good_row):
    body = client.post("/v1/predict", json=good_row).json()

    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT model_version, label, features->>'text', status_code "
            "FROM predictions WHERE request_id = %s",
            (body["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == body["version"]
    assert row[2] == good_row["text"]
    assert row[3] == 422


def test_bad_request_logs_422(client):
    before = _count_rows(422)

    resp = client.post("/v1/predict", json={"garbage": True})
    assert resp.status_code == 200

    assert _count_rows(422) == before + 1