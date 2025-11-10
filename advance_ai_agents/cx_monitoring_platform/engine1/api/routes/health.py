"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends

from ..app import get_repository

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Engine 1: SLA Library and Rules Platform",
    }


@router.get("/stats")
async def get_stats(repository=Depends(get_repository)):
    """Get repository statistics."""
    stats = repository.get_stats()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "stats": stats,
    }
