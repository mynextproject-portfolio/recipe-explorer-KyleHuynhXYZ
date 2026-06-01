from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str 
    description: str
    ingredients: List[str]
    instructions: List[str]
    servings: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class RecipeCreate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    servings: int = Field(default=1, ge=1)
    tags: List[str] = Field(default_factory=list)

class RecipeUpdate(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    servings: int
    tags: List[str]