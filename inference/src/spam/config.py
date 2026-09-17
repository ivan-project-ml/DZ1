from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_path: str = 'artifacts/model.joblib'
    database_url: str|None = 'postgresql://spam_user:spam123@localhost:5432/spam'
    log_level: str = 'INFO'

    model_config = {"env_file": ".env"}

settings = Settings()