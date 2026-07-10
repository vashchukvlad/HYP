from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_impact"
    jwt_secret: str = "development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
