# 数据库迁移

## Alembic 配置

本项目使用 Alembic 进行数据库迁移管理。

### 初始化迁移

```bash
# 生成初始迁移
alembic init alembic

# 配置 alembic.ini
# sql_alchemy.url = postgresql://user:pass@localhost/db
```

### 常用命令

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 查看迁移历史
alembic history

# 执行迁移
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>

# 查看当前版本
alembic current
```

### 迁移文件示例

```python
# alembic/versions/001_initial.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    op.create_index('ix_users_username', 'users', ['username'])

def downgrade():
    op.drop_index('ix_users_username')
    op.drop_table('users')
```

## 生产环境迁移流程

```bash
# 1. 备份数据库
./deploy/backup.sh

# 2. 在测试环境验证迁移
alembic upgrade head

# 3. 生产环境执行
alembic upgrade head

# 4. 验证数据完整性
```
