#!/bin/bash
# install.sh - 一键安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "企业级库存管理系统 - 安装脚本"
echo "=========================================="

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}请使用 sudo 运行此脚本${NC}"
   exit 1
fi

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}无法检测操作系统${NC}"
    exit 1
fi

echo "检测到操作系统: $OS $VER"

# 安装 Docker
install_docker() {
    echo ""
    echo "[1/5] 安装 Docker..."
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}Docker 已安装${NC}"
        docker --version
        return
    fi
    
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker 安装完成${NC}"
}

# 安装 Docker Compose
install_docker_compose() {
    echo ""
    echo "[2/5] 安装 Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}Docker Compose 已安装${NC}"
        docker-compose --version
        return
    fi
    
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}Docker Compose 安装完成${NC}"
}

# 创建目录结构
setup_directories() {
    echo ""
    echo "[3/5] 创建目录结构..."
    
    INSTALL_DIR="${INSTALL_DIR:-/opt/inventory-system}"
    mkdir -p "$INSTALL_DIR"
    mkdir -p /backup/inventory
    
    echo -e "${GREEN}目录创建完成: $INSTALL_DIR${NC}"
}

# 克隆代码
clone_code() {
    echo ""
    echo "[4/5] 下载代码..."
    
    INSTALL_DIR="${INSTALL_DIR:-/opt/inventory-system}"
    cd "$INSTALL_DIR"
    
    if [ -d ".git" ]; then
        echo "更新代码..."
        git pull origin main
    else
        echo "克隆代码..."
        git clone https://github.com/gyz9j5fgg2-glitch/inventory-system-enterprise.git .
    fi
    
    echo -e "${GREEN}代码下载完成${NC}"
}

# 配置环境
setup_environment() {
    echo ""
    echo "[5/5] 配置环境..."
    
    INSTALL_DIR="${INSTALL_DIR:-/opt/inventory-system}"
    cd "$INSTALL_DIR/deploy"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        
        # 生成随机密码
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-20)
        SECRET_KEY=$(openssl rand -base64 64 | tr -d "\n")
        
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        
        echo -e "${YELLOW}请编辑 .env 文件配置 LDAP 等参数${NC}"
        echo "配置文件位置: $INSTALL_DIR/deploy/.env"
    fi
    
    echo -e "${GREEN}环境配置完成${NC}"
}

# 启动服务
start_services() {
    echo ""
    echo "启动服务..."
    
    INSTALL_DIR="${INSTALL_DIR:-/opt/inventory-system}"
    cd "$INSTALL_DIR/deploy"
    
    docker-compose up -d
    
    echo "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}服务启动成功!${NC}"
        echo ""
        echo "访问地址:"
        echo "  - 前端: http://localhost"
        echo "  - API: http://localhost/api"
        echo "  - API文档: http://localhost/api/docs"
    else
        echo -e "${RED}服务启动失败，请检查日志${NC}"
        docker-compose logs
    fi
}

# 主流程
main() {
    install_docker
    install_docker_compose
    setup_directories
    clone_code
    setup_environment
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}安装完成!${NC}"
    echo "=========================================="
    echo ""
    echo "下一步:"
    echo "1. 编辑 .env 文件配置必要参数"
    echo "2. 运行 ./install.sh --start 启动服务"
    echo ""
    
    # 如果带 --start 参数则自动启动
    if [ "$1" == "--start" ]; then
        start_services
    fi
}

# 处理命令行参数
case "$1" in
    --start)
        start_services
        ;;
    --help|-h)
        echo "用法: ./install.sh [选项]"
        echo ""
        echo "选项:"
        echo "  --start    安装完成后自动启动服务"
        echo "  --help     显示帮助信息"
        echo ""
        echo "环境变量:"
        echo "  INSTALL_DIR    安装目录 (默认: /opt/inventory-system)"
        ;;
    *)
        main "$1"
        ;;
esac
