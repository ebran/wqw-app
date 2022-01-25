"""App settings"""
from typing import Optional
from functools import lru_cache

from pydantic import BaseSettings

from arq.connections import RedisSettings


# pylint: disable=too-few-public-methods
class _RedisSettings(BaseSettings):
    """Read Redis settings."""

    host: str = "localhost"
    port: int = 6379
    database: int = 0

    class Config:
        """Additional configuration."""

        env_file: str = ".env"
        env_prefix: str = "redis_"


@lru_cache
def get_redis_settings(_settings: Optional[_RedisSettings] = None) -> RedisSettings:
    """Redis settings."""
    if _settings is None:
        return RedisSettings(**_RedisSettings().dict())
    return RedisSettings(**_settings.dict())
