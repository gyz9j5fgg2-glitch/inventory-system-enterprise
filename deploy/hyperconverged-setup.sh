#!/bin/bash
# hyperconverged-setup.sh - 超融合环境一键配置脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
NODE_IPS=("192.168.10.11" "192.168.10.12" "192.168.10.13")
NODE_NAMES=("node1" "node2" "node3")
VIP="192.168.10.10"
SSH_USER="root"
SSH_PASS="YourPassword"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查SSH连接
check_ssh() {
    log_info "检查节点SSH连接..."
    for i in "${!NODE_IPS[@]}"; do
        if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "${SSH_USER}@${NODE_IPS[$i]}" "echo OK" &>/dev/null; then
            log_success "节点 ${NODE_NAMES[$i]} (${NODE_IPS[$i]}) 连接正常"
        else
            log_error "节点 ${NODE_NAMES[$i]} (${NODE_IPS[$i]}) 连接失败"
            exit 1
        fi
    done
}

# 配置主机名和hosts
setup_hosts() {
    log_info "配置主机名和hosts..."
    for i in "${!NODE_IPS[@]}"; do
        ssh "${SSH_USER}@${NODE_IPS[$i]}" "
            hostnamectl set-hostname ${NODE_NAMES[$i]}
            cat > /etc/hosts << 'EOF'
127.0.0.1   localhost
${NODE_IPS[0]}   ${NODE_NAMES[0]}
${NODE_IPS[1]}   ${NODE_NAMES[1]}
${NODE_IPS[2]}   ${NODE_NAMES[2]}
${VIP}          vip
EOF
        "
        log_success "${NODE_NAMES[$i]} 主机名配置完成"
    done
}

# 配置NTP
setup_ntp() {
    log_info "配置NTP时间同步..."
    for ip in "${NODE_IPS[@]}"; do
        ssh "${SSH_USER}@$ip" "
            yum install -y chrony
            systemctl enable chronyd
            systemctl start chronyd
            chronyc sources
        "
    done
    log_success "NTP配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙规则..."
    for ip in "${NODE_IPS[@]}"; do
        ssh "${SSH_USER}@$ip" "
            systemctl stop firewalld
            systemctl disable firewalld
            yum install -y iptables-services
            systemctl enable iptables
            
            # 允许内部网络通信
            iptables -A INPUT -s 192.168.10.0/24 -j ACCEPT
            iptables -A INPUT -s 192.168.20.0/24 -j ACCEPT
            iptables -A INPUT -s 192.168.30.0/24 -j ACCEPT
            
            # 允许SSH
            iptables -A INPUT -p tcp --dport 22 -j ACCEPT
            
            # 保存规则
            service iptables save
        "
    done
    log_success "防火墙配置完成"
}

# 配置SSH免密登录
setup_ssh_key() {
    log_info "配置SSH免密登录..."
    
    # 生成密钥
    if [ ! -f ~/.ssh/id_rsa ]; then
        ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
    fi
    
    # 分发公钥
    for ip in "${NODE_IPS[@]}"; do
        sshpass -p "$SSH_PASS" ssh-copy-id -o StrictHostKeyChecking=no "${SSH_USER}@$ip"
    done
    
    log_success "SSH免密登录配置完成"
}

# 检查硬件
check_hardware() {
    log_info "检查服务器硬件..."
    for ip in "${NODE_IPS[@]}"; do
        log_info "检查节点 $ip..."
        ssh "${SSH_USER}@$ip" "
            echo '=== CPU信息 ==='
            lscpu | grep 'Model name'
            lscpu | grep 'CPU(s)'
            
            echo '=== 内存信息 ==='
            free -h
            
            echo '=== 磁盘信息 ==='
            lsblk
            
            echo '=== 网卡信息 ==='
            ip link show
        "
    done
}

# 配置网络
setup_network() {
    log_info "配置网络..."
    
    # 配置管理网络 (VLAN10)
    for i in "${!NODE_IPS[@]}"; do
        ssh "${SSH_USER}@${NODE_IPS[$i]}" "
            cat > /etc/sysconfig/network-scripts/ifcfg-mgmt0 << EOF
DEVICE=mgmt0
BOOTPROTO=static
ONBOOT=yes
IPADDR=${NODE_IPS[$i]}
PREFIX=24
GATEWAY=192.168.10.1
VLAN=yes
EOF
        "
    done
    
    log_success "网络配置完成"
}

# 主菜单
show_menu() {
    clear
    echo "========================================"
    echo "  超融合环境配置工具"
    echo "========================================"
    echo ""
    echo "1. 检查SSH连接"
    echo "2. 配置SSH免密登录"
    echo "3. 配置主机名和hosts"
    echo "4. 配置NTP时间同步"
    echo "5. 配置防火墙"
    echo "6. 检查硬件信息"
    echo "7. 执行全部配置"
    echo "8. 退出"
    echo ""
    echo "========================================"
}

# 执行全部配置
run_all() {
    check_ssh
    setup_ssh_key
    setup_hosts
    setup_ntp
    setup_firewall
    check_hardware
    log_success "全部配置完成!"
}

# 主程序
main() {
    while true; do
        show_menu
        read -p "请选择操作 [1-8]: " choice
        
        case $choice in
            1) check_ssh ;;
            2) setup_ssh_key ;;
            3) setup_hosts ;;
            4) setup_ntp ;;
            5) setup_firewall ;;
            6) check_hardware ;;
            7) run_all ;;
            8) exit 0 ;;
            *) log_error "无效选择" ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 运行主程序
main
