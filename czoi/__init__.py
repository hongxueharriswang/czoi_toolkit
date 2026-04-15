# top-level
# czoa/__init__.py
"""
CZOA Toolkit - Constrained Zoned-Object Architecture

A Python implementation of the CZOA 11-tuple formalism for building
secure, adaptive, intelligent systems with recursive zones, first-class
properties, and neural components.

Author: Harris Wang
Version: 1.0.0
"""

from czoi.core.types import PropertyType, PropagationPolicy, DaemonAction, ConstraintType
from czoi.core.exceptions import (
    CZOIError,
    ZoneNotFoundError,
    PropertyNotFoundError,
    PermissionDeniedError,
    ConstraintViolationError,
    DaemonBlockError,
)
from czoi.operations import Operation
from czoi.zones import Zone, AtomicZone, CompositeZone
from czoi.properties import Property, PropertyStore
from czoi.roles import Role, User
from czoi.constraints.engine import (
    Constraint,
    IdentityConstraint,
    TriggerConstraint,
    GoalConstraint,
    AccessConstraint,
    ConstraintEngine,
)
from czoi.neural import NeuralComponent, PropertyPredictor, AnomalyDetector
from czoi.embedding.service import EmbeddingService
from czoi.daemons.base import Daemon, SecurityDaemon, PropertyDaemon
from czoi.daemons.manager import DaemonManager
from czoi.permissions import PermissionEngine
from czoi.toolkit import CZOASystem, CZOIToolkit
from czoi.roles.application import Application   # add this line

__all__ = [
    # Types
    "PropertyType",
    "PropagationPolicy",
    "DaemonAction",
    "ConstraintType",
    # Exceptions
    "CZOAError",
    "ZoneNotFoundError",
    "PropertyNotFoundError",
    "PermissionDeniedError",
    "ConstraintViolationError",
    "DaemonBlockError",
    # Zones
    "Zone",
    "AtomicZone",
    "CompositeZone",
    # Properties
    "Property",
    "PropertyStore",
    # Roles & Users
    "Role",
    "User",
    # Constraints
    "Constraint",
    "IdentityConstraint",
    "TriggerConstraint",
    "GoalConstraint",
    "AccessConstraint",
    "ConstraintEngine",
    # Neural
    "NeuralComponent",
    "PropertyPredictor",
    "AnomalyDetector",
    # Embedding
    "EmbeddingService",
    # Daemons
    "Daemon",
    "SecurityDaemon",
    "PropertyDaemon",
    "DaemonManager",
    # Permissions
    "PermissionEngine",
    # System
    "CZOASystem",
    "CZOAToolkit",
    "Application",
    "Operation",
    "CZOIError",
]

__version__ = "1.0.0"