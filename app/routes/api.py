from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Any, List, Optional
import json
import time

from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.deps import get_storage, get_external_client
from app.protocols import ExternalClientProtocol
from app.services.themealdb import ExternalAPIError
from app.validators import validate_import_recipes
from pydantic import ValidationError as PydanticValidationError

# --- PROMETHEUS METRIC ---
from app.metrics import RECIPE_SEARCHES
# -------------------------

router = APIRouter(prefix="/api")

# Constants
MAX_FILE_SIZE = 1_000_000  # 1MB


def create_error_response(
    status_code: int, field: str, message: str, details: Optional[List[dict]] = None
) -> dict:
    """Create a standardized error response."""
    response = {"error": message, "field": field, "status_code": status_code}
    if details:
        response["details"] = details
    return response


def serialize_recipe(recipe: Recipe, source: str = "internal") -> dict:
    payload = recipe.model_dump(mode="json")
    payload["source"] = source
    return payload


@router.get("/recipes")
def get_recipes(
    search: Optional[str] = Query(None, max_length=200),
    storage: Any = Depends(get_storage),
    external_client: ExternalClientProtocol = Depends(get_external_client),
):
    """Get all recipes or search by title."""
    
    # --- PROMETHEUS METRIC: Track Popularity ---
    if search and search.strip():
        RECIPE_SEARCHES.labels(query=search.lower().strip()).inc()
    # -------------------------------------------

    try:
        request_start = time.monotonic()
        internal_results = []
        external_results = []
        external_error = None
        internal_time_ms = 0.0
        external_time_ms = None

        internal_start = time.monotonic()
        if search and search.strip():
            internal_results = storage.search_recipes(search)
        else:
            internal_results = storage.get_all_recipes()
        internal_time_ms = (time.monotonic() - internal_start) * 1000

        if search and search.strip():
            external_start = time.monotonic()
            try:
                external_results = external_client.search_meals(search)
            except ExternalAPIError as exc:
                external_error = str(exc)
            finally:
                external_time_ms = (time.monotonic() - external_start) * 1000

        response_recipes = [
            serialize_recipe(recipe) for recipe in internal_results
        ] + external_results
        result = {
            "recipes": response_recipes,
            "count": len(response_recipes),
            "metrics": {
                "internal_ms": round(internal_time_ms, 2),
                "external_ms": round(external_time_ms, 2)
                if external_time_ms is not None
                else None,
                "total_ms": round((time.monotonic() - request_start) * 1000, 2),
                "source_counts": {
                    "internal": len(internal_results),
                    "external": len(external_results),
                },
                "cache_hits": getattr(external_client, "cache_hits", 0),
                "cache_misses": getattr(external_client, "cache_misses", 0),
            },
        }
        if external_error:
            result["external_error"] = external_error
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                500, "internal", f"Failed to retrieve recipes: {str(e)}"
            ),
        )

@router.get("/recipes/search")
def search_recipes(
    q: Optional[str] = Query(None, max_length=200),
    storage: Any = Depends(get_storage),
    external_client: ExternalClientProtocol = Depends(get_external_client),
):
    """Search recipes using the legacy /recipes/search?q=... route."""
    return get_recipes(search=q, storage=storage, external_client=external_client)

@router.get("/recipes/export")
def export_recipes(storage: Any = Depends(get_storage)):
    try:
        recipes = storage.get_all_recipes()
        recipes_dict = [
            serialize_recipe(recipe, source="internal") for recipe in recipes
        ]
        return {
            "recipes": recipes_dict,
            "count": len(recipes_dict),
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Export failed: {str(e)}"),
        )

@router.get("/recipes/internal/{recipe_id}")
def get_internal_recipe(recipe_id: str, storage: Any = Depends(get_storage)):
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty"),
        )
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                404, "recipe_id", f"Internal recipe with ID '{recipe_id}' not found"
            ),
        )
    return serialize_recipe(recipe, source="internal")

@router.get("/recipes/external/{recipe_id}")
def get_external_recipe(recipe_id: str, external_client: Any = Depends(get_external_client)):
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty"),
        )
    try:
        recipe = external_client.get_meal_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    404, "recipe_id", f"External recipe with ID '{recipe_id}' not found"
                ),
            )
        return recipe
    except ExternalAPIError as exc:
        raise HTTPException(
            status_code=502, detail=create_error_response(502, "external_api", str(exc))
        )

@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str, storage: Any = Depends(get_storage)):
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty"),
        )
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                404, "recipe_id", f"Recipe with ID '{recipe_id}' not found"
            ),
        )
    return serialize_recipe(recipe, source="internal")

@router.post("/recipes")
def create_recipe(recipe: RecipeCreate, storage: Any = Depends(get_storage)):
    try:
        new_recipe = storage.create_recipe(recipe)
        return serialize_recipe(new_recipe, source="internal")
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            error_details.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                422, "validation", "Recipe data validation failed", error_details
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                500, "internal", f"Failed to create recipe: {str(e)}"
            ),
        )

@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe: RecipeUpdate, storage: Any = Depends(get_storage)):
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty"),
        )
    try:
        existing_recipe = storage.get_recipe(recipe_id)
        if not existing_recipe:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    404, "recipe_id", f"Recipe with ID '{recipe_id}' not found"
                ),
            )
        updated_recipe = storage.update_recipe(recipe_id, recipe)
        return serialize_recipe(updated_recipe, source="internal")
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            error_details.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                422, "validation", "Recipe data validation failed", error_details
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                500, "internal", f"Failed to update recipe: {str(e)}"
            ),
        )

@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str, storage: Any = Depends(get_storage)):
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty"),
        )
    success = storage.delete_recipe(recipe_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(
                404, "recipe_id", f"Recipe with ID '{recipe_id}' not found"
            ),
        )
    return {
        "message": "Recipe deleted successfully",
        "recipe_id": recipe_id,
        "status": "success",
    }

@router.post("/recipes/import")
async def import_recipes(file: UploadFile = File(...), storage: Any = Depends(get_storage)):
    if not file:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "file", "No file provided"),
        )
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "filename", "File must have a name"),
        )
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                400, "filename", "File must be a JSON file (.json)"
            ),
        )
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(400, "file_content", "File is empty"),
            )
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    400,
                    "file_size",
                    f"File too large. Maximum size is {MAX_FILE_SIZE / 1_000_000}MB",
                ),
            )
        try:
            recipes_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    400, "json_format", f"Invalid JSON format: {str(e)}"
                ),
            )
        is_valid, validation_errors = validate_import_recipes(recipes_data)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    422,
                    "schema_validation",
                    "One or more recipes failed schema validation",
                    validation_errors[:10],
                ),
            )
        count = storage.import_recipes(recipes_data)
        return {
            "message": f"Successfully imported {count} recipes from {file.filename}",
            "count": count,
            "filename": file.filename,
            "status": "success",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Import failed: {str(e)}"),
        )