from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"))
    operator_name = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # 分区表建议按 created_at 分区
    )


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), nullable=False)  # IN, OUT, TRANSFER, ADJUST
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id"), nullable=True)
    quantity = Column(Integer, nullable=False)  # 正数入库，负数出库
    before_qty = Column(Integer, nullable=False)
    after_qty = Column(Integer, nullable=False)
    reference_type = Column(String(50))  # requisition, purchase_order, etc.
    reference_id = Column(Integer)
    reference_no = Column(String(100))
    operator_id = Column(Integer, ForeignKey("users.id"))
    operator_name = Column(String(100))
    remarks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        # 按 created_at 分区，提升历史查询性能
    )
