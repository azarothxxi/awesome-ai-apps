"""Action management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...models import Action
from ..app import get_repository

router = APIRouter()


@router.post("/", response_model=Action, status_code=201)
async def create_action(
    action: Action,
    repository=Depends(get_repository),
):
    """Create a new action."""
    created_action = repository.create_action(action)
    return created_action


@router.get("/", response_model=List[Action])
async def list_actions(
    enabled_only: bool = Query(False, description="Only return enabled actions"),
    repository=Depends(get_repository),
):
    """List all actions."""
    actions = repository.get_all_actions(enabled_only)
    return actions


@router.get("/{action_id}", response_model=Action)
async def get_action(
    action_id: UUID,
    repository=Depends(get_repository),
):
    """Get a specific action by ID."""
    action = repository.get_action(action_id)

    if not action:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")

    return action


@router.put("/{action_id}", response_model=Action)
async def update_action(
    action_id: UUID,
    action: Action,
    repository=Depends(get_repository),
):
    """Update an existing action."""
    updated_action = repository.update_action(action_id, action)

    if not updated_action:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")

    return updated_action


@router.delete("/{action_id}", status_code=204)
async def delete_action(
    action_id: UUID,
    repository=Depends(get_repository),
):
    """Delete an action."""
    deleted = repository.delete_action(action_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")

    return None
