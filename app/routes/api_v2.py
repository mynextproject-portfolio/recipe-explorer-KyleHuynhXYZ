from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, List, Optional
from app.models import RecipeV2, RecipeCreateV2
from app.deps import get_storage, get_current_user

router = APIRouter(prefix="/api/v2", tags=["Recipes V2"])

def serialize_v2(recipe: RecipeV2) -> dict:
    return recipe.model_dump(mode="json")

@router.get("/recipes")
def get_recipes_v2(
    search: Optional[str] = Query(None, description="Search by title"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    sort_by: str = Query("created_at", description="Sort field (created_at, title)"),
    limit: int = Query(50, ge=1, le=100),
    storage: Any = Depends(get_storage)
):
    """V2 Enhanced Search with filtering and sorting."""
    results = storage.search_recipes_v2(query=search, difficulty=difficulty)
    
    # Sorting logic
    if sort_by == "title":
        results.sort(key=lambda r: r.title)
    else:
        results.sort(key=lambda r: r.created_at, reverse=True)
        
    # Pagination
    paginated = results[:limit]
    
    return {
        "version": "v2",
        "count": len(paginated),
        "recipes": [serialize_v2(r) for r in paginated]
    }

@router.post("/recipes")
def create_recipe_v2(
    recipe: RecipeCreateV2, 
    storage: Any = Depends(get_storage),
    current_user = Depends(get_current_user) # Require auth to create V2 recipes
):
    """Create a recipe using the enhanced V2 schema."""
    try:
        new_recipe = storage.create_recipe_v2(recipe)
        return serialize_v2(new_recipe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recipes/{recipe_id}")
def get_recipe_v2(recipe_id: str, storage: Any = Depends(get_storage)):
    recipe = storage.get_recipe_v2(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return serialize_v2(recipe)