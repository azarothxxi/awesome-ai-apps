"""
SLA (Service Level Agreement) data models.

Defines the structure for SLA definitions, rules, conditions, and metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ServiceType(str, Enum):
    """Types of services that can be monitored."""

    VOICE_CALL_OUTGOING = "voice_call_outgoing"
    VOICE_CALL_INCOMING = "voice_call_incoming"
    VOICE_CALL_INTRA_NETWORK = "voice_call_intra_network"
    VOICE_CALL_INTER_NETWORK = "voice_call_inter_network"
    DATA_SESSION = "data_session"
    SMS_OUTGOING = "sms_outgoing"
    SMS_INCOMING = "sms_incoming"
    MMS_OUTGOING = "mms_outgoing"
    MMS_INCOMING = "mms_incoming"
    VIDEO_CALL = "video_call"
    STREAMING_VIDEO = "streaming_video"
    STREAMING_AUDIO = "streaming_audio"
    API_ENDPOINT = "api_endpoint"
    WEB_SERVICE = "web_service"
    DATABASE_QUERY = "database_query"
    FILE_TRANSFER = "file_transfer"
    CUSTOM = "custom"


class SeverityLevel(str, Enum):
    """Severity levels for SLA violations."""

    CRITICAL = "critical"  # Immediate action required
    MAJOR = "major"        # Significant impact
    MINOR = "minor"        # Low impact
    WARNING = "warning"    # Potential issue
    INFO = "info"          # Informational only


class MetricType(str, Enum):
    """Types of metrics that can be measured."""

    # Time-based metrics
    RESPONSE_TIME = "response_time"
    CONNECTION_TIME = "connection_time"
    PROCESSING_TIME = "processing_time"
    LATENCY = "latency"
    DURATION = "duration"

    # Count-based metrics
    ERROR_COUNT = "error_count"
    FAILURE_COUNT = "failure_count"
    SUCCESS_COUNT = "success_count"
    DROPPED_COUNT = "dropped_count"
    RETRY_COUNT = "retry_count"

    # Rate-based metrics
    ERROR_RATE = "error_rate"
    FAILURE_RATE = "failure_rate"
    SUCCESS_RATE = "success_rate"
    THROUGHPUT = "throughput"
    AVAILABILITY = "availability"

    # Quality metrics
    SIGNAL_STRENGTH = "signal_strength"
    PACKET_LOSS = "packet_loss"
    JITTER = "jitter"
    BANDWIDTH = "bandwidth"

    # Custom
    CUSTOM = "custom"


class ComparisonOperator(str, Enum):
    """Operators for comparing metric values."""

    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    IN_RANGE = "in_range"
    OUT_OF_RANGE = "out_of_range"


class TimeWindow(BaseModel):
    """Time window for evaluating metrics."""

    duration: int = Field(..., description="Duration in seconds", gt=0)
    unit: str = Field(default="seconds", description="Time unit")

    def to_seconds(self) -> int:
        """Convert time window to seconds."""
        unit_multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
        }
        return self.duration * unit_multipliers.get(self.unit, 1)


class RuleCondition(BaseModel):
    """A single condition within an SLA rule."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    metric_type: MetricType = Field(..., description="Type of metric to measure")
    operator: ComparisonOperator = Field(..., description="Comparison operator")
    threshold: Union[float, int, List[Union[float, int]]] = Field(
        ..., description="Threshold value(s) for comparison"
    )
    time_window: Optional[TimeWindow] = Field(
        None, description="Time window for evaluation"
    )
    additional_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional filters (e.g., signal_strength >= 4)"
    )
    description: str = Field(..., description="Human-readable description")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metric_type": "connection_time",
                    "operator": "<=",
                    "threshold": 3,
                    "time_window": {"duration": 1, "unit": "minutes"},
                    "description": "Connection time must be 3 seconds or less"
                }
            ]
        }
    }


class SLARule(BaseModel):
    """A rule that defines service level expectations."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., description="Rule name", min_length=1)
    description: str = Field(..., description="Detailed description")
    service_type: ServiceType = Field(..., description="Type of service")
    service_subtype: Optional[str] = Field(
        None, description="Optional service subtype (e.g., 'intra_network')"
    )

    # Rule conditions
    conditions: List[RuleCondition] = Field(
        ..., description="List of conditions (all must be met)", min_length=1
    )
    condition_logic: str = Field(
        default="AND",
        description="Logic for combining conditions (AND/OR)"
    )

    # Violation handling
    severity: SeverityLevel = Field(..., description="Severity when violated")
    action_ids: List[UUID] = Field(
        default_factory=list,
        description="IDs of actions to trigger on violation"
    )

    # Metadata
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(default=50, description="Rule priority (0-100)", ge=0, le=100)
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the rule")

    @field_validator('condition_logic')
    @classmethod
    def validate_condition_logic(cls, v: str) -> str:
        """Validate condition logic is either AND or OR."""
        if v.upper() not in ["AND", "OR"]:
            raise ValueError("condition_logic must be 'AND' or 'OR'")
        return v.upper()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Intra-Network Call Connection Time",
                    "description": "No more than 3 seconds to connect and ring destination number from same network",
                    "service_type": "voice_call_intra_network",
                    "conditions": [
                        {
                            "metric_type": "connection_time",
                            "operator": "<=",
                            "threshold": 3,
                            "description": "Connection time must be 3 seconds or less"
                        }
                    ],
                    "severity": "minor",
                    "enabled": True
                }
            ]
        }
    }


class SLA(BaseModel):
    """
    Service Level Agreement definition.

    Contains all rules and quality thresholds for a specific service.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., description="SLA name", min_length=1)
    description: str = Field(..., description="Detailed description")
    version: str = Field(default="1.0.0", description="SLA version")

    # Service identification
    service_type: ServiceType = Field(..., description="Primary service type")
    service_name: Optional[str] = Field(None, description="Custom service name")
    customer_id: Optional[str] = Field(None, description="Customer/tenant identifier")

    # Rules
    rules: List[SLARule] = Field(
        default_factory=list,
        description="List of SLA rules"
    )

    # Metadata
    enabled: bool = Field(default=True, description="Whether SLA is active")
    effective_date: Optional[datetime] = Field(
        None, description="When SLA becomes effective"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="When SLA expires"
    )

    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the SLA")

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format (semantic versioning)."""
        parts = v.split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Version must be in format 'X.Y.Z' (semantic versioning)")
        return v

    def get_active_rules(self) -> List[SLARule]:
        """Get all enabled rules."""
        return [rule for rule in self.rules if rule.enabled]

    def get_rules_by_severity(self, severity: SeverityLevel) -> List[SLARule]:
        """Get rules filtered by severity level."""
        return [rule for rule in self.rules if rule.severity == severity]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Premium Voice Service SLA",
                    "description": "SLA for premium voice call services",
                    "service_type": "voice_call_intra_network",
                    "version": "1.0.0",
                    "rules": [
                        {
                            "name": "Call Connection Time",
                            "description": "Maximum time to establish connection",
                            "service_type": "voice_call_intra_network",
                            "conditions": [
                                {
                                    "metric_type": "connection_time",
                                    "operator": "<=",
                                    "threshold": 3,
                                    "description": "Must connect within 3 seconds"
                                }
                            ],
                            "severity": "minor"
                        }
                    ]
                }
            ]
        }
    }
