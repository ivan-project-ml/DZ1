import os

import psycopg
import pytest

DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="нужен Postgres: задайте DATABASE_URL"),
]


def test_prediction_is_logged(client, good_row):
    body = client.post("/v1/predict", json=good_row).json()

    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT model_version, label, features->>'text', status_code "
            # ⚠️ ПРОВЕРЬТЕ: имя столбца с кодом ответа — "response_code" или как он у вас называется
            "FROM predictions WHERE request_id = %s",
            (body["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == body["model_version"]
    assert row[2] == good_row["text"]
    assert row[3] == 200


def test_bad_request_logs_422(client):
    resp = client.post("/v1/predict", json={"garbage": True})
    assert resp.status_code == 422

    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT status_code"
            "FROM predictions WHERE request_id = %s",
            (resp["request_id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == 422