"""
Action models for SLA violation responses.

Defines what actions should be taken when SLA rules are violated.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class ActionType(str, Enum):
    """Types of actions that can be triggered."""

    # Notification actions
    ALERT = "alert"                     # Send alert notification
    EMAIL = "email"                     # Send email
    SMS = "sms"                         # Send SMS
    WEBHOOK = "webhook"                 # Call webhook

    # Incident management
    CREATE_INCIDENT = "create_incident" # Create incident ticket
    UPDATE_INCIDENT = "update_incident" # Update existing incident
    ESCALATE = "escalate"               # Escalate to higher priority

    # Operational actions
    THROTTLE = "throttle"               # Throttle service
    CIRCUIT_BREAK = "circuit_break"     # Open circuit breaker
    FAILOVER = "failover"               # Trigger failover

    # Analytics
    LOG = "log"                         # Log event
    METRIC = "metric"                   # Record metric
    FLAG_COUNT = "flag_count"           # Increment flag counter

    # Custom
    CUSTOM = "custom"                   # Custom action


class Action(BaseModel):
    """Base action configuration."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., description="Action name", min_length=1)
    description: str = Field(..., description="Action description")
    action_type: ActionType = Field(..., description="Type of action")

    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific configuration"
    )

    # Execution settings
    enabled: bool = Field(default=True, description="Whether action is active")
    retry_on_failure: bool = Field(
        default=False,
        description="Retry action if it fails"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts",
        ge=0,
        le=10
    )
    timeout_seconds: int = Field(
        default=30,
        description="Action timeout in seconds",
        gt=0
    )

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Flag Incident Count",
                    "description": "Increment incident counter for reporting",
                    "action_type": "flag_count",
                    "config": {
                        "counter_name": "minor_violations",
                        "increment_by": 1
                    }
                }
            ]
        }
    }


class AlertAction(Action):
    """Action to send alerts through various channels."""

    action_type: ActionType = Field(default=ActionType.ALERT, frozen=True)

    # Alert configuration
    channels: List[str] = Field(
        ...,
        description="Alert channels (email, sms, slack, pagerduty, etc.)",
        min_length=1
    )
    recipients: List[str] = Field(
        ...,
        description="Alert recipients (emails, phone numbers, user IDs)",
        min_length=1
    )
    message_template: str = Field(
        ...,
        description="Alert message template with placeholders"
    )
    priority: str = Field(
        default="medium",
        description="Alert priority (low, medium, high, critical)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Send Email Alert",
                    "description": "Send email alert to operations team",
                    "channels": ["email"],
                    "recipients": ["ops@company.com", "oncall@company.com"],
                    "message_template": "SLA Violation: {rule_name} - {description}",
                    "priority": "high"
                }
            ]
        }
    }


class WebhookAction(Action):
    """Action to call a webhook endpoint."""

    action_type: ActionType = Field(default=ActionType.WEBHOOK, frozen=True)

    # Webhook configuration
    url: HttpUrl = Field(..., description="Webhook URL")
    method: str = Field(default="POST", description="HTTP method")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers"
    )
    payload_template: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload template with placeholders"
    )
    auth_type: Optional[str] = Field(
        None,
        description="Authentication type (bearer, basic, api_key)"
    )
    auth_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="Authentication credentials"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Notify Slack Channel",
                    "description": "Post violation to Slack #incidents channel",
                    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
                    "method": "POST",
                    "payload_template": {
                        "text": "SLA Violation Detected",
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Rule:* {rule_name}\n*Severity:* {severity}"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


class IncidentAction(Action):
    """Action to create or update incidents."""

    action_type: ActionType = Field(default=ActionType.CREATE_INCIDENT, frozen=True)

    # Incident configuration
    incident_system: str = Field(
        ...,
        description="Incident management system (jira, servicenow, pagerduty)"
    )
    incident_type: str = Field(
        default="sla_violation",
        description="Type of incident to create"
    )
    priority: str = Field(
        ...,
        description="Incident priority"
    )
    assignee: Optional[str] = Field(
        None,
        description="Default assignee"
    )
    title_template: str = Field(
        ...,
        description="Incident title template"
    )
    description_template: str = Field(
        ...,
        description="Incident description template"
    )
    labels: List[str] = Field(
        default_factory=list,
        description="Incident labels/tags"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Create JIRA Ticket",
                    "description": "Create incident ticket in JIRA",
                    "incident_system": "jira",
                    "incident_type": "bug",
                    "priority": "high",
                    "title_template": "[SLA] {rule_name} violation",
                    "description_template": "SLA rule '{rule_name}' was violated.\n\nSeverity: {severity}\nService: {service_type}\nTime: {timestamp}",
                    "labels": ["sla", "auto-generated"]
                }
            ]
        }
    }


class EscalationAction(Action):
    """Action to escalate issues through defined escalation paths."""

    action_type: ActionType = Field(default=ActionType.ESCALATE, frozen=True)

    # Escalation configuration
    escalation_levels: List[Dict[str, Any]] = Field(
        ...,
        description="Escalation levels with delay and recipients",
        min_length=1
    )
    current_level: int = Field(
        default=0,
        description="Current escalation level",
        ge=0
    )
    auto_escalate_after_minutes: int = Field(
        default=30,
        description="Auto-escalate after N minutes if not resolved",
        gt=0
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Multi-Level Escalation",
                    "description": "Escalate through team leads to executives",
                    "escalation_levels": [
                        {
                            "level": 1,
                            "delay_minutes": 0,
                            "recipients": ["team-lead@company.com"],
                            "message": "SLA violation requires attention"
                        },
                        {
                            "level": 2,
                            "delay_minutes": 15,
                            "recipients": ["director@company.com"],
                            "message": "ESCALATED: Unresolved SLA violation"
                        },
                        {
                            "level": 3,
                            "delay_minutes": 30,
                            "recipients": ["vp@company.com"],
                            "message": "CRITICAL: SLA violation requires executive attention"
                        }
                    ],
                    "auto_escalate_after_minutes": 15
                }
            ]
        }
    }


class LogAction(Action):
    """Action to log SLA violations."""

    action_type: ActionType = Field(default=ActionType.LOG, frozen=True)

    # Logging configuration
    log_level: str = Field(
        default="warning",
        description="Log level (debug, info, warning, error, critical)"
    )
    log_destination: str = Field(
        default="file",
        description="Log destination (file, stdout, syslog, elasticsearch)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, text, structured)"
    )
    include_context: bool = Field(
        default=True,
        description="Include full violation context in log"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Log to File",
                    "description": "Log violations to violations.log",
                    "log_level": "warning",
                    "log_destination": "file",
                    "log_format": "json",
                    "config": {
                        "file_path": "/var/log/cx-monitoring/violations.log"
                    }
                }
            ]
        }
    }


class MetricAction(Action):
    """Action to record metrics."""

    action_type: ActionType = Field(default=ActionType.METRIC, frozen=True)

    # Metric configuration
    metric_name: str = Field(..., description="Metric name")
    metric_type: str = Field(
        default="counter",
        description="Metric type (counter, gauge, histogram)"
    )
    metric_value: Optional[float] = Field(
        None,
        description="Static metric value (if not dynamic)"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels/tags"
    )
    destination: str = Field(
        default="prometheus",
        description="Metric destination (prometheus, datadog, cloudwatch)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Count Violations",
                    "description": "Increment violation counter metric",
                    "metric_name": "sla_violations_total",
                    "metric_type": "counter",
                    "metric_value": 1,
                    "labels": {
                        "severity": "minor",
                        "service_type": "voice_call"
                    },
                    "destination": "prometheus"
                }
            ]
        }
    }
