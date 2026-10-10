from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/care_cloud"
    vapi_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
