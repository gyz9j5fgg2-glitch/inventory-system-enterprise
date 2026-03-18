# 企业级库存管理系统 - 业务流程设计

## 角色权限

| 角色 | 权限 |
|------|------|
| **系统管理员** | 维护货物标题、用户管理、系统配置 |
| **申请人** | 提交领用申请、查看自己的申请 |
| **审批人** | 审批申请、查看审批历史 |
| **仓库管理员** | 维护库存数量、发货确认、采购入库 |

## 业务流程

### 1. 领用流程

```
申请人提交申请 → 审批人审批 → 仓库管理员发货确认 → 系统自动扣减库存
     ↑                    ↑              ↑
   草稿/提交           批准/拒绝      确认发货
```

**状态流转：**
- `draft` → `submitted` → `approved` → `shipped` → `completed`
- `draft` → `submitted` → `rejected`
- `approved` → `shipped` → `cancelled`

### 2. 采购流程

```
仓库管理员创建PO → 货物入库 → 系统自动增加库存
```

**PO信息：**
- PO号码（唯一）
- 供应商
- 采购时间
- 货物明细（货物、数量、单价）
- 入库时间
- 入库状态

## 数据库表更新

### 新增表

```sql
-- 采购订单
purchase_orders (
    id, po_no, supplier_id, order_date, 
    total_amount, status, remarks, created_by, created_at
)

-- 采购订单明细
purchase_order_items (
    id, po_id, product_id, quantity, unit_price, 
    received_qty, status
)

-- 入库记录
receiving_records (
    id, po_id, product_id, warehouse_id, 
    quantity, received_by, received_at, remarks
)
```

### 更新表

```sql
-- 申请单增加发货相关字段
requisitions (
    ...
    shipper_id,      -- 发货人
    shipped_at,      -- 发货时间
    ship_remarks     -- 发货备注
)
```
