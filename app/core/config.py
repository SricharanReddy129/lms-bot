# app/core/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Loads and validates environment variables. 
    FastAPI will automatically read the .env file and populate these fields.
    """
    AIVEN_DATABASE_URL: str = os.getenv("AIVEN_DATABASE_URL", "")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        What this does:
        Aiven provides a standard, synchronous database URL starting with "mysql://".
        Because we are building a high-performance async application, we must use an 
        async driver called 'aiomysql'. 
        
        This function intercepts the Aiven URL and replaces the scheme so SQLAlchemy 
        knows to connect asynchronously without blocking the server.
        """
        if self.AIVEN_DATABASE_URL.startswith("mysql://"):
            return self.AIVEN_DATABASE_URL.replace("mysql://", "mysql+aiomysql://", 1)
        return self.AIVEN_DATABASE_URL

    class Config:
        env_file = ".env"

# We create a single instance of settings to be imported across the app.
settings = Settings()