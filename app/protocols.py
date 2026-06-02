"""Abstract interfaces for dependency injection.

These protocols define the contract that implementations must satisfy,
allowing for easy component swapping and testing.
"""

from typing import List, Optional, Protocol

from app.models import Recipe, RecipeCreate, RecipeUpdate


class StorageProtocol(Protocol):
    """Abstract interface for recipe data access operations."""

    def get_all_recipes(self) -> List[Recipe]:
        """Retrieve all recipes."""
        ...

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """Retrieve a single recipe by ID."""
        ...

    def search_recipes(self, query: str) -> List[Recipe]:
        """Search recipes by title or other criteria."""
        ...

    def create_recipe(self, recipe: RecipeCreate) -> Recipe:
        """Create a new recipe."""
        ...

    def update_recipe(self, recipe_id: str, recipe: RecipeUpdate) -> Recipe:
        """Update an existing recipe."""
        ...

    def delete_recipe(self, recipe_id: str) -> bool:
        """Delete a recipe by ID."""
        ...

    def import_recipes(self, recipes_data: List[dict]) -> int:
        """Import multiple recipes from a list of dicts."""
        ...


class ExternalClientProtocol(Protocol):
    """Abstract interface for external recipe API operations."""

    cache_hits: int
    cache_misses: int

    def search_meals(self, query: str) -> List[dict]:
        """Search external API for meals matching query."""
        ...

    def get_meal_by_id(self, meal_id: str) -> Optional[dict]:
        """Retrieve a specific meal by ID from external API."""
        ...


class CacheClientProtocol(Protocol):
    """Abstract interface for caching operations."""

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value from cache."""
        ...

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        """Set a value in cache with expiry time."""
        ...
