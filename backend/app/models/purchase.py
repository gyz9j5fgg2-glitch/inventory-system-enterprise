from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Index, JSON, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class RequisitionStatus(str, PyEnum):
    DRAFT = "draft"           # 草稿
    SUBMITTED = "submitted"   # 已提交
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"     # 已拒绝
    SHIPPED = "shipped"       # 已发货
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消


class Requisition(Base):
    __tablename__ = "requisitions"
    
    id = Column(Integer, primary_key=True, index=True)
    req_no = Column(String(50), unique=True, nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.DRAFT)
    
    # 申请信息
    purpose = Column(Text)
    expected_date = Column(DateTime, nullable=True)
    remarks = Column(Text)
    
    # 审批信息
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_remarks = Column(Text)
    
    # 发货信息
    shipper_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    ship_remarks = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("RequisitionItem", back_populates="requisition", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_req_status_applicant', 'status', 'applicant_id'),
        Index('ix_req_status_approver', 'status', 'approver_id'),
    )


class RequisitionItem(Base):
    __tablename__ = "requisition_items"
    
    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("requisitions.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    
    # 申请数量
    quantity_requested = Column(Numeric(15, 3), nullable=False)
    quantity_approved = Column(Numeric(15, 3), default=0)
    quantity_shipped = Column(Numeric(15, 3), default=0)
    
    # 实际发货信息
    shipped_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    
    remarks = Column(Text)
    
    requisition = relationship("Requisition", back_populates="items")


class PurchaseOrderStatus(str, PyEnum):
    DRAFT = "draft"           # 草稿
    ORDERED = "ordered"       # 已下单
    PARTIAL = "partial"       # 部分到货
    RECEIVED = "received"     # 全部到货
    CANCELLED = "cancelled"   # 已取消


class PurchaseOrder(Base):
    """采购订单"""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_no = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    # 订单信息
    order_date = Column(DateTime, nullable=False)
    expected_date = Column(DateTime, nullable=True)
    total_amount = Column(Numeric(15, 2), default=0)
    
    # 状态
    status = Column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT)
    
    # 备注
    remarks = Column(Text)
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    receiving_records = relationship("ReceivingRecord", back_populates="purchase_order")


class PurchaseOrderItem(Base):
    """采购订单明细"""
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # 采购数量
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    
    # 已到货数量
    received_qty = Column(Numeric(15, 3), default=0)
    
    # 目标仓库
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    
    purchase_order = relationship("PurchaseOrder", back_populates="items")


class ReceivingRecord(Base):
    """入库记录"""
    __tablename__ = "receiving_records"
    
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    
    # 入库数量
    quantity = Column(Numeric(15, 3), nullable=False)
    
    # 入库信息
    received_by = Column(Integer, ForeignKey("users.id"))
    received_at = Column(DateTime, default=datetime.utcnow)
    remarks = Column(Text)
    
    purchase_order = relationship("PurchaseOrder", back_populates="receiving_records")
