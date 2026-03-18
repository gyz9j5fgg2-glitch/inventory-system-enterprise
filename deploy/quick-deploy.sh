#!/bin/bash
# quick-deploy.sh - 现有虚拟化平台快速部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
DB_HOST="${DB_HOST:-192.168.1.21}"
WEB01_HOST="${WEB01_HOST:-192.168.1.22}"
WEB02_HOST="${WEB02_HOST:-192.168.1.23}"
SSH_USER="${SSH_USER:-root}"

echo "========================================"
echo "EIMS 快速部署工具"
echo "========================================"
echo ""
echo "部署架构:"
echo "  数据库服务器: $DB_HOST"
echo "  Web服务器1:  $WEB01_HOST"
echo "  Web服务器2:  $WEB02_HOST"
echo ""

# 检查SSH连接
check_ssh() {
    echo -e "${BLUE}[1/5] 检查SSH连接...${NC}"
    
    for host in "$DB_HOST" "$WEB01_HOST" "$WEB02_HOST"; do
        if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$host" "echo OK" &>/dev/null; then
            echo -e "${GREEN}✓${NC} $host 连接正常"
        else
            echo -e "${RED}✗${NC} $host 连接失败"
            exit 1
        fi
    done
}

# 部署数据库
deploy_db() {
    echo -e "${BLUE}[2/5] 部署数据库服务器 ($DB_HOST)...${NC}"
    
    # 复制并执行安装脚本
    scp -o StrictHostKeyChecking=no install-db.sh "$SSH_USER@$DB_HOST:/root/"
    ssh -o StrictHostKeyChecking=no "$SSH_USER@$DB_HOST" "chmod +x /root/install-db.sh && /root/install-db.sh"
    
    # 获取密码
    DB_PASSWORD=$(ssh -o StrictHostKeyChecking=no "$SSH_USER@$DB_HOST" "cat /root/db-password.txt | grep 'Database Password' | cut -d': ' -f2")
    REDIS_PASSWORD=$(ssh -o StrictHostKeyChecking=no "$SSH_USER@$DB_HOST" "cat /root/db-password.txt | grep 'Redis Password' | cut -d': ' -f2")
    
    echo -e "${GREEN}✓${NC} 数据库部署完成"
    echo "  数据库密码: $DB_PASSWORD"
    echo "  Redis密码: $REDIS_PASSWORD"
}

# 部署Web服务器
deploy_web() {
    local host=$1
    local name=$2
    
    echo -e "${BLUE}[$3/5] 部署 $name ($host)...${NC}"
    
    # 获取数据库密码
    DB_PASSWORD=$(ssh -o StrictHostKeyChecking=no "$SSH_USER@$DB_HOST" "cat /root/db-password.txt | grep 'Database Password' | cut -d': ' -f2")
    REDIS_PASSWORD=$(ssh -o StrictHostKeyChecking=no "$SSH_USER@$DB_HOST" "cat /root/db-password.txt | grep 'Redis Password' | cut -d': ' -f2")
    
    # 创建临时安装脚本
    cat > /tmp/install-app-temp.sh << EOF
#!/bin/bash
DB_HOST="$DB_HOST"
DB_PASSWORD="$DB_PASSWORD"
REDIS_PASSWORD="$REDIS_PASSWORD"

$(cat install-app.sh | sed '1,/^EOF$/d')
EOF
    
    scp -o StrictHostKeyChecking=no /tmp/install-app-temp.sh "$SSH_USER@$host:/root/install-app.sh"
    ssh -o StrictHostKeyChecking=no "$SSH_USER@$host" "chmod +x /root/install-app.sh && /root/install-app.sh"
    
    echo -e "${GREEN}✓${NC} $name 部署完成"
}

# 验证部署
verify_deployment() {
    echo -e "${BLUE}[5/5] 验证部署...${NC}"
    
    # 检查数据库
    if ssh "$SSH_USER@$DB_HOST" "systemctl is-active postgresql-15" &>/dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL 运行正常"
    else
        echo -e "${RED}✗${NC} PostgreSQL 未运行"
    fi
    
    # 检查Redis
    if ssh "$SSH_USER@$DB_HOST" "systemctl is-active redis" &>/dev/null; then
        echo -e "${GREEN}✓${NC} Redis 运行正常"
    else
        echo -e "${RED}✗${NC} Redis 未运行"
    fi
    
    # 检查Web服务
    for host in "$WEB01_HOST" "$WEB02_HOST"; do
        if curl -s "http://$host/health" | grep -q "ok"; then
            echo -e "${GREEN}✓${NC} Web服务 ($host) 运行正常"
        else
            echo -e "${RED}✗${NC} Web服务 ($host) 异常"
        fi
    done
}

# 显示部署信息
show_info() {
    echo ""
    echo "========================================"
    echo -e "${GREEN}部署完成!${NC}"
    echo "========================================"
    echo ""
    echo "访问地址:"
    echo "  - Web服务器1: http://$WEB01_HOST"
    echo "  - Web服务器2: http://$WEB02_HOST"
    echo ""
    echo "默认账号:"
    echo "  - 管理员: admin / admin123"
    echo "  - 申请人: applicant / applicant123"
    echo "  - 审批人: approver / approver123"
    echo "  - 仓库管理员: warehouse / warehouse123"
    echo ""
    echo "下一步:"
    echo "  1. 在负载均衡设备上配置后端服务器"
    echo "  2. 配置域名解析到负载均衡VIP"
    echo "  3. 测试完整业务流程"
    echo ""
}

# 主菜单
main() {
    echo "选择操作:"
    echo "1. 完整部署 (数据库 + 2台Web)"
    echo "2. 仅部署数据库"
    echo "3. 仅部署Web服务器"
    echo "4. 验证部署状态"
    echo "5. 退出"
    echo ""
    read -p "请选择 [1-5]: " choice
    
    case $choice in
        1)
            check_ssh
            deploy_db
            deploy_web "$WEB01_HOST" "Web服务器1" "3"
            deploy_web "$WEB02_HOST" "Web服务器2" "4"
            verify_deployment
            show_info
            ;;
        2)
            check_ssh
            deploy_db
            echo -e "${GREEN}数据库部署完成${NC}"
            ;;
        3)
            check_ssh
            deploy_web "$WEB01_HOST" "Web服务器1" "2"
            deploy_web "$WEB02_HOST" "Web服务器2" "3"
            verify_deployment
            show_info
            ;;
        4)
            verify_deployment
            ;;
        5)
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            ;;
    esac
}

# 运行
main
