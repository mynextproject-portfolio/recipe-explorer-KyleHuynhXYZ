from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

API_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
TIMEOUT_SECONDS = 5.0


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
    cuisine = (meal_data.get("strArea") or meal_data.get("strCategory") or "Unknown").strip()
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
        "source": "external"
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
        raise ExternalAPIError(f"External API returned HTTP {exc.response.status_code}") from exc
    except ValueError as exc:
        raise ExternalAPIError(f"External API returned invalid JSON: {exc}") from exc


def search_meals(query: str) -> List[Dict[str, Any]]:
    payload = _fetch_json("search.php", {"s": query})
    meals = payload.get("meals")
    if not meals:
        return []
    return [_transform_meal(meal) for meal in meals if isinstance(meal, dict)]


def get_meal_by_id(meal_id: str) -> Optional[Dict[str, Any]]:
    payload = _fetch_json("lookup.php", {"i": meal_id})
    meals = payload.get("meals")
    if not meals:
        return None
    first_meal = meals[0]
    if not isinstance(first_meal, dict):
        return None
    return _transform_meal(first_meal)
