"""
Script to load example SLAs and actions into the platform.

Usage:
    python examples/load_examples.py
"""

import json
import sys
from pathlib import Path

import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE_URL = "http://localhost:8000/api/v1"


def load_sla(sla_data: dict) -> dict:
    """Load an SLA into the platform."""
    response = httpx.post(f"{API_BASE_URL}/slas/", json=sla_data)
    response.raise_for_status()
    return response.json()


def load_action(action_data: dict) -> dict:
    """Load an action into the platform."""
    response = httpx.post(f"{API_BASE_URL}/actions/", json=action_data)
    response.raise_for_status()
    return response.json()


def main():
    """Load all example data."""
    examples_dir = Path(__file__).parent

    print("Loading example data into CX Monitoring Platform...\n")

    # Load actions first
    print("Loading actions...")
    actions_file = examples_dir / "actions.json"
    with open(actions_file) as f:
        actions_data = json.load(f)

    action_ids = []
    for action_data in actions_data:
        try:
            action = load_action(action_data)
            action_ids.append(action["id"])
            print(f"  ✓ Loaded action: {action['name']}")
        except Exception as e:
            print(f"  ✗ Failed to load action: {e}")

    print(f"\nLoaded {len(action_ids)} actions\n")

    # Load SLAs
    print("Loading SLAs...")
    sla_file = examples_dir / "voice_call_sla.json"
    with open(sla_file) as f:
        sla_data = json.load(f)

    # Assign some actions to the rules
    if action_ids and len(sla_data["rules"]) > 0:
        # Assign action IDs to rules based on severity
        for rule in sla_data["rules"]:
            if rule["severity"] == "minor":
                rule["action_ids"] = [action_ids[0]] if len(action_ids) > 0 else []
            elif rule["severity"] == "major":
                rule["action_ids"] = [action_ids[1], action_ids[2]] if len(action_ids) > 2 else []

    try:
        sla = load_sla(sla_data)
        print(f"  ✓ Loaded SLA: {sla['name']}")
        print(f"    - ID: {sla['id']}")
        print(f"    - Rules: {len(sla['rules'])}")
        sla_id = sla['id']
    except Exception as e:
        print(f"  ✗ Failed to load SLA: {e}")
        return

    print("\n" + "="*60)
    print("Example data loaded successfully!")
    print("="*60)

    print(f"\nSLA ID: {sla_id}")
    print("\nYou can now test the platform:")
    print(f"  1. View SLA: GET {API_BASE_URL}/slas/{sla_id}")
    print(f"  2. Evaluate metrics: POST {API_BASE_URL}/evaluation/evaluate")
    print(f"  3. View API docs: http://localhost:8000/docs")

    print("\nExample evaluation request:")
    print(json.dumps({
        "sla_id": sla_id,
        "metrics": {
            "connection_time": 4.2,
            "signal_strength": 4,
            "dropped_count": 2,
            "failure_rate": 0.08
        }
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("Error: Could not connect to API server.")
        print("Make sure the server is running: uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
