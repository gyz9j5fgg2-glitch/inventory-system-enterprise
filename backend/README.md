# FastAPI 企业级后端

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模型
│   ├── routers/             # API 路由
│   ├── services/            # 业务逻辑
│   ├── tasks/               # Celery 异步任务
│   ├── middleware/          # 中间件
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload

# 启动 Celery  worker
celery -A app.tasks worker --loglevel=info
```

## 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/inventory

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LDAP
LDAP_SERVER=ldap://ad.company.com
LDAP_BASE_DN=dc=company,dc=com

# 其他
DEBUG=false
LOG_LEVEL=INFO
```
