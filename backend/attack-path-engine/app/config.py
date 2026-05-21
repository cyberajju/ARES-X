"""Configuration for the Attack Path Engine."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    host: str = "0.0.0.0"
    port: int = 8082
    log_level: str = "info"
    graph_engine_url: str = "http://localhost:50051"
    asset_service_url: str = "http://localhost:8081"
    simulation_iterations: int = 10000
    max_path_depth: int = 10

    class Config:
        env_prefix = "ATTACK_PATH_"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
