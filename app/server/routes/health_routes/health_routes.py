from typing import Any
from fastapi import APIRouter, Request

health_router = APIRouter(prefix = "/api/health")


@health_router.get("")
async def health(request: Request) -> dict[str, Any]:
    config = request.app.state.config
    return {"status": "ok", "environment": config.environment.value, "version": config.version}
