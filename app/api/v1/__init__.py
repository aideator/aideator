from fastapi import APIRouter

# The legacy `/runs` endpoints have been deprecated in favour of unified `/tasks` routes.
# Remove their import so they are no longer registered.
from app.api.v1 import (
    admin_messaging,
    agent_outputs,
    auth,
    health,
    tasks,
)

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# Removed – use /tasks endpoints exclusively
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
# Removed sessions, preferences, credentials, provider-keys, and admin-data routers - simplified for dev mode
api_router.include_router(
    admin_messaging.router, prefix="/admin-messaging", tags=["Admin Messaging"]
)
api_router.include_router(
    agent_outputs.router, prefix="/agent-outputs", tags=["Agent Outputs"]
)
