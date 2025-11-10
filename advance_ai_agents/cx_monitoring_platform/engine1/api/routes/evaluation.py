"""SLA evaluation endpoints."""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from ...rules import EvaluationResult
from ..app import get_repository, get_rules_engine

router = APIRouter()


class EvaluateRequest(BaseModel):
    """Request model for SLA evaluation."""

    sla_id: UUID = Field(..., description="ID of SLA to evaluate")
    metrics: Dict[str, Any] = Field(
        ..., description="Dictionary of metric values", examples=[{
            "connection_time": 2.5,
            "signal_strength": 4,
            "error_count": 0,
        }]
    )
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    additional_context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context"
    )


class BatchEvaluateRequest(BaseModel):
    """Request model for batch SLA evaluation."""

    metrics: Dict[str, Any] = Field(..., description="Dictionary of metric values")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    enabled_only: bool = Field(
        True, description="Only evaluate enabled SLAs"
    )


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_sla(
    request: EvaluateRequest = Body(...),
    repository=Depends(get_repository),
    rules_engine=Depends(get_rules_engine),
):
    """
    Evaluate a single SLA against provided metrics.

    This endpoint checks if the service metrics comply with the SLA rules
    and returns any violations detected.
    """
    # Get the SLA
    sla = repository.get_sla(request.sla_id)

    if not sla:
        raise HTTPException(
            status_code=404, detail=f"SLA {request.sla_id} not found"
        )

    # Register actions from repository
    for action_id in set(
        action_id for rule in sla.rules for action_id in rule.action_ids
    ):
        action = repository.get_action(action_id)
        if action:
            rules_engine.register_action(action)

    # Evaluate
    result = rules_engine.evaluate_sla(
        sla=sla,
        metrics=request.metrics,
        customer_id=request.customer_id,
        additional_context=request.additional_context,
    )

    return result


@router.post("/evaluate/batch", response_model=Dict[str, EvaluationResult])
async def batch_evaluate_slas(
    request: BatchEvaluateRequest = Body(...),
    repository=Depends(get_repository),
    rules_engine=Depends(get_rules_engine),
):
    """
    Evaluate all (or enabled) SLAs against provided metrics.

    Useful for checking compliance across all service level agreements
    with a single API call.
    """
    # Get SLAs to evaluate
    slas = repository.get_all_slas(enabled_only=request.enabled_only)

    if not slas:
        return {}

    # Register all actions
    all_action_ids = set()
    for sla in slas:
        for rule in sla.rules:
            all_action_ids.update(rule.action_ids)

    for action_id in all_action_ids:
        action = repository.get_action(action_id)
        if action:
            rules_engine.register_action(action)

    # Evaluate all SLAs
    results = rules_engine.evaluate_multiple_slas(
        slas=slas,
        metrics=request.metrics,
        customer_id=request.customer_id,
    )

    # Convert UUID keys to strings for JSON serialization
    return {str(sla_id): result for sla_id, result in results.items()}


@router.post("/evaluate/rule")
async def evaluate_single_rule(
    sla_id: UUID,
    rule_id: UUID,
    metrics: Dict[str, Any] = Body(...),
    repository=Depends(get_repository),
    rules_engine=Depends(get_rules_engine),
):
    """
    Evaluate a single rule from an SLA.

    Useful for testing individual rules during development.
    """
    # Get the SLA
    sla = repository.get_sla(sla_id)

    if not sla:
        raise HTTPException(status_code=404, detail=f"SLA {sla_id} not found")

    # Find the rule
    rule = next((r for r in sla.rules if r.id == rule_id), None)

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule {rule_id} not found in SLA {sla_id}"
        )

    # Evaluate
    is_compliant, violation_reasons = rules_engine.evaluator.evaluate_rule(
        rule, metrics
    )

    return {
        "rule_id": str(rule_id),
        "rule_name": rule.name,
        "is_compliant": is_compliant,
        "violation_reasons": violation_reasons,
        "severity": rule.severity.value if not is_compliant else None,
    }
