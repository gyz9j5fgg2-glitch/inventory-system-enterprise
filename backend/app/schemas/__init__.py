from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== 用户 Schema ==========

class UserBase(BaseModel):
    username: str
    email: EmailStr
    department_id: Optional[int] = None


class UserCreate(UserBase):
    password: Optional[str] = None
    role_ids: Optional[List[int]] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ========== 库存 Schema ==========

class WarehouseBase(BaseModel):
    code: str
    name: str
    location: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseResponse(WarehouseBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    sku: str
    name: str
    category_id: Optional[int] = None
    spec: Optional[str] = None
    unit: str = "件"
    barcode: Optional[str] = None
    description: Optional[str] = None
    min_stock: Optional[float] = 0
    max_stock: Optional[float] = 0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    location_id: Optional[int]
    quantity: float
    locked_quantity: float
    available_quantity: float
    updated_at: datetime
    
    product: ProductResponse
    warehouse: WarehouseResponse
    
    class Config:
        from_attributes = True


class InventoryListResponse(BaseModel):
    items: List[InventoryResponse]
    total: int
    page: int
    page_size: int


# ========== 申请 Schema ==========

class RequisitionItemCreate(BaseModel):
    product_id: int
    warehouse_id: Optional[int] = None
    quantity_requested: float
    remarks: Optional[str] = None


class RequisitionCreate(BaseModel):
    department_id: Optional[int] = None
    purpose: Optional[str] = None
    expected_date: Optional[datetime] = None
    remarks: Optional[str] = None
    items: List[RequisitionItemCreate]


class RequisitionResponse(BaseModel):
    id: int
    req_no: str
    applicant_id: int
    department_id: Optional[int]
    status: str
    total_amount: float
    purpose: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|transfer)$")
    comment: Optional[str] = None
    assignee_id: Optional[int] = None
