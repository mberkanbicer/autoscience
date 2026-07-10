"""Connector health and status endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.connectors.manager import ConnectorManager
from app.dependencies import get_connector_manager

router = APIRouter()


@router.get("/health")
async def connector_health(
    manager: Annotated[ConnectorManager, Depends(get_connector_manager)],
) -> dict:
    """Check availability of registered academic source connectors."""
    health = await manager.health_check()
    return {
        "connectors": health,
        "healthy_count": sum(1 for ok in health.values() if ok),
        "total_count": len(health),
        "cached": manager.cache is not None,
        "optional": getattr(manager, "optional_connectors", {}),
        "registered": list(manager.connectors.keys()),
    }


@router.post("/{name}/reset")
async def reset_connector_circuit(
    name: str,
    manager: Annotated[ConnectorManager, Depends(get_connector_manager)],
) -> dict:
    """Manually reset the circuit-breaker for a connector.

    Clears the failure counter and cooldown timer so the next
    request will be allowed through. Returns the previous state.
    """
    try:
        return manager.reset_circuit_breaker(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
