"""Storage layer for SLA Library."""

from .repository import SLARepository, InMemorySLARepository

__all__ = [
    "SLARepository",
    "InMemorySLARepository",
]
