
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey, Table, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

# Association tables
role_operations = Table(
    'role_operations', Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id')),
    Column('operation_id', UUID(as_uuid=True), ForeignKey('operations.id'))
)

user_zone_roles = Table(
    'user_zone_roles', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('zone_id', UUID(as_uuid=True), ForeignKey('zones.id')),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id')),
    Column('weight', Float, default=1.0)
)

class ZoneModel(Base):
    __tablename__ = 'zones'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent = relationship("ZoneModel", remote_side=[id], backref="children")
    roles = relationship("RoleModel", back_populates="zone")
    applications = relationship("ApplicationModel", back_populates="owning_zone")
    users = relationship("UserModel", secondary=user_zone_roles, viewonly=True)

class RoleModel(Base):
    __tablename__ = 'roles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    zone = relationship("ZoneModel", back_populates="roles")
    base_permissions = relationship("OperationModel", secondary=role_operations)

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String)
    attributes = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    zone_roles = relationship("UserZoneRole", back_populates="user")

class UserZoneRole(Base):
    __tablename__ = 'user_zone_roles_table'
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    zone_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
    weight = Column(Float, default=1.0)
    user = relationship("UserModel", back_populates="zone_roles")
    zone = relationship("ZoneModel")
    role = relationship("RoleModel")

class ApplicationModel(Base):
    __tablename__ = 'applications'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owning_zone_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owning_zone = relationship("ZoneModel", back_populates="applications")
    operations = relationship("OperationModel", back_populates="app")

class OperationModel(Base):
    __tablename__ = 'operations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    app_id = Column(UUID(as_uuid=True), ForeignKey('applications.id'), nullable=False)
    method = Column(String)
    app = relationship("ApplicationModel", back_populates="operations")

class GammaMappingModel(Base):
    __tablename__ = 'gamma_mappings'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_zone_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), nullable=False)
    child_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    parent_zone_id = Column(UUID(as_uuid=True), ForeignKey('zones.id'), nullable=False)
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    weight = Column(Float, default=1.0)
    priority = Column(Integer, default=0)

class ConstraintModel(Base):
    __tablename__ = 'constraints'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    type = Column(String) # identity, trigger, goal, access
    target = Column(JSON)
    condition = Column(String)
    priority = Column(Integer, default=0)

class Storage:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    def get_session(self):
        return self.Session()
    def save_system(self, system):
        # In a real implementation, would convert core models to SQLAlchemy models and save
        pass
    def get_gamma_mappings(self, child_zone_id=None, child_role_id=None):
        session = self.get_session()
        query = session.query(GammaMappingModel)
        if child_zone_id:
            query = query.filter_by(child_zone_id=child_zone_id)
        if child_role_id:
            query = query.filter_by(child_role_id=child_role_id)
        return query.all()
    def get_constraints(self, type=None, target_roles=None, target_operations=None):
        session = self.get_session()
        query = session.query(ConstraintModel)
        if type:
            query = query.filter_by(type=type)
        # Target filtering would be more complex
        return query.all()
    def get_role(self, role_id):
        session = self.get_session()
        return session.query(RoleModel).get(role_id)
    def get_recent_violations(self, limit=100):
        # Placeholder
        return []
