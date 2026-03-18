from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, ReceivingRecord
from app.models.workflow import Requisition, RequisitionStatus, RequisitionItem
from app.models.inventory import Inventory, InventoryTransaction
from app.services.auth import get_current_user, require_permission
from app.services.permissions import can_ship_requisition, can_receive_purchase

router = APIRouter()


# ========== 申请单发货确认 ==========

@router.post("/requisitions/{req_id}/ship")
async def ship_requisition(
    req_id: int,
    ship_remarks: str = "",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    仓库管理员发货确认
    确认后自动扣减库存
    """
    # 检查权限
    if not can_ship_requisition(current_user.get('role')):
        raise HTTPException(status_code=403, detail="需要仓库管理员权限")
    
    # 查询申请单
    result = await db.execute(
        select(Requisition).where(
            and_(Requisition.id == req_id, Requisition.status == RequisitionStatus.APPROVED)
        )
    )
    requisition = result.scalar_one_or_none()
    
    if not requisition:
        raise HTTPException(status_code=404, detail="申请单不存在或状态不正确")
    
    # 获取申请明细
    items_result = await db.execute(
        select(RequisitionItem).where(RequisitionItem.requisition_id == req_id)
    )
    items = items_result.scalars().all()
    
    # 检查库存并扣减
    for item in items:
        # 查询库存
        inv_result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.product_id == item.product_id,
                    Inventory.warehouse_id == item.warehouse_id
                )
            )
        )
        inventory = inv_result.scalar_one_or_none()
        
        if not inventory or inventory.available_quantity < item.quantity_approved:
            raise HTTPException(
                status_code=400, 
                detail=f"货物库存不足: {item.product_id}"
            )
        
        # 记录扣减前数量
        before_qty = inventory.quantity
        
        # 扣减库存
        inventory.quantity -= item.quantity_approved
        inventory.available_quantity -= item.quantity_approved
        inventory.updated_at = datetime.utcnow()
        inventory.updated_by = current_user.get('id')
        
        # 创建库存交易记录
        transaction = InventoryTransaction(
            transaction_type='OUT',
            product_id=item.product_id,
            warehouse_id=item.warehouse_id,
            quantity=-item.quantity_approved,
            before_qty=before_qty,
            after_qty=inventory.quantity,
            reference_type='requisition',
            reference_id=req_id,
            reference_no=requisition.req_no,
            operator_id=current_user.get('id'),
            operator_name=current_user.get('name'),
            remarks=f"申请单发货: {requisition.req_no}"
        )
        db.add(transaction)
        
        # 更新申请明细
        item.quantity_shipped = item.quantity_approved
        item.shipped_by = current_user.get('id')
        item.shipped_at = datetime.utcnow()
    
    # 更新申请单状态
    requisition.status = RequisitionStatus.SHIPPED
    requisition.shipper_id = current_user.get('id')
    requisition.shipped_at = datetime.utcnow()
    requisition.ship_remarks = ship_remarks
    
    await db.commit()
    
    return {"message": "发货确认成功，库存已扣减", "req_no": requisition.req_no}


@router.get("/requisitions/to-ship")
async def get_pending_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取待发货的申请单列表"""
    if not can_ship_requisition(current_user.get('role')):
        raise HTTPException(status_code=403, detail="需要仓库管理员权限")
    
    # 查询已批准待发货的申请
    result = await db.execute(
        select(Requisition)
        .where(Requisition.status == RequisitionStatus.APPROVED)
        .order_by(Requisition.approved_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    requisitions = result.scalars().all()
    
    return {
        "items": requisitions,
        "total": len(requisitions),
        "page": page,
        "page_size": page_size
    }


# ========== 采购管理 ==========

@router.post("/purchase-orders")
async def create_purchase_order(
    po_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建采购订单
    仅仓库管理员可操作
    """
    if not can_manage_purchase(current_user.get('role')):
        raise HTTPException(status_code=403, detail="需要仓库管理员权限")
    
    # 生成PO号码
    po_no = f"PO{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 创建采购订单
    po = PurchaseOrder(
        po_no=po_no,
        supplier_id=po_data.get('supplier_id'),
        order_date=datetime.strptime(po_data.get('order_date'), '%Y-%m-%d'),
        expected_date=datetime.strptime(po_data.get('expected_date'), '%Y-%m-%d') if po_data.get('expected_date') else None,
        total_amount=po_data.get('total_amount', 0),
        remarks=po_data.get('remarks'),
        created_by=current_user.get('id'),
        status=PurchaseOrderStatus.DRAFT
    )
    db.add(po)
    await db.flush()
    
    # 创建采购明细
    for item_data in po_data.get('items', []):
        item = PurchaseOrderItem(
            po_id=po.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            warehouse_id=item_data.get('warehouse_id'),
            received_qty=0
        )
        db.add(item)
    
    await db.commit()
    await db.refresh(po)
    
    return {"message": "采购订单创建成功", "po_no": po_no, "id": po.id}


@router.get("/purchase-orders")
async def list_purchase_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """查询采购订单列表"""
    query = select(PurchaseOrder)
    
    if status:
        query = query.where(PurchaseOrder.status == status)
    
    query = query.order_by(PurchaseOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    pos = result.scalars().all()
    
    return {
        "items": pos,
        "total": len(pos),
        "page": page,
        "page_size": page_size
    }


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase(
    po_id: int,
    receive_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    采购入库
    入库后自动增加库存
    """
    if not can_receive_purchase(current_user.get('role')):
        raise HTTPException(status_code=403, detail="需要仓库管理员权限")
    
    # 查询采购订单
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    if po.status == PurchaseOrderStatus.RECEIVED:
        raise HTTPException(status_code=400, detail="该订单已全部入库")
    
    # 处理入库
    for item_data in receive_data.get('items', []):
        item_id = item_data['item_id']
        quantity = item_data['quantity']
        warehouse_id = item_data['warehouse_id']
        
        # 查询采购明细
        item_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id)
        )
        po_item = item_result.scalar_one_or_none()
        
        if not po_item:
            continue
        
        # 查询或创建库存记录
        inv_result = await db.execute(
            select(Inventory).where(
                and_(
                    Inventory.product_id == po_item.product_id,
                    Inventory.warehouse_id == warehouse_id
                )
            )
        )
        inventory = inv_result.scalar_one_or_none()
        
        if inventory:
            # 更新库存
            before_qty = inventory.quantity
            inventory.quantity += quantity
            inventory.available_quantity += quantity
            inventory.updated_at = datetime.utcnow()
            inventory.updated_by = current_user.get('id')
        else:
            # 创建新库存记录
            before_qty = 0
            inventory = Inventory(
                product_id=po_item.product_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                available_quantity=quantity,
                locked_quantity=0,
                updated_by=current_user.get('id')
            )
            db.add(inventory)
        
        # 创建入库记录
        receiving = ReceivingRecord(
            po_id=po_id,
            product_id=po_item.product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            received_by=current_user.get('id'),
            remarks=item_data.get('remarks')
        )
        db.add(receiving)
        
        # 创建库存交易记录
        transaction = InventoryTransaction(
            transaction_type='IN',
            product_id=po_item.product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            before_qty=before_qty,
            after_qty=before_qty + quantity,
            reference_type='purchase',
            reference_id=po_id,
            reference_no=po.po_no,
            operator_id=current_user.get('id'),
            operator_name=current_user.get('name'),
            remarks=f"采购入库: {po.po_no}"
        )
        db.add(transaction)
        
        # 更新采购明细到货数量
        po_item.received_qty += quantity
    
    # 更新采购订单状态
    # 检查是否全部到货
    all_items_result = await db.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po_id)
    )
    all_items = all_items_result.scalars().all()
    
    all_received = all(item.received_qty >= item.quantity for item in all_items)
    any_received = any(item.received_qty > 0 for item in all_items)
    
    if all_received:
        po.status = PurchaseOrderStatus.RECEIVED
    elif any_received:
        po.status = PurchaseOrderStatus.PARTIAL
    
    await db.commit()
    
    return {
        "message": "入库成功，库存已更新",
        "po_no": po.po_no,
        "status": po.status.value
    }


@router.get("/purchase-orders/{po_id}")
async def get_purchase_order(
    po_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取采购订单详情"""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    po = result.scalar_one_or_none()
    
    if not po:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    
    return po
