from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from datetime import datetime


@dataclass
class ErrorEntry:
    time_s: int
    errorCode: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ErrorEntry':
        return ErrorEntry(
            time_s=data['time_s'],
            errorCode=data['errorCode']
        )


@dataclass
class DeskConfig:
    name: str
    manufacturer: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DeskConfig':
        return DeskConfig(
            name=data['name'],
            manufacturer=data['manufacturer']
        )


@dataclass
class DeskState:
    position_mm: int
    speed_mms: int
    status: str
    isPositionLost: bool
    isOverloadProtectionUp: bool
    isOverloadProtectionDown: bool
    isAntiCollision: bool

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DeskState':
        return DeskState(
            position_mm=data['position_mm'],
            speed_mms=data['speed_mms'],
            status=data['status'],
            isPositionLost=data['isPositionLost'],
            isOverloadProtectionUp=data['isOverloadProtectionUp'],
            isOverloadProtectionDown=data['isOverloadProtectionDown'],
            isAntiCollision=data['isAntiCollision']
        )


@dataclass
class DeskUsage:
    activationsCounter: int
    sitStandCounter: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DeskUsage':
        return DeskUsage(
            activationsCounter=data['activationsCounter'],
            sitStandCounter=data['sitStandCounter']
        )


@dataclass
class Desk:
    config: DeskConfig
    state: DeskState
    usage: DeskUsage
    lastErrors: List[ErrorEntry]

    clock_s: Optional[int] = None
    user: Optional[str] = None

    mac_address: Optional[str] = None
    parsed_at: Optional[datetime] = field(default_factory=datetime.now)

    @classmethod
    def from_json(cls, json_str: str, mac_address: Optional[str] = None, user: Optional[str] = None) -> 'Desk':
        """Parse a Desk instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data, mac_address=mac_address, user=user)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], mac_address: Optional[str] = None, user: Optional[str] = None) -> 'Desk':
        """Parse a Desk instance from a dictionary."""
        return cls(
            config=DeskConfig.from_dict(data['config']),
            state=DeskState.from_dict(data['state']),
            usage=DeskUsage.from_dict(data['usage']),
            lastErrors=[ErrorEntry.from_dict(err) for err in data.get('lastErrors', [])],
            user=user,
            mac_address=mac_address,
            parsed_at=datetime.now()
        )

    def is_sitting_height(self, tolerance_mm: int = 50) -> bool:
        """Check if desk is likely in sitting position (~680 mm ± tolerance)."""
        return 630 <= self.state.position_mm <= 730

    def is_standing_height(self, tolerance_mm: int = 100) -> bool:
        """Check if desk is likely in standing position (>1000 mm)."""
        return self.state.position_mm > 1000

    def has_errors(self) -> bool:
        """Check if any errors are recorded."""
        return len(self.lastErrors) > 0

    def latest_error_time(self) -> Optional[int]:
        """Return the most recent error time in seconds (relative to desk clock)."""
        if not self.lastErrors:
            return None
        return max(err.time_s for err in self.lastErrors)

    def is_in_collision(self) -> bool:
        """Check if desk is currently in collision state."""
        return self.state.status == "Collision" and self.state.isAntiCollision

    def __str__(self) -> str:
        user_str = f", user={self.user}" if self.user else ""
        mac_str = f" ({self.mac_address})" if self.mac_address else ""
        return f"Desk({self.config.name}{mac_str}: {self.state.position_mm}mm, {self.state.status}{user_str})"