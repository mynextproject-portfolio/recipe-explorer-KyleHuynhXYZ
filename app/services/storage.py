import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
from app.models import Recipe, RecipeCreate, RecipeUpdate

# Global counter for analytics (can be used for analytics)
recipe_view_count = {}

class SQLiteRecipeStorage:
    def __init__(self, db_path: str = "recipes.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Creates a thread-safe connection for each transaction."""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Initializes the database schema."""
        with self._get_connection() as conn:
            # We store the full Pydantic model as a JSON string in 'data'
            # id and title are extracted for fast querying and searching
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recipes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            ''')
            conn.commit()

    def get_all_recipes(self) -> List[Recipe]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM recipes")
            # Pydantic automatically parses the JSON dict back into proper types (like datetime)
            return [Recipe(**json.loads(row[0])) for row in cursor.fetchall()]

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM recipes WHERE id = ?", (recipe_id,))
            row = cursor.fetchone()
            if row:
                return Recipe(**json.loads(row[0]))
            return None

    def search_recipes(self, query: str) -> List[Recipe]:
        if not query:
            return self.get_all_recipes()

        with self._get_connection() as conn:
            # Case-insensitive substring search using SQLite LIKE
            cursor = conn.execute(
                "SELECT data FROM recipes WHERE title LIKE ?", 
                (f"%{query}%",)
            )
            return [Recipe(**json.loads(row[0])) for row in cursor.fetchall()]

    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        recipe = Recipe(**recipe_data.model_dump())
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO recipes (id, title, data) VALUES (?, ?, ?)",
                (recipe.id, recipe.title, recipe.model_dump_json())
            )
            conn.commit()
        return recipe

    def update_recipe(self, recipe_id: str, recipe_data: RecipeUpdate) -> Optional[Recipe]:
        # Fetch existing recipe to apply updates
        existing_recipe = self.get_recipe(recipe_id)
        if not existing_recipe:
            return None

        # Apply updates
        updated_data = recipe_data.model_dump()
        for key, value in updated_data.items():
            setattr(existing_recipe, key, value)
        existing_recipe.updated_at = datetime.now()

        # Save back to database
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE recipes SET title = ?, data = ? WHERE id = ?",
                (existing_recipe.title, existing_recipe.model_dump_json(), recipe_id)
            )
            conn.commit()
        return existing_recipe

    def delete_recipe(self, recipe_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
            conn.commit()
            return cursor.rowcount > 0

    def import_recipes(self, recipes_data: List[dict]) -> int:
        count = 0
        with self._get_connection() as conn:
            # Replace all existing recipes to match original in-memory behavior
            conn.execute("DELETE FROM recipes")
            
            for recipe_dict in recipes_data:
                try:
                    # Handle datetime strings if they exist
                    if "created_at" in recipe_dict and isinstance(recipe_dict["created_at"], str):
                        recipe_dict["created_at"] = datetime.fromisoformat(recipe_dict["created_at"])
                    if "updated_at" in recipe_dict and isinstance(recipe_dict["updated_at"], str):
                        recipe_dict["updated_at"] = datetime.fromisoformat(recipe_dict["updated_at"])

                    recipe = Recipe(**recipe_dict)
                    
                    conn.execute(
                        "INSERT INTO recipes (id, title, data) VALUES (?, ?, ?)",
                        (recipe.id, recipe.title, recipe.model_dump_json())
                    )
                    count += 1
                except Exception:
                    # Skip invalid recipes
                    continue
            conn.commit()
            
        return count

# Global storage instance injected into dependencies
recipe_storage = SQLiteRecipeStorage("recipes.db")