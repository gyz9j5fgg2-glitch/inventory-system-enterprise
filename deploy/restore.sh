#!/bin/bash
# restore.sh - 数据恢复脚本

set -e

BACKUP_DIR="${BACKUP_DIR:-/backup/inventory}"

echo "=========================================="
echo "数据恢复工具"
echo "=========================================="

# 列出可用备份
echo "可用的数据库备份:"
ls -lt "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -10
echo ""

echo "可用的 Redis 备份:"
ls -lt "$BACKUP_DIR"/*.rdb 2>/dev/null | head -10
echo ""

# 选择备份文件
read -p "请输入要恢复的数据库备份文件名 (如 db_20240318_020000.sql.gz): " DB_BACKUP
read -p "请输入要恢复的 Redis 备份文件名 (如 redis_20240318_020000.rdb): " REDIS_BACKUP

# 确认恢复
echo ""
echo "⚠️  警告: 此操作将覆盖当前数据!"
echo "数据库备份: $DB_BACKUP"
echo "Redis 备份: $REDIS_BACKUP"
read -p "确认恢复? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# 恢复数据库
echo ""
echo "[1/2] 恢复 PostgreSQL..."
gunzip < "$BACKUP_DIR/$DB_BACKUP" | docker exec -i inventory-postgres psql -U inventory -d inventory
if [ $? -eq 0 ]; then
    echo "✓ 数据库恢复成功"
else
    echo "✗ 数据库恢复失败"
    exit 1
fi

# 恢复 Redis
echo "[2/2] 恢复 Redis..."
docker cp "$BACKUP_DIR/$REDIS_BACKUP" inventory-redis:/data/dump.rdb
docker restart inventory-redis
if [ $? -eq 0 ]; then
    echo "✓ Redis 恢复成功"
else
    echo "✗ Redis 恢复失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "恢复完成: $(date)"
echo "=========================================="
