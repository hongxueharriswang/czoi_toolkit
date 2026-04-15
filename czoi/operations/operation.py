# czoi/operations/operation.py
from dataclasses import dataclass, field
from typing import Dict, Set, Any, Callable, Optional
from uuid import UUID, uuid4 
from zones.base import Zone

@dataclass
class Operation:
    """
    An executable operation (method) in the system.
    
    Attributes
    ----------
    name : str
        Operation name (unique within application).
    app_id : UUID
        ID of the application providing this operation.
    signature : Dict[str, str]
        Input/output types mapping.
    read_properties : Set[UUID]
        Property IDs that this operation reads.
    write_properties : Set[UUID]
        Property IDs that this operation modifies.
    precondition : Optional[Callable[[Dict], bool]]
        Boolean function over property state.
    postcondition : Optional[Callable[[Dict, Any], bool]]
        Function over (old_state, result) -> bool.
    property_condition : Optional[str]
        Expression string for property-based permission.
    required_role_ids : Set[UUID]
        Roles that have base permission for this operation.
    """
    name: str
    app_id: UUID
    signature: Dict[str, str]
    read_properties: Set[UUID] = field(default_factory=set)
    write_properties: Set[UUID] = field(default_factory=set)
    precondition: Optional[Callable[[Dict], bool]] = None
    postcondition: Optional[Callable[[Dict, Any], bool]] = None
    property_condition: Optional[str] = None
    required_role_ids: Set[UUID] = field(default_factory=set)
    
    async def execute(self, zone: 'Zone', context: Dict) -> Any:
        """
        Execute the operation (to be overridden by application logic).
        
        Parameters
        ----------
        zone : Zone
            The zone in which execution occurs.
        context : Dict
            Execution context (user, parameters, etc.).
        
        Returns
        -------
        Any
            Operation result.
        """
    name: str
    app_id: UUID
    signature: Dict[str, str] = field(default_factory=dict)
    read_properties: Set[UUID] = field(default_factory=set)
    write_properties: Set[UUID] = field(default_factory=set)
    precondition: Optional[Callable[[Dict], bool]] = None
    postcondition: Optional[Callable[[Dict, Any], bool]] = None
    property_condition: Optional[str] = None
    required_role_ids: Set[UUID] = field(default_factory=set)
    id: UUID = field(default_factory=uuid4)

    async def execute(self, zone: 'Zone', context: Dict) -> Any:
        """
        Execute the operation (to be overridden by application logic).
        
        Parameters
        ----------
        zone : Zone
            The zone in which execution occurs.
        context : Dict
            Execution context (user, parameters, etc.).
        
        Returns
        -------
        Any
            Operation result.
        """
        raise NotImplementedError("Operation.execute must be overridden by subclass")