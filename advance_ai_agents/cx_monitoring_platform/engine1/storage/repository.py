"""
Repository pattern for SLA and Action storage.

Provides abstraction for storing and retrieving SLAs, rules, and actions.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from ..models import SLA, Action, ServiceType, SeverityLevel, SLARule


class SLARepository(ABC):
    """Abstract base class for SLA storage."""

    @abstractmethod
    def create_sla(self, sla: SLA) -> SLA:
        """Create a new SLA."""
        pass

    @abstractmethod
    def get_sla(self, sla_id: UUID) -> Optional[SLA]:
        """Get an SLA by ID."""
        pass

    @abstractmethod
    def get_all_slas(self, enabled_only: bool = False) -> List[SLA]:
        """Get all SLAs."""
        pass

    @abstractmethod
    def get_slas_by_service_type(
        self, service_type: ServiceType, enabled_only: bool = False
    ) -> List[SLA]:
        """Get SLAs filtered by service type."""
        pass

    @abstractmethod
    def get_slas_by_customer(
        self, customer_id: str, enabled_only: bool = False
    ) -> List[SLA]:
        """Get SLAs for a specific customer."""
        pass

    @abstractmethod
    def update_sla(self, sla_id: UUID, sla: SLA) -> Optional[SLA]:
        """Update an existing SLA."""
        pass

    @abstractmethod
    def delete_sla(self, sla_id: UUID) -> bool:
        """Delete an SLA."""
        pass

    @abstractmethod
    def create_action(self, action: Action) -> Action:
        """Create a new action."""
        pass

    @abstractmethod
    def get_action(self, action_id: UUID) -> Optional[Action]:
        """Get an action by ID."""
        pass

    @abstractmethod
    def get_all_actions(self, enabled_only: bool = False) -> List[Action]:
        """Get all actions."""
        pass

    @abstractmethod
    def update_action(self, action_id: UUID, action: Action) -> Optional[Action]:
        """Update an existing action."""
        pass

    @abstractmethod
    def delete_action(self, action_id: UUID) -> bool:
        """Delete an action."""
        pass


class InMemorySLARepository(SLARepository):
    """
    In-memory implementation of SLA repository.

    Useful for testing and development.
    """

    def __init__(self):
        self._slas: Dict[UUID, SLA] = {}
        self._actions: Dict[UUID, Action] = {}

    def create_sla(self, sla: SLA) -> SLA:
        """Create a new SLA."""
        sla.created_at = datetime.utcnow()
        sla.updated_at = datetime.utcnow()
        self._slas[sla.id] = sla
        return sla

    def get_sla(self, sla_id: UUID) -> Optional[SLA]:
        """Get an SLA by ID."""
        return self._slas.get(sla_id)

    def get_all_slas(self, enabled_only: bool = False) -> List[SLA]:
        """Get all SLAs."""
        slas = list(self._slas.values())
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def get_slas_by_service_type(
        self, service_type: ServiceType, enabled_only: bool = False
    ) -> List[SLA]:
        """Get SLAs filtered by service type."""
        slas = [sla for sla in self._slas.values() if sla.service_type == service_type]
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def get_slas_by_customer(
        self, customer_id: str, enabled_only: bool = False
    ) -> List[SLA]:
        """Get SLAs for a specific customer."""
        slas = [
            sla for sla in self._slas.values() if sla.customer_id == customer_id
        ]
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def update_sla(self, sla_id: UUID, sla: SLA) -> Optional[SLA]:
        """Update an existing SLA."""
        if sla_id not in self._slas:
            return None

        sla.updated_at = datetime.utcnow()
        self._slas[sla_id] = sla
        return sla

    def delete_sla(self, sla_id: UUID) -> bool:
        """Delete an SLA."""
        if sla_id in self._slas:
            del self._slas[sla_id]
            return True
        return False

    def create_action(self, action: Action) -> Action:
        """Create a new action."""
        action.created_at = datetime.utcnow()
        action.updated_at = datetime.utcnow()
        self._actions[action.id] = action
        return action

    def get_action(self, action_id: UUID) -> Optional[Action]:
        """Get an action by ID."""
        return self._actions.get(action_id)

    def get_all_actions(self, enabled_only: bool = False) -> List[Action]:
        """Get all actions."""
        actions = list(self._actions.values())
        if enabled_only:
            actions = [action for action in actions if action.enabled]
        return actions

    def update_action(self, action_id: UUID, action: Action) -> Optional[Action]:
        """Update an existing action."""
        if action_id not in self._actions:
            return None

        action.updated_at = datetime.utcnow()
        self._actions[action_id] = action
        return action

    def delete_action(self, action_id: UUID) -> bool:
        """Delete an action."""
        if action_id in self._actions:
            del self._actions[action_id]
            return True
        return False

    def get_stats(self) -> Dict:
        """Get repository statistics."""
        return {
            "total_slas": len(self._slas),
            "enabled_slas": len([sla for sla in self._slas.values() if sla.enabled]),
            "total_actions": len(self._actions),
            "enabled_actions": len(
                [action for action in self._actions.values() if action.enabled]
            ),
        }


class JSONFileSLARepository(SLARepository):
    """
    File-based JSON repository for SLAs.

    Persists SLAs and actions to JSON files.
    """

    def __init__(self, storage_dir: str = "./data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.slas_file = self.storage_dir / "slas.json"
        self.actions_file = self.storage_dir / "actions.json"

        # Load existing data
        self._slas = self._load_slas()
        self._actions = self._load_actions()

    def _load_slas(self) -> Dict[UUID, SLA]:
        """Load SLAs from file."""
        if not self.slas_file.exists():
            return {}

        with open(self.slas_file, "r") as f:
            data = json.load(f)

        slas = {}
        for sla_data in data:
            sla = SLA.model_validate(sla_data)
            slas[sla.id] = sla

        return slas

    def _save_slas(self) -> None:
        """Save SLAs to file."""
        data = [sla.model_dump(mode="json") for sla in self._slas.values()]

        with open(self.slas_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_actions(self) -> Dict[UUID, Action]:
        """Load actions from file."""
        if not self.actions_file.exists():
            return {}

        with open(self.actions_file, "r") as f:
            data = json.load(f)

        actions = {}
        for action_data in data:
            action = Action.model_validate(action_data)
            actions[action.id] = action

        return actions

    def _save_actions(self) -> None:
        """Save actions to file."""
        data = [action.model_dump(mode="json") for action in self._actions.values()]

        with open(self.actions_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    # Implement all abstract methods using the in-memory dict + file persistence
    def create_sla(self, sla: SLA) -> SLA:
        sla.created_at = datetime.utcnow()
        sla.updated_at = datetime.utcnow()
        self._slas[sla.id] = sla
        self._save_slas()
        return sla

    def get_sla(self, sla_id: UUID) -> Optional[SLA]:
        return self._slas.get(sla_id)

    def get_all_slas(self, enabled_only: bool = False) -> List[SLA]:
        slas = list(self._slas.values())
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def get_slas_by_service_type(
        self, service_type: ServiceType, enabled_only: bool = False
    ) -> List[SLA]:
        slas = [sla for sla in self._slas.values() if sla.service_type == service_type]
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def get_slas_by_customer(
        self, customer_id: str, enabled_only: bool = False
    ) -> List[SLA]:
        slas = [sla for sla in self._slas.values() if sla.customer_id == customer_id]
        if enabled_only:
            slas = [sla for sla in slas if sla.enabled]
        return slas

    def update_sla(self, sla_id: UUID, sla: SLA) -> Optional[SLA]:
        if sla_id not in self._slas:
            return None
        sla.updated_at = datetime.utcnow()
        self._slas[sla_id] = sla
        self._save_slas()
        return sla

    def delete_sla(self, sla_id: UUID) -> bool:
        if sla_id in self._slas:
            del self._slas[sla_id]
            self._save_slas()
            return True
        return False

    def create_action(self, action: Action) -> Action:
        action.created_at = datetime.utcnow()
        action.updated_at = datetime.utcnow()
        self._actions[action.id] = action
        self._save_actions()
        return action

    def get_action(self, action_id: UUID) -> Optional[Action]:
        return self._actions.get(action_id)

    def get_all_actions(self, enabled_only: bool = False) -> List[Action]:
        actions = list(self._actions.values())
        if enabled_only:
            actions = [action for action in actions if action.enabled]
        return actions

    def update_action(self, action_id: UUID, action: Action) -> Optional[Action]:
        if action_id not in self._actions:
            return None
        action.updated_at = datetime.utcnow()
        self._actions[action_id] = action
        self._save_actions()
        return action

    def delete_action(self, action_id: UUID) -> bool:
        if action_id in self._actions:
            del self._actions[action_id]
            self._save_actions()
            return True
        return False
