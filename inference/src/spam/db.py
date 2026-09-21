import psycopg
from psycopg.types.json import Json

from spam.config import settings

DDL = """
CREATE TABLE IF NOT EXISTS predictions (

    request_id      uuid PRIMARY KEY,
    ts      timestamptz NOT NULL DEFAULT now(),
    model_version       text,
    features        jsonb,
    label       text,
    latency_ms real,
    status_code integer NOT NULL
)
"""

def init() -> None:
    if not settings.database_url:
        print("DATABASE_URL не задан")
        return

    try:
        with psycopg.connect(settings.database_url) as conn:
            print("✓ PostgreSQL: подключение успешно")
            conn.execute(DDL)
            print("✓ DDL выполнен")
    except psycopg.Error as e:
        print(f"✗ PostgreSQL: ошибка подключения: {e}")


def save_prediction(request_id : str, features : dict, label : str, model_version : str, latency_ms : float, status_code: int) -> None:
    if not settings.database_url:
        return
    with psycopg.connect(settings.database_url) as conn:
            conn.execute(
            "INSERT INTO predictions (request_id, model_version, features, label, latency_ms, status_code) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (request_id, model_version, Json(features), label, latency_ms, status_code),
        )
