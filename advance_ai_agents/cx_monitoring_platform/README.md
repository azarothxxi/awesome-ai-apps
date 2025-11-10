# CX Monitoring Platform - Engine 1: SLA Library and Rules Platform

A comprehensive, pro-active customer experience monitoring platform that actively monitors customer usage against SLA rules, automatically flagging service degradation events, issues, or failures.

## Overview

Engine 1 serves as the **SLA Library and Rules Platform** - the foundation of the CX monitoring system. It hosts:

- **SLA Definitions**: All service level agreements and quality thresholds
- **Rules Engine**: Specific rules that govern service quality
- **Action Triggers**: Automated responses to SLA violations
- **Evaluation API**: Real-time metrics evaluation against SLA rules

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Engine 1: SLA Library                     │
│                    and Rules Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   SLA Models │  │ Rules Engine │  │   Actions    │     │
│  │   (Pydantic) │  │  (Evaluator) │  │  (Triggers)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Storage    │  │  FastAPI     │  │   Examples   │     │
│  │ (Repository) │  │    (API)     │  │   (Samples)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Comprehensive SLA Modeling

Define service level agreements with:
- Multiple service types (voice calls, data sessions, APIs, etc.)
- Flexible rule conditions with multiple metrics
- Severity levels (Critical, Major, Minor, Warning, Info)
- Time windows for metric evaluation
- Customer-specific SLAs

### 2. Powerful Rules Engine

Evaluate metrics against SLA rules with:
- Multiple comparison operators (>, >=, <, <=, ==, !=, in_range, out_of_range)
- Complex condition logic (AND/OR)
- Batch evaluation across multiple SLAs
- Real-time violation detection

### 3. Automated Actions

Trigger actions on SLA violations:
- **Alerts**: Email, SMS, webhooks
- **Incidents**: Auto-create tickets (JIRA, ServiceNow)
- **Logging**: File, stdout, Elasticsearch
- **Metrics**: Prometheus, DataDog, CloudWatch
- **Escalation**: Multi-level escalation paths

### 4. REST API

Complete FastAPI-based API for:
- SLA management (CRUD operations)
- Action configuration
- Real-time evaluation
- Batch processing
- Statistics and monitoring

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Setup

1. **Navigate to the project directory:**

```bash
cd advance_ai_agents/cx_monitoring_platform
```

2. **Install dependencies:**

```bash
# Using pip
pip install -e .

# Or using uv (faster)
uv pip install -e .
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Quick Start

### 1. Start the API Server

```bash
# From the cx_monitoring_platform directory
uvicorn main:app --reload

# Server will start at http://localhost:8000
```

### 2. Load Example Data

```bash
python examples/load_examples.py
```

### 3. Access API Documentation

Open your browser to:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Usage Examples

### Example 1: Voice Call SLA

Based on your requirements, here's a voice call SLA with three rules:

**Service Type**: Outgoing Call (Intra-Network)

**Rule 1: Connection Time**
- **Threshold**: No more than 3 seconds to connect and ring destination
- **Severity**: Minor
- **Action**: Flag incident count

**Rule 2: Dropped Calls**
- **Threshold**: No more than 3 network-caused dropped calls per day (4+ bar signal)
- **Severity**: Major
- **Action**: Create incident ticket, send alert

**Rule 3: Failed Connect Attempts**
- **Threshold**: No more than 1 failed call per 10 attempts (10% failure rate)
- **Severity**: Major
- **Action**: Create incident ticket, send alert

### Example 2: Creating an SLA via API

```bash
curl -X POST "http://localhost:8000/api/v1/slas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Voice Service SLA",
    "description": "SLA for premium voice call services",
    "service_type": "voice_call_intra_network",
    "version": "1.0.0",
    "rules": [
      {
        "name": "Call Connection Time",
        "description": "Maximum 3 seconds to connect",
        "service_type": "voice_call_intra_network",
        "conditions": [
          {
            "metric_type": "connection_time",
            "operator": "<=",
            "threshold": 3,
            "description": "Connection time must be 3s or less"
          }
        ],
        "severity": "minor",
        "enabled": true
      }
    ]
  }'
```

### Example 3: Evaluating Metrics Against SLA

```bash
curl -X POST "http://localhost:8000/api/v1/evaluation/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "sla_id": "YOUR_SLA_ID",
    "metrics": {
      "connection_time": 4.2,
      "signal_strength": 4,
      "dropped_count": 2,
      "failure_rate": 0.08
    },
    "customer_id": "customer_123"
  }'
```

**Response (Violation Detected):**

```json
{
  "timestamp": "2025-11-10T12:34:56.789Z",
  "is_compliant": false,
  "total_rules_evaluated": 3,
  "rules_passed": 2,
  "rules_violated": 1,
  "violations": [
    {
      "id": "violation_uuid",
      "sla_name": "Premium Voice Service SLA",
      "rule_name": "Call Connection Time",
      "severity": "minor",
      "violation_reasons": [
        "Connection time must be 3s or less: 4.2 <= 3 (VIOLATED)"
      ],
      "metrics": {
        "connection_time": 4.2,
        "signal_strength": 4
      },
      "service_type": "voice_call_intra_network"
    }
  ],
  "violations_by_severity": {
    "minor": 1
  }
}
```

### Example 4: Python SDK Usage

```python
from engine1.models import SLA, SLARule, RuleCondition, Action
from engine1.rules import RulesEngine
from engine1.storage import InMemorySLARepository

# Create repository and engine
repository = InMemorySLARepository()
engine = RulesEngine()

# Create an SLA
sla = SLA(
    name="API Response Time SLA",
    description="Ensure API responds within acceptable time",
    service_type="api_endpoint",
    rules=[
        SLARule(
            name="Response Time < 500ms",
            description="API must respond in under 500ms",
            service_type="api_endpoint",
            conditions=[
                RuleCondition(
                    metric_type="response_time",
                    operator="<=",
                    threshold=500,
                    description="Response time under 500ms"
                )
            ],
            severity="major"
        )
    ]
)

# Save SLA
repository.create_sla(sla)

# Evaluate metrics
metrics = {
    "response_time": 650,  # Violates the 500ms threshold
}

result = engine.evaluate_sla(sla, metrics)

print(f"Compliant: {result.is_compliant}")
print(f"Violations: {len(result.violations)}")
```

## API Reference

### SLA Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/slas/` | Create new SLA |
| GET | `/api/v1/slas/` | List all SLAs |
| GET | `/api/v1/slas/{sla_id}` | Get specific SLA |
| PUT | `/api/v1/slas/{sla_id}` | Update SLA |
| DELETE | `/api/v1/slas/{sla_id}` | Delete SLA |
| PATCH | `/api/v1/slas/{sla_id}/enable` | Enable SLA |
| PATCH | `/api/v1/slas/{sla_id}/disable` | Disable SLA |

### Action Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/actions/` | Create new action |
| GET | `/api/v1/actions/` | List all actions |
| GET | `/api/v1/actions/{action_id}` | Get specific action |
| PUT | `/api/v1/actions/{action_id}` | Update action |
| DELETE | `/api/v1/actions/{action_id}` | Delete action |

### Evaluation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/evaluation/evaluate` | Evaluate single SLA |
| POST | `/api/v1/evaluation/batch` | Evaluate all SLAs |
| POST | `/api/v1/evaluation/rule` | Evaluate single rule |

### Health & Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stats` | Repository statistics |

## Data Models

### Service Types

- `voice_call_outgoing` / `voice_call_incoming`
- `voice_call_intra_network` / `voice_call_inter_network`
- `data_session`
- `sms_outgoing` / `sms_incoming`
- `video_call`
- `api_endpoint`
- `web_service`
- And more...

### Metric Types

**Time-based:**
- `response_time`, `connection_time`, `latency`, `duration`

**Count-based:**
- `error_count`, `failure_count`, `success_count`, `dropped_count`

**Rate-based:**
- `error_rate`, `failure_rate`, `success_rate`, `availability`

**Quality:**
- `signal_strength`, `packet_loss`, `jitter`, `bandwidth`

### Severity Levels

- `critical` - Immediate action required
- `major` - Significant impact
- `minor` - Low impact
- `warning` - Potential issue
- `info` - Informational only

### Action Types

- `alert` - Send notifications
- `email` / `sms` / `webhook` - Communication
- `create_incident` / `escalate` - Incident management
- `log` / `metric` / `flag_count` - Monitoring
- `custom` - Custom actions

## Testing

The platform includes test data in `examples/test_metrics.json`:

1. **Compliant metrics** - All rules pass
2. **Connection time violation** - Exceeds 3s threshold
3. **Dropped calls violation** - Too many dropped calls
4. **Failure rate violation** - Call failure rate exceeds 10%
5. **Multiple violations** - Multiple rules violated

Test using the evaluation endpoint with these metrics.

## Development

### Project Structure

```
cx_monitoring_platform/
├── engine1/                  # Main package
│   ├── models/              # Pydantic models
│   │   ├── sla.py          # SLA and rule models
│   │   └── actions.py      # Action models
│   ├── rules/              # Rules engine
│   │   ├── evaluator.py    # Evaluation logic
│   │   └── engine.py       # Main engine
│   ├── storage/            # Storage layer
│   │   └── repository.py   # Repository pattern
│   └── api/                # FastAPI application
│       ├── app.py          # App factory
│       └── routes/         # API routes
├── examples/               # Example SLAs and data
├── main.py                # Entry point
├── pyproject.toml         # Dependencies
└── README.md              # This file
```

### Running Tests

```bash
# TODO: Add pytest tests
pytest
```

### Code Quality

```bash
# Format code
black engine1/

# Type checking
mypy engine1/

# Linting
ruff check engine1/
```

## Roadmap

### Current: Engine 1 ✅
- [x] SLA Library and Rules Platform
- [x] REST API
- [x] In-memory and file-based storage
- [x] Example configurations

### Future Engines

- **Engine 2**: Real-time Metrics Collection and Aggregation
- **Engine 3**: Violation Detection and Alert Management
- **Engine 4**: Analytics and Reporting Dashboard
- **Engine 5**: ML-based Predictive Quality Analysis

### Enhancements
- [ ] Database storage (PostgreSQL)
- [ ] Redis caching
- [ ] Webhook action execution
- [ ] Email/SMS notifications
- [ ] JIRA/ServiceNow integration
- [ ] Metrics export (Prometheus)
- [ ] Streamlit dashboard
- [ ] Authentication & authorization
- [ ] Multi-tenancy support
- [ ] Audit logging

## Contributing

This is part of the awesome-ai-apps repository. Contributions welcome!

## License

See repository LICENSE file.

## Support

For issues and questions:
- Create an issue in the repository
- Refer to API documentation at `/docs`
- Check example configurations in `examples/`

---

**Built with**: FastAPI, Pydantic, Python 3.11+

**Part of**: CX Monitoring Platform (5-Engine Architecture)
