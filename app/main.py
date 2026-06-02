from fastapi.middleware.cors import CORSMiddleware
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.routes import api, pages, auth, api_v2  # Add api_v2 here
from app.services.storage import recipe_storage
from prometheus_client import make_asgi_app
from app.metrics import API_RESPONSE_TIME

APP_NAME = "Recipe Explorer API"
VERSION = "2.0.0" # Bumped to 2.0.0
DEBUG = True
SAMPLE_DATA_PATH = Path(__file__).parent.parent / "sample-recipes.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    if SAMPLE_DATA_PATH.exists():
        try:
            with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as sample_file:
                recipes_data = json.load(sample_file)
            recipe_storage.import_recipes(recipes_data)
        except Exception:
            pass
    yield

app = FastAPI(title=APP_NAME, version=VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- DEPRECATION & TIMING MIDDLEWARE ---
@app.middleware("http")
async def global_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Track metrics
    if request.url.path != "/metrics":
        API_RESPONSE_TIME.labels(
            method=request.method, endpoint=request.url.path
        ).observe(time.time() - start_time)
        
    # Inject V1 Deprecation Warning Header
    if request.url.path.startswith("/api/recipes") or request.url.path == "/api/search":
        response.headers["Warning"] = '299 - "This v1 API is deprecated. Please migrate to /api/v2/recipes"'
        response.headers["X-API-Version"] = "1.0"
    elif request.url.path.startswith("/api/v2"):
        response.headers["X-API-Version"] = "2.0"
        
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(api.router)
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(auth.collections_router)
app.include_router(api_v2.router)  # Mount the new V2 router

@app.get("/health")
def health_check():
    return {"status": "healthy"}