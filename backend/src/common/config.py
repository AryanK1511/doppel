from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "PROD"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = AppSettings()
