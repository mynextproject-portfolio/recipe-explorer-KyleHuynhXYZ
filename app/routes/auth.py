from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models import UserCreate, Token, UserBase
from app.services.auth import verify_password, get_password_hash, create_access_token
from app.deps import get_storage, get_current_user
from app.routes.api import serialize_recipe

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
collections_router = APIRouter(prefix="/api/collections", tags=["Collections"])

@router.post("/register", response_model=UserBase)
def register(user: UserCreate, storage = Depends(get_storage)):
    existing_user = storage.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_pwd = get_password_hash(user.password)
    new_user = storage.create_user(user, hashed_pwd)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), storage = Depends(get_storage)):
    user = storage.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserBase)
def get_me(current_user = Depends(get_current_user)):
    return current_user

# --- COLLECTIONS ROUTES ---

@collections_router.post("/{recipe_id}/toggle")
def toggle_favorite(recipe_id: str, current_user = Depends(get_current_user), storage = Depends(get_storage)):
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    is_favorited = storage.toggle_favorite(current_user.id, recipe_id)
    return {"status": "success", "favorited": is_favorited}

@collections_router.get("/favorites")
def get_favorites(current_user = Depends(get_current_user), storage = Depends(get_storage)):
    favorites = storage.get_user_favorites(current_user.id)
    return {"recipes": [serialize_recipe(r) for r in favorites], "count": len(favorites)}