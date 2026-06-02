import sqlite3
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from app.models import Recipe, RecipeCreate, RecipeUpdate, UserCreate, UserInDB

# Global counter for analytics
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS recipes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            ''')
            # NEW: Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
            ''')
            # NEW: Favorites/Collections table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    user_id TEXT NOT NULL,
                    recipe_id TEXT NOT NULL,
                    PRIMARY KEY (user_id, recipe_id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()

    # --- RECIPE METHODS ---
    def get_all_recipes(self) -> List[Recipe]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT data FROM recipes")
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
        existing_recipe = self.get_recipe(recipe_id)
        if not existing_recipe:
            return None
        updated_data = recipe_data.model_dump()
        for key, value in updated_data.items():
            setattr(existing_recipe, key, value)
        existing_recipe.updated_at = datetime.now()
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
            conn.execute("DELETE FROM recipes")
            for recipe_dict in recipes_data:
                try:
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
                    continue
            conn.commit()
        return count

    # --- NEW USER & COLLECTION METHODS ---
    def create_user(self, user_data: UserCreate, hashed_password: str) -> UserInDB:
        user_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
                    (user_id, user_data.username, hashed_password)
                )
                conn.commit()
                return UserInDB(id=user_id, username=user_data.username, hashed_password=hashed_password)
            except sqlite3.IntegrityError:
                return None # Username already exists

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return UserInDB(id=row[0], username=row[1], hashed_password=row[2])
            return None

    def toggle_favorite(self, user_id: str, recipe_id: str) -> bool:
        """Returns True if favorited, False if unfavorited."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
            if cursor.fetchone():
                conn.execute("DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?", (user_id, recipe_id))
                conn.commit()
                return False
            else:
                conn.execute("INSERT INTO favorites (user_id, recipe_id) VALUES (?, ?)", (user_id, recipe_id))
                conn.commit()
                return True

    def get_user_favorites(self, user_id: str) -> List[Recipe]:
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT r.data FROM recipes r
                JOIN favorites f ON r.id = f.recipe_id
                WHERE f.user_id = ?
            ''', (user_id,))
            return [Recipe(**json.loads(row[0])) for row in cursor.fetchall()]

# Global storage instance injected into dependencies
recipe_storage = SQLiteRecipeStorage("recipes.db")