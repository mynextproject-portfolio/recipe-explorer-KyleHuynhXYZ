from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

from app.protocols import StorageProtocol, ExternalClientProtocol, CacheClientProtocol
from app.services.storage import recipe_storage
from app.services import themealdb
from app.services.auth import SECRET_KEY, ALGORITHM
from app.models import TokenData, UserInDB

# Tells FastAPI where the login endpoint is for Swagger UI documentation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_storage() -> StorageProtocol:
    """Dependency provider for the recipe storage layer."""
    return recipe_storage

def get_external_client() -> ExternalClientProtocol:
    """Dependency provider for the external recipe API client."""
    return themealdb

def get_cache_client() -> Optional[CacheClientProtocol]:
    """Dependency provider for a cache client (Redis)."""
    try:
        return themealdb._get_redis_client()
    except Exception:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), storage = Depends(get_storage)) -> UserInDB:
    """Dependency to validate JWT and return the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
        
    user = storage.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user