# 权限配置
# 定义各角色可访问的资源和操作

ROLES = {
    'admin': {
        'name': '系统管理员',
        'description': '维护货物标题、用户管理、系统配置',
        'permissions': [
            'user:read', 'user:write', 'user:delete',
            'product:read', 'product:write', 'product:delete',
            'inventory:read', 'inventory:write',
            'warehouse:read', 'warehouse:write',
            'requisition:read', 'requisition:write', 'requisition:delete',
            'approval:read', 'approval:write',
            'purchase:read', 'purchase:write', 'purchase:delete',
            'report:read', 'report:write',
            'system:read', 'system:write'
        ]
    },
    'applicant': {
        'name': '申请人',
        'description': '提交领用申请、查看自己的申请',
        'permissions': [
            'product:read',
            'inventory:read',
            'requisition:read', 'requisition:write', 'requisition:submit'
        ]
    },
    'approver': {
        'name': '审批人',
        'description': '审批申请、查看审批历史',
        'permissions': [
            'product:read',
            'inventory:read',
            'requisition:read',
            'approval:read', 'approval:write'
        ]
    },
    'warehouse_manager': {
        'name': '仓库管理员',
        'description': '维护库存数量、发货确认、采购入库',
        'permissions': [
            'product:read',
            'inventory:read', 'inventory:write', 'inventory:ship',
            'warehouse:read',
            'requisition:read', 'requisition:ship',
            'purchase:read', 'purchase:write', 'purchase:receive',
            'report:read'
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


def can_submit_requisition(role: str) -> bool:
    """是否可以提交申请"""
    return has_permission(role, 'requisition:submit')


def can_approve_requisition(role: str) -> bool:
    """是否可以审批申请"""
    return has_permission(role, 'approval:write')


def can_ship_requisition(role: str) -> bool:
    """是否可以发货确认"""
    return has_permission(role, 'requisition:ship')


def can_manage_purchase(role: str) -> bool:
    """是否可以管理采购"""
    return has_permission(role, 'purchase:write')


def can_receive_purchase(role: str) -> bool:
    """是否可以采购入库"""
    return has_permission(role, 'purchase:receive')
