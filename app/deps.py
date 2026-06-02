from typing import Any, Optional

from app.services.storage import recipe_storage
from app.services import themealdb


def get_storage() -> Any:
    """Dependency provider for the recipe storage layer."""
    return recipe_storage


def get_external_client() -> Any:
    """Dependency provider for TheMealDB adapter.

    Returns the module-like client that exposes `search_meals` and `get_meal_by_id`.
    """
    return themealdb


def get_cache_client() -> Optional[Any]:
    """Dependency provider for a cache client (Redis). May raise if redis not available.

    Callers should handle absence of a cache client.
    """
    try:
        return themealdb._get_redis_client()
    except Exception:
        return None
