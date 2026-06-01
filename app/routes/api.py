from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage
from app.validators import validate_recipe_create, validate_recipe_update, validate_import_recipes
from pydantic import ValidationError as PydanticValidationError

router = APIRouter(prefix="/api")

# Constants
MAX_FILE_SIZE = 1_000_000  # 1MB


def create_error_response(status_code: int, field: str, message: str, details: Optional[List[dict]] = None) -> dict:
    """Create a standardized error response."""
    response = {
        "error": message,
        "field": field,
        "status_code": status_code
    }
    if details:
        response["details"] = details
    return response


@router.get("/recipes")
def get_recipes(search: Optional[str] = Query(None, max_length=200)):
    """Get all recipes or search by title.
    
    Query Parameters:
    - search: Optional search string to filter recipes by title
    
    Returns:
    - 200: List of recipes
    """
    try:
        if search:
            recipes = recipe_storage.search_recipes(search)
        else:
            recipes = recipe_storage.get_all_recipes()
        
        return {
            "recipes": recipes,
            "count": len(recipes)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Failed to retrieve recipes: {str(e)}")
        )


@router.get("/recipes/export")
def export_recipes():
    """Export all recipes as JSON.
    
    Returns:
    - 200: JSON array of all recipes
    """
    try:
        recipes = recipe_storage.get_all_recipes()
        recipes_dict = [recipe.model_dump(mode='json') for recipe in recipes]
        return {
            "recipes": recipes_dict,
            "count": len(recipes_dict),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Export failed: {str(e)}")
        )


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific recipe by ID.
    
    Path Parameters:
    - recipe_id: The unique identifier of the recipe
    
    Returns:
    - 200: Recipe object
    - 404: Recipe not found
    """
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty")
        )
    
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(404, "recipe_id", f"Recipe with ID '{recipe_id}' not found")
        )
    return recipe


@router.post("/recipes")
def create_recipe(recipe: RecipeCreate):
    """Create a new recipe.
    
    Request Body:
    - title: Recipe title (1-200 chars)
    - description: Recipe description (1-2000 chars)
    - cuisine: Cuisine type (1-100 chars)
    - ingredients: List of ingredients (1-50 items, each 1-500 chars)
    - instructions: List of instructions (1-100 items, each 1-1000 chars)
    - servings: Number of servings (1-100)
    - tags: List of tags (0-20 items)
    
    Returns:
    - 201: Created recipe with ID
    - 422: Validation error
    """
    try:
        # Validation is handled by Pydantic models
        new_recipe = recipe_storage.create_recipe(recipe)
        return new_recipe
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            error_details.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        raise HTTPException(
            status_code=422,
            detail=create_error_response(422, "validation", "Recipe data validation failed", error_details)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Failed to create recipe: {str(e)}")
        )


@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe: RecipeUpdate):
    """Update an existing recipe.
    
    Path Parameters:
    - recipe_id: The unique identifier of the recipe to update
    
    Request Body: Same schema as POST /recipes
    
    Returns:
    - 200: Updated recipe
    - 404: Recipe not found
    - 422: Validation error
    """
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty")
        )
    
    try:
        existing_recipe = recipe_storage.get_recipe(recipe_id)
        if not existing_recipe:
            raise HTTPException(
                status_code=404,
                detail=create_error_response(404, "recipe_id", f"Recipe with ID '{recipe_id}' not found")
            )
        
        updated_recipe = recipe_storage.update_recipe(recipe_id, recipe)
        return updated_recipe
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            error_details.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        raise HTTPException(
            status_code=422,
            detail=create_error_response(422, "validation", "Recipe data validation failed", error_details)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Failed to update recipe: {str(e)}")
        )


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str):
    """Delete a recipe.
    
    Path Parameters:
    - recipe_id: The unique identifier of the recipe to delete
    
    Returns:
    - 200: Deletion success message
    - 404: Recipe not found
    """
    if not recipe_id or not recipe_id.strip():
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "recipe_id", "Recipe ID cannot be empty")
        )
    
    success = recipe_storage.delete_recipe(recipe_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=create_error_response(404, "recipe_id", f"Recipe with ID '{recipe_id}' not found")
        )
    
    return {
        "message": "Recipe deleted successfully",
        "recipe_id": recipe_id,
        "status": "success"
    }


@router.post("/recipes/import")
async def import_recipes(file: UploadFile = File(...)):
    """Import recipes from a JSON file.
    
    File Format:
    - Must be JSON array of recipe objects
    - Each recipe must conform to Recipe schema
    
    Returns:
    - 200: Import success with count
    - 400: Invalid file format or size
    - 422: Schema validation failed
    """
    if not file:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "file", "No file provided")
        )
    
    # Validate file name
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "filename", "File must have a name")
        )
    
    if not file.filename.lower().endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail=create_error_response(400, "filename", "File must be a JSON file (.json)")
        )
    
    try:
        # Read and validate file size
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(400, "file_content", "File is empty")
            )
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    400,
                    "file_size",
                    f"File too large. Maximum size is {MAX_FILE_SIZE / 1_000_000}MB"
                )
            )
        
        # Parse JSON
        try:
            recipes_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(400, "json_format", f"Invalid JSON format: {str(e)}")
            )
        
        # Validate schema compliance
        is_valid, validation_errors = validate_import_recipes(recipes_data)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=create_error_response(
                    422,
                    "schema_validation",
                    "One or more recipes failed schema validation",
                    validation_errors[:10]  # Return first 10 errors
                )
            )
        
        # Import recipes
        count = recipe_storage.import_recipes(recipes_data)
        
        return {
            "message": f"Successfully imported {count} recipes from {file.filename}",
            "count": count,
            "filename": file.filename,
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=create_error_response(500, "internal", f"Import failed: {str(e)}")
        )
