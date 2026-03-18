# 权限配置
# 定义各角色可访问的资源和操作

ROLES = {
    'admin': {
        'name': '系统管理员',
        'description': '拥有系统所有权限',
        'permissions': [
            'user:read', 'user:write', 'user:delete',
            'product:read', 'product:write', 'product:delete',
            'inventory:read', 'inventory:write', 'inventory:delete',
            'warehouse:read', 'warehouse:write', 'warehouse:delete',
            'requisition:read', 'requisition:write', 'requisition:delete',
            'approval:read', 'approval:write',
            'report:read', 'report:write',
            'system:read', 'system:write'
        ]
    },
    'warehouse_manager': {
        'name': '仓库管理员',
        'description': '管理仓库和库存数量',
        'permissions': [
            'product:read',
            'inventory:read', 'inventory:write',
            'warehouse:read',
            'requisition:read',
            'report:read'
        ]
    },
    'approver': {
        'name': '审批人',
        'description': '审批领用申请',
        'permissions': [
            'product:read',
            'inventory:read',
            'requisition:read',
            'approval:read', 'approval:write',
            'report:read'
        ]
    },
    'user': {
        'name': '普通用户',
        'description': '提交领用申请',
        'permissions': [
            'product:read',
            'inventory:read',
            'requisition:read', 'requisition:write'
        ]
    }
}


# 权限检查函数
def has_permission(role: str, permission: str) -> bool:
    """检查角色是否有指定权限"""
    if role not in ROLES:
        return False
    return permission in ROLES[role]['permissions']


def get_role_permissions(role: str) -> list:
    """获取角色的所有权限"""
    if role not in ROLES:
        return []
    return ROLES[role]['permissions']


def get_role_name(role: str) -> str:
    """获取角色显示名称"""
    if role not in ROLES:
        return role
    return ROLES[role]['name']
