"""
Main Rules Engine for SLA monitoring.

Orchestrates rule evaluation, violation detection, and action triggering.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..models import SLA, Action, SeverityLevel, SLARule
from .evaluator import RuleEvaluator

logger = logging.getLogger(__name__)


class ViolationEvent(BaseModel):
    """Represents an SLA violation event."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Rule and SLA information
    sla_id: UUID = Field(..., description="ID of violated SLA")
    sla_name: str = Field(..., description="Name of violated SLA")
    rule_id: UUID = Field(..., description="ID of violated rule")
    rule_name: str = Field(..., description="Name of violated rule")

    # Violation details
    severity: SeverityLevel = Field(..., description="Violation severity")
    violation_reasons: List[str] = Field(
        default_factory=list,
        description="Detailed reasons for violation"
    )

    # Metrics at time of violation
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metric values at time of violation"
    )

    # Actions triggered
    triggered_actions: List[UUID] = Field(
        default_factory=list,
        description="IDs of actions triggered"
    )

    # Context
    service_type: str = Field(..., description="Type of service")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    additional_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sla_name": "Premium Voice Service SLA",
                    "rule_name": "Intra-Network Call Connection Time",
                    "severity": "minor",
                    "violation_reasons": [
                        "Connection time: 4.2s > 3s (VIOLATED)"
                    ],
                    "metrics": {
                        "connection_time": 4.2,
                        "signal_strength": 4
                    },
                    "service_type": "voice_call_intra_network"
                }
            ]
        }
    }


class EvaluationResult(BaseModel):
    """Result of SLA evaluation."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Overall status
    is_compliant: bool = Field(..., description="Whether all SLAs are compliant")
    total_rules_evaluated: int = Field(default=0)
    rules_passed: int = Field(default=0)
    rules_violated: int = Field(default=0)

    # Violations
    violations: List[ViolationEvent] = Field(
        default_factory=list,
        description="List of violations detected"
    )

    # Summary by severity
    violations_by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of violations by severity level"
    )

    # Metadata
    evaluation_duration_ms: Optional[float] = Field(
        None,
        description="Time taken to evaluate"
    )


class RulesEngine:
    """
    Main Rules Engine for SLA monitoring.

    Evaluates metrics against SLA rules, detects violations,
    and triggers appropriate actions.
    """

    def __init__(self, actions_registry: Optional[Dict[UUID, Action]] = None):
        """
        Initialize the Rules Engine.

        Args:
            actions_registry: Dictionary of available actions keyed by ID
        """
        self.evaluator = RuleEvaluator()
        self.actions_registry = actions_registry or {}
        self.logger = logging.getLogger(__name__)

    def register_action(self, action: Action) -> None:
        """Register an action with the engine."""
        self.actions_registry[action.id] = action
        self.logger.info(f"Registered action: {action.name} ({action.id})")

    def evaluate_sla(
        self,
        sla: SLA,
        metrics: Dict[str, Any],
        customer_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate an SLA against provided metrics.

        Args:
            sla: The SLA to evaluate
            metrics: Dictionary of metric values
            customer_id: Optional customer identifier
            additional_context: Optional additional context

        Returns:
            EvaluationResult with compliance status and violations
        """
        start_time = datetime.utcnow()

        if not sla.enabled:
            self.logger.debug(f"SLA {sla.name} is disabled, skipping evaluation")
            return EvaluationResult(
                is_compliant=True,
                total_rules_evaluated=0,
                rules_passed=0,
                rules_violated=0,
            )

        violations = []
        violations_by_severity = {}
        active_rules = sla.get_active_rules()

        # Evaluate each rule
        for rule in active_rules:
            is_compliant, violation_reasons = self.evaluator.evaluate_rule(
                rule, metrics
            )

            if not is_compliant:
                # Create violation event
                violation = ViolationEvent(
                    sla_id=sla.id,
                    sla_name=sla.name,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    violation_reasons=violation_reasons,
                    metrics=metrics.copy(),
                    triggered_actions=rule.action_ids,
                    service_type=rule.service_type.value,
                    customer_id=customer_id or sla.customer_id,
                    additional_context=additional_context or {},
                )

                violations.append(violation)

                # Track by severity
                severity_key = rule.severity.value
                violations_by_severity[severity_key] = (
                    violations_by_severity.get(severity_key, 0) + 1
                )

                # Trigger actions
                self._trigger_actions(violation, rule.action_ids)

        # Calculate evaluation duration
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        # Build result
        total_rules = len(active_rules)
        rules_violated = len(violations)
        rules_passed = total_rules - rules_violated

        result = EvaluationResult(
            is_compliant=(rules_violated == 0),
            total_rules_evaluated=total_rules,
            rules_passed=rules_passed,
            rules_violated=rules_violated,
            violations=violations,
            violations_by_severity=violations_by_severity,
            evaluation_duration_ms=duration_ms,
        )

        return result

    def evaluate_multiple_slas(
        self,
        slas: List[SLA],
        metrics: Dict[str, Any],
        customer_id: Optional[str] = None,
    ) -> Dict[UUID, EvaluationResult]:
        """
        Evaluate multiple SLAs against the same metrics.

        Args:
            slas: List of SLAs to evaluate
            metrics: Dictionary of metric values
            customer_id: Optional customer identifier

        Returns:
            Dictionary mapping SLA IDs to evaluation results
        """
        results = {}

        for sla in slas:
            result = self.evaluate_sla(sla, metrics, customer_id)
            results[sla.id] = result

        return results

    def _trigger_actions(
        self,
        violation: ViolationEvent,
        action_ids: List[UUID],
    ) -> None:
        """
        Trigger actions in response to a violation.

        Args:
            violation: The violation event
            action_ids: List of action IDs to trigger
        """
        for action_id in action_ids:
            action = self.actions_registry.get(action_id)

            if not action:
                self.logger.warning(
                    f"Action {action_id} not found in registry, skipping"
                )
                continue

            if not action.enabled:
                self.logger.debug(f"Action {action.name} is disabled, skipping")
                continue

            try:
                self._execute_action(action, violation)
            except Exception as e:
                self.logger.error(
                    f"Error executing action {action.name}: {e}",
                    exc_info=True
                )

                # Retry if configured
                if action.retry_on_failure:
                    self._retry_action(action, violation)

    def _execute_action(self, action: Action, violation: ViolationEvent) -> None:
        """
        Execute a single action.

        This is a placeholder that should be extended based on action type.

        Args:
            action: The action to execute
            violation: The violation event that triggered the action
        """
        self.logger.info(
            f"Executing action '{action.name}' ({action.action_type}) "
            f"for violation of rule '{violation.rule_name}'"
        )

        # Log the violation for now
        # In a full implementation, this would:
        # - Send emails/SMS/webhooks
        # - Create incidents
        # - Record metrics
        # - etc.

        self.logger.warning(
            f"SLA VIOLATION - "
            f"Rule: {violation.rule_name}, "
            f"Severity: {violation.severity.value}, "
            f"Reasons: {', '.join(violation.violation_reasons)}"
        )

    def _retry_action(self, action: Action, violation: ViolationEvent) -> None:
        """
        Retry a failed action.

        Args:
            action: The action to retry
            violation: The violation event
        """
        for attempt in range(action.max_retries):
            self.logger.info(
                f"Retrying action {action.name}, attempt {attempt + 1}/{action.max_retries}"
            )
            try:
                self._execute_action(action, violation)
                self.logger.info(f"Action {action.name} succeeded on retry")
                return
            except Exception as e:
                self.logger.error(f"Retry attempt {attempt + 1} failed: {e}")

        self.logger.error(
            f"Action {action.name} failed after {action.max_retries} retries"
        )
