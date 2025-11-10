"""SLA management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...models import SLA, ServiceType
from ..app import get_repository

router = APIRouter()


@router.post("/", response_model=SLA, status_code=201)
async def create_sla(
    sla: SLA,
    repository=Depends(get_repository),
):
    """Create a new SLA."""
    created_sla = repository.create_sla(sla)
    return created_sla


@router.get("/", response_model=List[SLA])
async def list_slas(
    enabled_only: bool = Query(False, description="Only return enabled SLAs"),
    service_type: Optional[ServiceType] = Query(
        None, description="Filter by service type"
    ),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    repository=Depends(get_repository),
):
    """List all SLAs with optional filters."""
    if customer_id:
        slas = repository.get_slas_by_customer(customer_id, enabled_only)
    elif service_type:
        slas = repository.get_slas_by_service_type(service_type, enabled_only)
    else:
        slas = repository.get_all_slas(enabled_only)

    return slas


@router.get("/{sla_id}", response_model=SLA)
async def get_sla(
    sla_id: UUID,
    repository=Depends(get_repository),
):
    """Get a specific SLA by ID."""
    sla = repository.get_sla(sla_id)

    if not sla:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    return sla


@router.put("/{sla_id}", response_model=SLA)
async def update_sla(
    sla_id: UUID,
    sla: SLA,
    repository=Depends(get_repository),
):
    """Update an existing SLA."""
    updated_sla = repository.update_sla(sla_id, sla)

    if not updated_sla:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    return updated_sla


@router.delete("/{sla_id}", status_code=204)
async def delete_sla(
    sla_id: UUID,
    repository=Depends(get_repository),
):
    """Delete an SLA."""
    deleted = repository.delete_sla(sla_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    return None


@router.patch("/{sla_id}/enable", response_model=SLA)
async def enable_sla(
    sla_id: UUID,
    repository=Depends(get_repository),
):
    """Enable an SLA."""
    sla = repository.get_sla(sla_id)

    if not sla:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    sla.enabled = True
    updated_sla = repository.update_sla(sla_id, sla)

    return updated_sla


@router.patch("/{sla_id}/disable", response_model=SLA)
async def disable_sla(
    sla_id: UUID,
    repository=Depends(get_repository),
):
    """Disable an SLA."""
    sla = repository.get_sla(sla_id)

    if not sla:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    sla.enabled = False
    updated_sla = repository.update_sla(sla_id, sla)

    return updated_sla
