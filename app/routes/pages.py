from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models import RecipeCreate, RecipeUpdate
from app.deps import get_storage, get_external_client
from app.protocols import ExternalClientProtocol
from app.services.themealdb import ExternalAPIError

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    search: Optional[str] = None,
    message: Optional[str] = None,
    storage: Any = Depends(get_storage),
    external_client: ExternalClientProtocol = Depends(get_external_client),
):
    """Home page with recipe list and search"""
    external_error = None
    if search:
        internal_results = storage.search_recipes(search)
        try:
            external_results = external_client.search_meals(search)
        except ExternalAPIError as exc:
            external_results = []
            external_error = str(exc)
    else:
        internal_results = storage.get_all_recipes()
        external_results = []

    recipes = []
    for recipe in internal_results:
        recipe_dict = recipe.model_dump(mode="json")
        recipe_dict["source"] = "internal"
        recipes.append(recipe_dict)
    recipes.extend(external_results)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "recipes": recipes,
            "search_query": search or "",
            "message": message,
            "external_error": external_error,
        },
    )


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request):
    """New recipe form"""
    return templates.TemplateResponse(
        request=request,
        name="recipe_form.html",
        context={"request": request, "recipe": None, "is_edit": False},
    )


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(
    request: Request,
    recipe_id: str,
    message: Optional[str] = None,
    storage: Any = Depends(get_storage),
    external_client: ExternalClientProtocol = Depends(get_external_client),
):
    """Recipe detail page"""
    recipe = storage.get_recipe(recipe_id)
    if recipe:
        recipe = recipe.model_dump(mode="json")
        recipe["source"] = "internal"
    else:
        if recipe_id.startswith("external-"):
            external_id = recipe_id.replace("external-", "", 1)
            try:
                recipe = external_client.get_meal_by_id(external_id)
                if recipe:
                    recipe["created_at"] = datetime.fromisoformat(recipe["created_at"])
                    recipe["updated_at"] = datetime.fromisoformat(recipe["updated_at"])
                else:
                    raise HTTPException(status_code=404, detail="Recipe not found")
            except ExternalAPIError as exc:
                raise HTTPException(status_code=502, detail=str(exc))
        else:
            raise HTTPException(status_code=404, detail="Recipe not found")

    return templates.TemplateResponse(
        request=request,
        name="recipe_detail.html",
        context={"request": request, "recipe": recipe, "message": message},
    )


@router.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def edit_recipe_form(
    request: Request,
    recipe_id: str,
    storage: Any = Depends(get_storage),
):
    """Edit recipe form"""
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return templates.TemplateResponse(
        request=request,
        name="recipe_form.html",
        context={"request": request, "recipe": recipe, "is_edit": True},
    )


@router.post("/recipes/new")
def create_recipe_form(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    cuisine: str = Form(...),
    servings: int = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    tags: str = Form(...),
    storage: Any = Depends(get_storage),
):
    """Handle new recipe form submission"""
    try:
        # Check title length
        if len(title) > 200:
            raise ValueError("Title too long")

        # Parse ingredients (one per line) and tags (comma-separated)
        ingredient_list = [
            ing.strip() for ing in ingredients.split("\n") if ing.strip()
        ]
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        instruction_steps = [
            step.strip() for step in instructions.split("\n\n") if step.strip()
        ]

        # Validation
        if len(ingredient_list) == 0:
            raise ValueError("At least one ingredient required")

        if len(instruction_steps) == 0:
            raise ValueError("Instructions are required")

        if not cuisine.strip():
            raise ValueError("Cuisine is required")

        recipe_data = RecipeCreate(
            title=title,
            description=description,
            cuisine=cuisine.strip(),
            ingredients=ingredient_list,
            instructions=instruction_steps,
            servings=servings,
            tags=tag_list,
        )

        new_recipe = storage.create_recipe(recipe_data)
        return RedirectResponse(
            url=f"/recipes/{new_recipe.id}?message=Recipe created successfully",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/?message=Error creating recipe: {str(e)}", status_code=303
        )


@router.post("/recipes/{recipe_id}/edit")
def update_recipe_form(
    request: Request,
    recipe_id: str,
    title: str = Form(...),
    description: str = Form(...),
    cuisine: str = Form(...),
    servings: int = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    tags: str = Form(...),
    storage: Any = Depends(get_storage),
):
    """Handle edit recipe form submission"""
    try:
        # Check title length
        if len(title) > 200:
            raise ValueError("Title is too long!")

        # Parse ingredients (one per line) and tags (comma-separated)
        ingredient_list = [
            ing.strip() for ing in ingredients.split("\n") if ing.strip()
        ]
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        instruction_steps = [
            step.strip() for step in instructions.split("\n\n") if step.strip()
        ]

        if len(ingredient_list) == 0:
            raise ValueError("Need ingredients!")

        if len(instruction_steps) == 0:
            raise ValueError("Instructions are required")

        if not cuisine.strip():
            raise ValueError("Cuisine is required")

        recipe_data = RecipeUpdate(
            title=title,
            description=description,
            cuisine=cuisine.strip(),
            ingredients=ingredient_list,
            instructions=instruction_steps,
            servings=servings,
            tags=tag_list,
        )

        updated_recipe = storage.update_recipe(recipe_id, recipe_data)
        if not updated_recipe:
            return RedirectResponse(url="/?message=Recipe not found", status_code=303)

        return RedirectResponse(
            url=f"/recipes/{recipe_id}?message=Recipe updated successfully",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/recipes/{recipe_id}?message=Error updating recipe: {str(e)}",
            status_code=303,
        )


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe_form(recipe_id: str, storage: Any = Depends(get_storage)):
    """Handle recipe deletion"""
    success = storage.delete_recipe(recipe_id)
    if success:
        return RedirectResponse(
            url="/?message=Recipe deleted successfully", status_code=303
        )
    else:
        return RedirectResponse(url="/?message=Recipe not found", status_code=303)


@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request, message: Optional[str] = None):
    """Import recipes page"""
    return templates.TemplateResponse(
        request=request,
        name="import.html",
        context={"request": request, "message": message},
    )
