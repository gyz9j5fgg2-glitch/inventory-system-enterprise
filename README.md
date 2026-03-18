# 企业级库存管理系统

## 项目概述

基于 FastAPI + PostgreSQL 的企业级库存管理系统，支持高并发、大数据量场景。

## 技术栈

- **后端**: FastAPI (Python)
- **数据库**: PostgreSQL 15+
- **缓存**: Redis
- **消息队列**: Celery
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ 内存

### 2. 启动服务

```bash
cd deploy

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置数据库密码等
vim .env

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

### 3. 初始化数据

```bash
# 执行数据库迁移
docker-compose exec api alembic upgrade head

# 创建初始管理员账号
docker-compose exec api python -m app.init_data
```

### 4. 访问系统

- API 文档: http://localhost/docs
- 管理界面: http://localhost
- 默认账号: admin / admin123

## 生产环境部署

### 配置 LDAP

编辑 `.env` 文件：

```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://ad.company.com:389
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN=cn=admin,dc=company,dc=com
LDAP_PASSWORD=your-ldap-password
```

### 数据库优化

```sql
-- 创建分区表（按时间分区）
CREATE TABLE inventory_transactions_2024 PARTITION OF inventory_transactions
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 创建索引
CREATE INDEX CONCURRENTLY idx_inventory_product_wh 
    ON inventory(product_id, warehouse_id);
```

### 备份策略

```bash
# 自动备份脚本（添加到 crontab）
0 2 * * * docker exec inventory-postgres pg_dump -U inventory inventory > /backup/inventory_$(date +\%Y\%m\%d).sql
```

## 性能指标

| 指标 | 目标 |
|------|------|
| 并发用户 | 5000+ |
| QPS | 5000+ |
| 响应时间 | P99 < 200ms |
| 数据量 | 支持亿级记录 |

## 文档

- [部署指南](docs/DEPLOYMENT.md) - 完整的部署文档
- [配置指南](docs/CONFIGURATION.md) - 系统配置说明
- [数据库迁移](docs/MIGRATIONS.md) - 数据库版本管理

## 快速链接

- **API 文档**: http://localhost/api/docs (启动后访问)
- **前端界面**: http://localhost
- **默认账号**: admin / admin123

## License

MIT
