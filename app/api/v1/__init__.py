from fastapi import APIRouter

from app.api.v1 import auth, health, runs, streams, admin

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(streams.router, prefix="/runs", tags=["Streaming"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])