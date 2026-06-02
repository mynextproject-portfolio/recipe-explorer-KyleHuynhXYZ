from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import json

import httpx

try:
    import redis
except Exception:
    redis = None

API_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
TIMEOUT_SECONDS = 5.0
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours


class ExternalAPIError(Exception):
    pass


def _build_external_id(meal_id: str) -> str:
    return f"external-{meal_id}"


def _parse_ingredients(meal_data: Dict[str, Any]) -> List[str]:
    ingredients: List[str] = []
    for index in range(1, 21):
        ingredient = meal_data.get(f"strIngredient{index}")
        measure = meal_data.get(f"strMeasure{index}")
        if ingredient and ingredient.strip():
            ingredient_text = ingredient.strip()
            if measure and measure.strip():
                ingredients.append(f"{measure.strip()} {ingredient_text}")
            else:
                ingredients.append(ingredient_text)
    return ingredients


def _parse_tags(tag_string: Optional[str]) -> List[str]:
    if not tag_string:
        return []
    return [tag.strip() for tag in tag_string.split(",") if tag.strip()]


def _transform_meal(meal_data: Dict[str, Any]) -> Dict[str, Any]:
    meal_id = meal_data.get("idMeal")
    if not meal_id:
        raise ExternalAPIError("External recipe is missing an ID")

    title = (meal_data.get("strMeal") or "").strip()
    description = (meal_data.get("strInstructions") or "").strip()
    cuisine = (
        meal_data.get("strArea") or meal_data.get("strCategory") or "Unknown"
    ).strip()
    ingredients = _parse_ingredients(meal_data)
    instructions_text = (meal_data.get("strInstructions") or "").strip()
    instructions = [instructions_text] if instructions_text else []
    tags = _parse_tags(meal_data.get("strTags"))

    return {
        "id": _build_external_id(meal_id),
        "title": title,
        "description": description,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "instructions": instructions,
        "servings": 1,
        "tags": tags,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "source": "external",
    }


def _fetch_json(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        response = httpx.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as exc:
        raise ExternalAPIError(f"External API request failed: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise ExternalAPIError(
            f"External API returned HTTP {exc.response.status_code}"
        ) from exc
    except ValueError as exc:
        raise ExternalAPIError(f"External API returned invalid JSON: {exc}") from exc


def search_meals(query: str) -> List[Dict[str, Any]]:
    # Caching: try Redis first
    try:
        client = _get_redis_client()
    except Exception:
        client = None

    cache_key = f"meal_search:{query.lower()}"
    if client:
        try:
            raw = client.get(cache_key)
            if raw:
                _increment_cache_hit()
                data = json.loads(raw)
                return data
        except Exception:
            # swallow cache errors and continue to fetch
            pass

    payload = _fetch_json("search.php", {"s": query})
    meals = payload.get("meals")
    if not meals:
        result = []
    else:
        result = [_transform_meal(meal) for meal in meals if isinstance(meal, dict)]

    if client:
        try:
            client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(result))
            _increment_cache_miss()
        except Exception:
            pass

    return result


def get_meal_by_id(meal_id: str) -> Optional[Dict[str, Any]]:
    try:
        client = _get_redis_client()
    except Exception:
        client = None

    cache_key = f"meal_id:{meal_id}"
    if client:
        try:
            raw = client.get(cache_key)
            if raw:
                _increment_cache_hit()
                return json.loads(raw)
        except Exception:
            pass

    payload = _fetch_json("lookup.php", {"i": meal_id})
    meals = payload.get("meals")
    if not meals:
        return None
    first_meal = meals[0]
    if not isinstance(first_meal, dict):
        return None
    transformed = _transform_meal(first_meal)

    if client:
        try:
            client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(transformed))
            _increment_cache_miss()
        except Exception:
            pass

    return transformed


# Redis client and simple metrics
_redis_client = None
cache_hits = 0
cache_misses = 0


def _get_redis_client():
    global _redis_client
    if _redis_client:
        return _redis_client
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if redis is None:
        raise RuntimeError("redis package not available")
    _redis_client = redis.Redis.from_url(url, decode_responses=True)
    return _redis_client


def _increment_cache_hit():
    global cache_hits
    cache_hits += 1


def _increment_cache_miss():
    global cache_misses
    cache_misses += 1
