from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")
    SCYLLA_HOST: str = "localhost"
    SCYLLA_PORT: int = 9042
    SCYLLA_KEYSPACE: str = "fleet_tracker"
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    COMPANY_ID: str = "COMP_HCM_01"

settings = Settings()
