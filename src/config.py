from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: SecretStr
    TEST_DATABASE_URL: SecretStr = SecretStr("")

    # Auth
    SECRET_JWT_SIGNING_KEY: SecretStr
    JWT_EXPIRATION_TIME_IN_HOURS: int = 24

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_AS_JSON: bool = False


config = Config()


def get_database_url() -> str:
    return config.DATABASE_URL.get_secret_value()
