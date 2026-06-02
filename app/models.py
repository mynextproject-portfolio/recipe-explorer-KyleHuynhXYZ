from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List
import uuid

# Constants
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
MAX_INGREDIENT_LENGTH = 500
MAX_INSTRUCTION_LENGTH = 1000
MAX_INGREDIENTS = 50
MAX_INSTRUCTIONS = 100
MAX_TAGS = 20
MIN_SERVINGS = 1
MAX_SERVINGS = 100


class Recipe(BaseModel):
    """Recipe model with comprehensive validation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    cuisine: str = Field(min_length=1, max_length=100)
    ingredients: List[str] = Field(min_length=1, max_length=MAX_INGREDIENTS)
    instructions: List[str] = Field(min_length=1, max_length=MAX_INSTRUCTIONS)
    servings: int = Field(default=1, ge=MIN_SERVINGS, le=MAX_SERVINGS)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("ingredients", mode="before")
    @classmethod
    def validate_ingredients(cls, v):
        """Validate each ingredient string length."""
        if not isinstance(v, list):
            raise ValueError("Ingredients must be a list")
        for ingredient in v:
            if not isinstance(ingredient, str):
                raise ValueError("Each ingredient must be a string")
            if len(ingredient.strip()) == 0:
                raise ValueError("Ingredients cannot be empty strings")
            if len(ingredient) > MAX_INGREDIENT_LENGTH:
                raise ValueError(
                    f"Each ingredient must be at most {MAX_INGREDIENT_LENGTH} characters"
                )
        return v

    @field_validator("instructions", mode="before")
    @classmethod
    def validate_instructions(cls, v):
        """Validate each instruction string length."""
        if not isinstance(v, list):
            raise ValueError("Instructions must be a list")
        for instruction in v:
            if not isinstance(instruction, str):
                raise ValueError("Each instruction must be a string")
            if len(instruction.strip()) == 0:
                raise ValueError("Instructions cannot be empty strings")
            if len(instruction) > MAX_INSTRUCTION_LENGTH:
                raise ValueError(
                    f"Each instruction must be at most {MAX_INSTRUCTION_LENGTH} characters"
                )
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Validate each tag string."""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")
            if len(tag.strip()) == 0:
                raise ValueError("Tags cannot be empty strings")
        return v


class RecipeCreate(BaseModel):
    """Recipe creation model with comprehensive validation."""

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    cuisine: str = Field(min_length=1, max_length=100)
    ingredients: List[str] = Field(min_length=1, max_length=MAX_INGREDIENTS)
    instructions: List[str] = Field(min_length=1, max_length=MAX_INSTRUCTIONS)
    servings: int = Field(default=1, ge=MIN_SERVINGS, le=MAX_SERVINGS)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS)

    @field_validator("ingredients", mode="before")
    @classmethod
    def validate_ingredients(cls, v):
        """Validate each ingredient string length."""
        if not isinstance(v, list):
            raise ValueError("Ingredients must be a list")
        for ingredient in v:
            if not isinstance(ingredient, str):
                raise ValueError("Each ingredient must be a string")
            if len(ingredient.strip()) == 0:
                raise ValueError("Ingredients cannot be empty strings")
            if len(ingredient) > MAX_INGREDIENT_LENGTH:
                raise ValueError(
                    f"Each ingredient must be at most {MAX_INGREDIENT_LENGTH} characters"
                )
        return v

    @field_validator("instructions", mode="before")
    @classmethod
    def validate_instructions(cls, v):
        """Validate each instruction string length."""
        if not isinstance(v, list):
            raise ValueError("Instructions must be a list")
        for instruction in v:
            if not isinstance(instruction, str):
                raise ValueError("Each instruction must be a string")
            if len(instruction.strip()) == 0:
                raise ValueError("Instructions cannot be empty strings")
            if len(instruction) > MAX_INSTRUCTION_LENGTH:
                raise ValueError(
                    f"Each instruction must be at most {MAX_INSTRUCTION_LENGTH} characters"
                )
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Validate each tag string."""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")
            if len(tag.strip()) == 0:
                raise ValueError("Tags cannot be empty strings")
        return v


class RecipeUpdate(BaseModel):
    """Recipe update model with comprehensive validation."""

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_LENGTH)
    cuisine: str = Field(min_length=1, max_length=100)
    ingredients: List[str] = Field(min_length=1, max_length=MAX_INGREDIENTS)
    instructions: List[str] = Field(min_length=1, max_length=MAX_INSTRUCTIONS)
    servings: int = Field(ge=MIN_SERVINGS, le=MAX_SERVINGS)
    tags: List[str] = Field(max_length=MAX_TAGS)

    @field_validator("ingredients", mode="before")
    @classmethod
    def validate_ingredients(cls, v):
        """Validate each ingredient string length."""
        if not isinstance(v, list):
            raise ValueError("Ingredients must be a list")
        for ingredient in v:
            if not isinstance(ingredient, str):
                raise ValueError("Each ingredient must be a string")
            if len(ingredient.strip()) == 0:
                raise ValueError("Ingredients cannot be empty strings")
            if len(ingredient) > MAX_INGREDIENT_LENGTH:
                raise ValueError(
                    f"Each ingredient must be at most {MAX_INGREDIENT_LENGTH} characters"
                )
        return v

    @field_validator("instructions", mode="before")
    @classmethod
    def validate_instructions(cls, v):
        """Validate each instruction string length."""
        if not isinstance(v, list):
            raise ValueError("Instructions must be a list")
        for instruction in v:
            if not isinstance(instruction, str):
                raise ValueError("Each instruction must be a string")
            if len(instruction.strip()) == 0:
                raise ValueError("Instructions cannot be empty strings")
            if len(instruction) > MAX_INSTRUCTION_LENGTH:
                raise ValueError(
                    f"Each instruction must be at most {MAX_INSTRUCTION_LENGTH} characters"
                )
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v):
        """Validate each tag string."""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("Each tag must be a string")
            if len(tag.strip()) == 0:
                raise ValueError("Tags cannot be empty strings")
        return v

# --- AUTHENTICATION MODELS ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserInDB(UserBase):
    id: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

    # --- API V2 MODELS ---

class NutritionInfo(BaseModel):
    calories: Optional[int] = 0
    protein_g: Optional[float] = 0.0
    carbs_g: Optional[float] = 0.0
    fat_g: Optional[float] = 0.0

class RecipeV2(Recipe):
    """Enhanced V2 schema extending the base V1 Recipe."""
    difficulty: str = Field(default="Medium", pattern="^(Easy|Medium|Hard|Expert)$")
    equipment: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    nutrition: NutritionInfo = Field(default_factory=NutritionInfo)

class RecipeCreateV2(RecipeCreate):
    difficulty: str = "Medium"
    equipment: List[str] = []
    dietary_restrictions: List[str] = []
    nutrition: Optional[NutritionInfo] = None

class RecipeUpdateV2(RecipeUpdate):
    difficulty: Optional[str] = None
    equipment: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    nutrition: Optional[NutritionInfo] = None