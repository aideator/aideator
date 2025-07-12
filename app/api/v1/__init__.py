from fastapi import APIRouter

from app.api.v1 import (
    admin_messaging,
    agent_outputs,
    auth,
    credentials,
    health,
    models,
    preferences,
    runs,
    sessions,
    websocket,
)
from app.api.v1.endpoints import admin, provider_keys

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(sessions.router, tags=["Sessions"])
api_router.include_router(preferences.router, tags=["Preferences"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(
    credentials.router, prefix="/credentials", tags=["Credentials"]
)
api_router.include_router(
    provider_keys.router, prefix="/provider-keys", tags=["Provider Keys"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(
    admin_messaging.router, prefix="/admin-messaging", tags=["Admin Messaging"]
)
api_router.include_router(
    agent_outputs.router, prefix="/agent-outputs", tags=["Agent Outputs"]
)
api_router.include_router(websocket.router, tags=["WebSocket"])
