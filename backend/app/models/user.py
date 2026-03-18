from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Index, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    level = Column(Integer, default=1)
    path = Column(String(500))  # 层级路径，如: /1/2/3/
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    children = relationship("Organization", backref="parent", remote_side=[id])
    departments = relationship("Department", back_populates="organization")


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="departments")
    users = relationship("User", back_populates="department")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # LDAP用户可为空
    department_id = Column(Integer, ForeignKey("departments.id"))
    ad_guid = Column(String(100), nullable=True)  # AD域GUID
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = relationship("Department", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    __table_args__ = (
        Index('ix_users_dept_active', 'department_id', 'is_active'),
    )


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(JSON, default=list)  # ["inventory:read", "inventory:write"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
