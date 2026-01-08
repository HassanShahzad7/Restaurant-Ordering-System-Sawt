"""Configuration management for Sawt using pydantic-settings."""

from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql://sawt:sawt_password@localhost:5432/sawt",
        description="PostgreSQL connection URL",
    )
    test_database_url: str = Field(
        default="postgresql://sawt:sawt_password@localhost:5432/sawt_test",
        description="PostgreSQL connection URL for tests",
    )
    db_pool_min_size: int = Field(default=5, description="Minimum database pool size")
    db_pool_max_size: int = Field(default=20, description="Maximum database pool size")

    # OpenRouter API Configuration
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key",
    )
    openrouter_model: str = Field(
        default="openai/gpt-5-mini",
        description="OpenRouter model to use",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )

    # Pinecone Configuration
    pinecone_api_key: str = Field(
        default="",
        description="Pinecone API key",
    )
    pinecone_index: str = Field(
        default="sawt-menu",
        description="Pinecone index name for menu items",
    )
    pinecone_environment: str = Field(
        default="us-east-1",
        description="Pinecone environment",
    )

    # Application Settings
    delivery_fee: Decimal = Field(
        default=Decimal("15.00"),
        description="Fixed delivery fee in SAR",
    )
    opening_hour: int = Field(
        default=9,
        description="Restaurant opening hour (24h format)",
    )
    closing_hour: int = Field(
        default=3,
        description="Restaurant closing hour (24h format, cross-midnight)",
    )
    session_expiry_hours: int = Field(
        default=2,
        description="Session expiry time in hours",
    )
    timezone: str = Field(
        default="Asia/Riyadh",
        description="Restaurant timezone",
    )

    # Tax Configuration
    tax_included: bool = Field(
        default=True,
        description="Whether prices are tax-inclusive",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return "localhost" not in self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
