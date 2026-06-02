from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    app_name: str = "Phantom Protocol"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    demo_mode: bool = Field(default=True, env="DEMO_MODE")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://phantom:phantom@localhost:5432/phantom",
        env="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://phantom:phantom@localhost:5432/phantom",
        env="DATABASE_URL_SYNC",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Gemini
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = "gemini-1.5-flash"

    # Mesh Network
    mesh_node_id: str = Field(default_factory=lambda: f"node-{secrets.token_hex(4)}", env="MESH_NODE_ID")
    mesh_network_url: str = Field(default="wss://phantom-mesh.railway.app", env="MESH_NETWORK_URL")
    mesh_broadcast_interval: int = 5

    # JWT
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Sentinel
    attack_confidence_threshold: float = 0.65
    phantom_mode_timeout: int = 300

    # Sentence Transformers
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
