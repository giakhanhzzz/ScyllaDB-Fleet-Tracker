import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SCYLLA_HOST: str = os.getenv("SCYLLA_HOST", "localhost")
    SCYLLA_PORT: int = int(os.getenv("SCYLLA_PORT", "9042"))
    SCYLLA_KEYSPACE: str = os.getenv("SCYLLA_KEYSPACE", "fleet_tracker")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_fleet_tracker_scylladb_nosql_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    COMPANY_ID: str = "COMP_HCM_01"

    class Config:
        env_file = ".env"

settings = Settings()
