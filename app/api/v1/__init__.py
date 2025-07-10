from fastapi import APIRouter

from app.api.v1 import (
    auth,
    credentials,
    health,
    models,
    preferences,
    runs,
    sessions,
    streams,
)
from app.api.v1.endpoints import admin, provider_keys

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(streams.router, prefix="/runs", tags=["Streaming"])
api_router.include_router(sessions.router, tags=["Sessions"])
api_router.include_router(preferences.router, tags=["Preferences"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(credentials.router, prefix="/credentials", tags=["Credentials"])
api_router.include_router(provider_keys.router, prefix="/provider-keys", tags=["Provider Keys"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
