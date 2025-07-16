from fastapi import APIRouter

from app.api.v1 import (
    admin_messaging,
    agent_outputs,
    auth,
    health,
    runs,
    tasks,
)

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
# Removed sessions, preferences, credentials, provider-keys, and admin-data routers - simplified for dev mode
api_router.include_router(
    admin_messaging.router, prefix="/admin-messaging", tags=["Admin Messaging"]
)
api_router.include_router(
    agent_outputs.router, prefix="/agent-outputs", tags=["Agent Outputs"]
)
