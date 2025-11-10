"""
Core evaluation logic for SLA rules and conditions.

Evaluates metrics against defined thresholds and conditions.
"""

from typing import Any, Dict, List, Optional, Union

from ..models import (
    ComparisonOperator,
    MetricType,
    RuleCondition,
    SLARule,
)


class MetricEvaluator:
    """Evaluates individual metric values against conditions."""

    @staticmethod
    def evaluate(
        metric_value: Union[float, int],
        operator: ComparisonOperator,
        threshold: Union[float, int, List[Union[float, int]]],
    ) -> bool:
        """
        Evaluate a metric value against a threshold using an operator.

        Args:
            metric_value: The measured metric value
            operator: Comparison operator
            threshold: Threshold value(s) to compare against

        Returns:
            True if condition is met (no violation), False if violated
        """
        try:
            if operator == ComparisonOperator.GREATER_THAN:
                return metric_value > threshold

            elif operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                return metric_value >= threshold

            elif operator == ComparisonOperator.LESS_THAN:
                return metric_value < threshold

            elif operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
                return metric_value <= threshold

            elif operator == ComparisonOperator.EQUAL:
                return metric_value == threshold

            elif operator == ComparisonOperator.NOT_EQUAL:
                return metric_value != threshold

            elif operator == ComparisonOperator.IN_RANGE:
                if not isinstance(threshold, list) or len(threshold) != 2:
                    raise ValueError("IN_RANGE requires threshold as [min, max]")
                return threshold[0] <= metric_value <= threshold[1]

            elif operator == ComparisonOperator.OUT_OF_RANGE:
                if not isinstance(threshold, list) or len(threshold) != 2:
                    raise ValueError("OUT_OF_RANGE requires threshold as [min, max]")
                return metric_value < threshold[0] or metric_value > threshold[1]

            else:
                raise ValueError(f"Unsupported operator: {operator}")

        except Exception as e:
            raise ValueError(f"Error evaluating metric: {e}")


class RuleEvaluator:
    """Evaluates SLA rules against metric data."""

    def __init__(self):
        self.metric_evaluator = MetricEvaluator()

    def evaluate_condition(
        self,
        condition: RuleCondition,
        metrics: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluate a single rule condition.

        Args:
            condition: The condition to evaluate
            metrics: Dictionary of metric values

        Returns:
            Tuple of (is_met, reason_if_not_met)
            - is_met: True if condition is satisfied, False if violated
            - reason_if_not_met: Explanation if condition not met
        """
        # Get the metric value
        metric_key = condition.metric_type.value
        if metric_key not in metrics:
            return False, f"Metric '{metric_key}' not found in provided data"

        metric_value = metrics[metric_key]

        # Check additional filters if specified
        if condition.additional_filters:
            for filter_key, filter_value in condition.additional_filters.items():
                if filter_key not in metrics:
                    return False, f"Filter metric '{filter_key}' not found"

                # Simple equality check for filters
                if metrics[filter_key] != filter_value:
                    return True, None  # Filter not met, but not a violation

        # Evaluate the main condition
        try:
            is_met = self.metric_evaluator.evaluate(
                metric_value=metric_value,
                operator=condition.operator,
                threshold=condition.threshold,
            )

            if is_met:
                return True, None
            else:
                reason = (
                    f"{condition.description}: "
                    f"{metric_value} {condition.operator.value} {condition.threshold} "
                    f"(VIOLATED)"
                )
                return False, reason

        except Exception as e:
            return False, f"Error evaluating condition: {str(e)}"

    def evaluate_rule(
        self,
        rule: SLARule,
        metrics: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """
        Evaluate an entire SLA rule.

        Args:
            rule: The SLA rule to evaluate
            metrics: Dictionary of metric values

        Returns:
            Tuple of (is_compliant, violation_reasons)
            - is_compliant: True if rule is satisfied, False if violated
            - violation_reasons: List of reasons if not compliant
        """
        if not rule.enabled:
            return True, []  # Disabled rules are always compliant

        condition_results = []
        violation_reasons = []

        # Evaluate each condition
        for condition in rule.conditions:
            is_met, reason = self.evaluate_condition(condition, metrics)
            condition_results.append(is_met)

            if not is_met and reason:
                violation_reasons.append(reason)

        # Apply condition logic (AND/OR)
        if rule.condition_logic == "AND":
            is_compliant = all(condition_results)
        else:  # OR
            is_compliant = any(condition_results)

        return is_compliant, violation_reasons

    def batch_evaluate_rules(
        self,
        rules: List[SLARule],
        metrics: Dict[str, Any],
    ) -> Dict[str, tuple[bool, List[str]]]:
        """
        Evaluate multiple rules against the same metrics.

        Args:
            rules: List of rules to evaluate
            metrics: Dictionary of metric values

        Returns:
            Dictionary mapping rule IDs to (is_compliant, violation_reasons)
        """
        results = {}

        for rule in rules:
            is_compliant, reasons = self.evaluate_rule(rule, metrics)
            results[str(rule.id)] = (is_compliant, reasons)

        return results
