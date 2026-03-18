# 企业级库存管理系统 - 技术架构设计

## 项目概述

- **项目名称**: Enterprise Inventory Management System (EIMS)
- **目标**: 支持大型企业高并发、大数据量的库存管理
- **数据库**: PostgreSQL 15+
- **部署**: Docker + Kubernetes / 传统服务器

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI (Python) - 高性能异步支持 |
| 数据库 | PostgreSQL 15+ |
| 缓存 | Redis |
| 消息队列 | Celery + RabbitMQ/Redis |
| ORM | SQLAlchemy 2.0 + asyncpg |
| 认证 | JWT + LDAP/AD 集成 |
| 前端 | Vue 3 + Element Plus |
| 部署 | Docker + Docker Compose |

## 核心功能模块

### 1. 组织架构管理
- 部门管理（树形结构）
- 用户管理（同步 AD/LDAP）
- 角色权限（RBAC）
- 数据权限（部门隔离）

### 2. 库存管理
- 仓库/库位管理
- 货物分类（多级类目）
- SKU 管理（规格、批次、序列号）
- 库存预警（安全库存、有效期预警）
- 库存盘点

### 3. 业务流程
- 采购入库
- 领用申请（多级审批工作流）
- 调拨管理
- 退货/报废
- 库存锁定/预留

### 4. 审批工作流
- 可视化流程设计器
- 多级审批（会签/或签）
- 条件分支
- 审批委托/转办
- 审批历史

### 5. 报表与分析
- 库存台账
- 出入库明细
- 库存周转分析
- 领用统计（按部门/个人/货物）
- 自定义报表

## 数据库设计要点

### 核心表结构

```sql
-- 组织架构
organizations (id, parent_id, name, code, level, path)
departments (id, org_id, name, code, manager_id)
users (id, username, email, department_id, ad_guid, is_active)
roles (id, name, permissions)
user_roles (user_id, role_id)

-- 仓库与库位
warehouses (id, code, name, location, manager_id)
locations (id, warehouse_id, code, name, parent_id, path)

-- 货物管理
categories (id, parent_id, name, code, level)
products (id, category_id, sku, name, spec, unit, barcode)
product_batches (id, product_id, batch_no, expiry_date, supplier_id)

-- 库存核心
inventory (id, product_id, warehouse_id, location_id, 
           quantity, locked_quantity, available_quantity,
           batch_id, updated_at)
inventory_transactions (id, type, product_id, warehouse_id, 
                        quantity, before_qty, after_qty,
                        reference_type, reference_id, 
                        operator_id, created_at)

-- 业务流程
requisitions (id, req_no, applicant_id, department_id, 
              status, total_amount, purpose, created_at)
requisition_items (id, requisition_id, product_id, 
                   quantity, approved_qty, status)
approval_instances (id, workflow_id, business_type, business_id,
                    current_step, status, started_at, completed_at)
approval_tasks (id, instance_id, step_name, assignee_id,
                action, comment, created_at, completed_at)

-- 审计日志
audit_logs (id, table_name, record_id, action, 
            old_values, new_values, operator_id, ip_address, created_at)
```

### 性能优化

- **分区表**: inventory_transactions 按时间分区
- **索引策略**: 
  - 复合索引 (product_id, warehouse_id)
  - GIN 索引 (JSON 字段)
  - 部分索引 (未完成的审批任务)
- **读写分离**: 报表查询走只读副本

## 部署架构

### 单机部署 (Docker Compose)

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: inventory
      POSTGRES_USER: inventory
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    
  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://inventory:${DB_PASSWORD}@postgres/inventory
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      
  celery_worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://inventory:${DB_PASSWORD}@postgres/inventory
    depends_on:
      - postgres
      - redis
      
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - api
```

### 集群部署 (Kubernetes)

```
[Ingress Controller]
       ↓
[Frontend Pods x 3]
       ↓
[API Pods x 5]
       ↓
[PostgreSQL HA (Patroni)]
[Redis Cluster]
```

## 性能指标

| 指标 | 目标 |
|------|------|
| 并发用户 | 5000+ |
| QPS | 5000+ |
| 响应时间 | P99 < 200ms |
| 数据量 | 支持亿级记录 |
| 可用性 | 99.9% |

## 安全设计

- HTTPS/TLS 全链路加密
- JWT Token + Refresh Token
- SQL 注入防护（SQLAlchemy ORM）
- XSS/CSRF 防护
- 敏感数据加密存储
- 操作审计日志
- 数据脱敏（报表导出）

## 扩展计划

1. **Phase 1**: 核心功能（库存管理 + 审批流）
2. **Phase 2**: 高级功能（条码/RFID、移动端）
3. **Phase 3**: 集成（ERP、财务系统、WMS）
4. **Phase 4**: AI（需求预测、智能补货）
