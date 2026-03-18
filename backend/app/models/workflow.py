from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Index, JSON, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class RequisitionStatus(str, PyEnum):
    DRAFT = "draft"           # 草稿
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"     # 已拒绝
    PARTIAL = "partial"       # 部分批准
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消


class Requisition(Base):
    __tablename__ = "requisitions"
    
    id = Column(Integer, primary_key=True, index=True)
    req_no = Column(String(50), unique=True, nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.DRAFT)
    total_amount = Column(Numeric(15, 2), default=0)
    purpose = Column(Text)
    expected_date = Column(DateTime, nullable=True)
    remarks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("RequisitionItem", back_populates="requisition", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_req_status_dept', 'status', 'department_id'),
        Index('ix_req_applicant_status', 'applicant_id', 'status'),
    )


class RequisitionItem(Base):
    __tablename__ = "requisition_items"
    
    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    quantity_requested = Column(Numeric(15, 3), nullable=False)
    quantity_approved = Column(Numeric(15, 3), default=0)
    quantity_issued = Column(Numeric(15, 3), default=0)
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.PENDING)
    remarks = Column(Text)
    
    requisition = relationship("Requisition", back_populates="items")


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"))
    business_type = Column(String(50), nullable=False)  # requisition, transfer, etc.
    business_id = Column(Integer, nullable=False)
    current_step = Column(Integer, default=1)
    status = Column(String(20), default="running")  # running, completed, rejected
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    tasks = relationship("ApprovalTask", back_populates="instance")


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("approval_instances.id"))
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, default=1)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(20), nullable=True)  # approve, reject, transfer
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    instance = relationship("ApprovalInstance", back_populates="tasks")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    business_type = Column(String(50), nullable=False)
    description = Column(Text)
    steps = Column(JSON)  # [{"order": 1, "name": "部门经理审批", "approver_type": "role", "approver_id": 1}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
