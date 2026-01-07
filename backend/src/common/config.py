from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "PROD"
    GEMINI_API_KEY: str
    TAVILY_API_KEY: str
    ELEVENLABS_API_KEY: str
    FAL_KEY: str
    ASSEMBLYAI_API_KEY: str
    MONGODB_URI: str
    GCP_BUCKET_NAME: str
    GCP_SERVICE_ACCOUNT_KEY: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = AppSettings()
