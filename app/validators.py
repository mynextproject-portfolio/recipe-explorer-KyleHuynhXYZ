"""
Schema validation module for Recipe Explorer.
Provides centralized validation functions for recipe data compliance.
"""

from typing import List, Dict, Any, Tuple
from app.models import Recipe, RecipeCreate, RecipeUpdate
from pydantic import ValidationError as PydanticValidationError


def validate_recipe_create(data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate recipe creation data against schema.
    Returns (is_valid, errors) tuple.
    """
    errors = []
    try:
        RecipeCreate(**data)
        return True, []
    except PydanticValidationError as e:
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        return False, errors


def validate_recipe_update(data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate recipe update data against schema.
    Returns (is_valid, errors) tuple.
    """
    errors = []
    try:
        RecipeUpdate(**data)
        return True, []
    except PydanticValidationError as e:
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )
        return False, errors


def validate_import_recipes(data: Any) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate import recipes data.
    Returns (is_valid, errors) tuple.
    """
    errors = []

    # Check if data is a list
    if not isinstance(data, list):
        return False, [{"field": "root", "message": "Data must be an array of recipes"}]

    # Check if list is empty
    if len(data) == 0:
        return False, [{"field": "root", "message": "Recipe list cannot be empty"}]

    # Validate each recipe
    valid_recipes = []
    for idx, recipe_data in enumerate(data):
        if not isinstance(recipe_data, dict):
            errors.append(
                {
                    "field": f"recipes[{idx}]",
                    "message": "Each recipe must be an object",
                    "index": idx,
                }
            )
            continue

        try:
            # For import, we use Recipe model to validate full schema
            Recipe(**recipe_data)
            valid_recipes.append(recipe_data)
        except PydanticValidationError as e:
            for error in e.errors():
                errors.append(
                    {
                        "field": f"recipes[{idx}].{'.'.join(str(x) for x in error['loc'])}",
                        "message": error["msg"],
                        "type": error["type"],
                        "index": idx,
                    }
                )

    # If there are any errors, return validation failure
    if errors:
        return False, errors

    return True, []


def validate_schema_compliance(
    data: Any, schema_type: str = "recipe"
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Generic schema compliance validator.
    schema_type: "recipe", "create", "update", "import"
    """
    if schema_type == "create":
        return validate_recipe_create(data)
    elif schema_type == "update":
        return validate_recipe_update(data)
    elif schema_type == "import":
        return validate_import_recipes(data)
    else:
        return False, [
            {"field": "schema_type", "message": f"Unknown schema type: {schema_type}"}
        ]
