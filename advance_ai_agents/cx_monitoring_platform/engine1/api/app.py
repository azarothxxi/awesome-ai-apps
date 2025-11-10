"""
FastAPI application for Engine 1: SLA Library and Rules Platform.

Provides REST API for managing SLAs, rules, actions, and evaluating metrics.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..rules import RulesEngine
from ..storage import InMemorySLARepository
from .routes import actions, evaluation, health, slas


# Global state
app_state = {
    "repository": None,
    "rules_engine": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app_state["repository"] = InMemorySLARepository()
    app_state["rules_engine"] = RulesEngine()

    yield

    # Shutdown
    app_state.clear()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="CX Monitoring Platform - Engine 1",
        description="SLA Library and Rules Platform API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(slas.router, prefix="/api/v1/slas", tags=["SLAs"])
    app.include_router(actions.router, prefix="/api/v1/actions", tags=["Actions"])
    app.include_router(
        evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"]
    )

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "CX Monitoring Platform - Engine 1",
            "description": "SLA Library and Rules Platform",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


def get_repository():
    """Dependency injection for repository."""
    return app_state["repository"]


def get_rules_engine():
    """Dependency injection for rules engine."""
    return app_state["rules_engine"]
