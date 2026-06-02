from typing import Optional

from app.protocols import StorageProtocol, ExternalClientProtocol, CacheClientProtocol
from app.services.storage import recipe_storage
from app.services import themealdb


def get_storage() -> StorageProtocol:
    """Dependency provider for the recipe storage layer.

    Returns the concrete in-memory storage implementation that satisfies StorageProtocol.
    """
    return recipe_storage


def get_external_client() -> ExternalClientProtocol:
    """Dependency provider for the external recipe API client.

    Returns the TheMealDB adapter that satisfies ExternalClientProtocol.
    """
    return themealdb


def get_cache_client() -> Optional[CacheClientProtocol]:
    """Dependency provider for a cache client (Redis).

    May return None if redis is not available or not initialized.
    """
    try:
        return themealdb._get_redis_client()
    except Exception:
        return None
