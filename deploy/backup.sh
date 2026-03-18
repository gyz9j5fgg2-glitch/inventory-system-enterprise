#!/bin/bash
# backup.sh - 数据库自动备份脚本

set -e

# 配置
BACKUP_DIR="${BACKUP_DIR:-/backup/inventory}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "备份开始: $(date)"
echo "=========================================="

# 检查 Docker 容器状态
if ! docker ps | grep -q inventory-postgres; then
    echo "错误: PostgreSQL 容器未运行"
    exit 1
fi

# 备份 PostgreSQL
echo "[1/2] 备份 PostgreSQL 数据库..."
docker exec inventory-postgres pg_dump -U inventory inventory | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
if [ $? -eq 0 ]; then
    echo "✓ 数据库备份成功: db_$DATE.sql.gz"
else
    echo "✗ 数据库备份失败"
    exit 1
fi

# 备份 Redis
echo "[2/2] 备份 Redis 数据..."
docker exec inventory-redis redis-cli BGSAVE
sleep 2
docker cp inventory-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"
if [ $? -eq 0 ]; then
    echo "✓ Redis 备份成功: redis_$DATE.rdb"
else
    echo "✗ Redis 备份失败"
fi

# 清理旧备份
echo ""
echo "清理 $RETENTION_DAYS 天前的备份..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete

# 显示备份列表
echo ""
echo "当前备份文件:"
ls -lh "$BACKUP_DIR" | tail -10

echo ""
echo "=========================================="
echo "备份完成: $(date)"
echo "=========================================="
