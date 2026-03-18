from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Index, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    address = Column(Text)
    manager_id = Column(Integer, ForeignKey("users.id"))
    contact_phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    locations = relationship("Location", back_populates="warehouse")


class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    path = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    warehouse = relationship("Warehouse", back_populates="locations")
    parent = relationship("Location", remote_side="Location.id")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    level = Column(Integer, default=1)
    path = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    children = relationship("Category", backref="parent", remote_side=[id])
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    spec = Column(String(500))  # 规格
    unit = Column(String(20), default="件")
    barcode = Column(String(100), nullable=True, index=True)
    description = Column(Text)
    min_stock = Column(Numeric(15, 3), default=0)  # 安全库存
    max_stock = Column(Numeric(15, 3), default=0)  # 最大库存
    is_batch_managed = Column(Boolean, default=False)  # 是否批次管理
    is_serialized = Column(Boolean, default=False)  # 是否序列号管理
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")
    
    __table_args__ = (
        Index('ix_products_cat_active', 'category_id', 'is_active'),
    )


class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("product_batches.id"), nullable=True)
    quantity = Column(Numeric(15, 3), default=0)  # 总数量
    locked_quantity = Column(Numeric(15, 3), default=0)  # 锁定数量（审批中）
    available_quantity = Column(Numeric(15, 3), default=0)  # 可用数量
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    product = relationship("Product", back_populates="inventory")
    
    __table_args__ = (
        Index('ix_inventory_product_wh', 'product_id', 'warehouse_id'),
        Index('ix_inventory_available', 'available_quantity'),
    )


class ProductBatch(Base):
    __tablename__ = "product_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    batch_no = Column(String(100), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    production_date = Column(DateTime)
    expiry_date = Column(DateTime)
    quantity_received = Column(Numeric(15, 3))
    quantity_remaining = Column(Numeric(15, 3))
    created_at = Column(DateTime, default=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
