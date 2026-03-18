"""
LDAP/AD 域认证服务
支持 Windows Active Directory 域认证
"""
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class LDAPAuthService:
    """LDAP 认证服务类"""
    
    def __init__(self):
        self.server = os.getenv('LDAP_SERVER', '')
        self.base_dn = os.getenv('LDAP_BASE_DN', 'dc=company,dc=com')
        self.user_dn = os.getenv('LDAP_USER_DN', '')
        self.password = os.getenv('LDAP_PASSWORD', '')
        self.enabled = os.getenv('LDAP_ENABLED', 'false').lower() == 'true'
        
    def is_enabled(self) -> bool:
        """检查 LDAP 是否启用"""
        return self.enabled and bool(self.server)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        验证用户凭据
        返回用户信息或 None
        """
        if not self.is_enabled():
            return None
            
        try:
            from ldap3 import Server, Connection, SUBTREE, AUTO_BIND_NO_TLS
            from ldap3.core.exceptions import LDAPException
            
            # 构建用户 DN
            user_dn = f"CN={username},{self.base_dn}"
            
            # 连接 LDAP 服务器
            server = Server(self.server, get_info=AUTO_BIND_NO_TLS)
            
            # 尝试绑定
            conn = Connection(server, user=user_dn, password=password, auto_bind=True)
            
            if conn.bind():
                # 获取用户信息
                user_info = self._get_user_info(conn, username)
                conn.unbind()
                return user_info
                
        except ImportError:
            logger.warning("ldap3 模块未安装，请运行: pip install ldap3")
        except Exception as e:
            logger.error(f"LDAP 认证失败: {e}")
            
        return None
    
    def _get_user_info(self, conn, username: str) -> Dict:
        """获取用户详细信息"""
        try:
            conn.search(
                search_base=self.base_dn,
                search_filter=f"(sAMAccountName={username})",
                search_scope=SUBTREE,
                attributes=['cn', 'mail', 'department', 'title', 'memberOf']
            )
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    'username': username,
                    'name': str(entry.cn) if hasattr(entry, 'cn') else username,
                    'email': str(entry.mail) if hasattr(entry, 'mail') else f"{username}@company.com",
                    'department': str(entry.department) if hasattr(entry, 'department') else '',
                    'title': str(entry.title) if hasattr(entry, 'title') else '',
                    'groups': [str(g) for g in entry.memberOf] if hasattr(entry, 'memberOf') else []
                }
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            
        return {
            'username': username,
            'name': username,
            'email': f"{username}@company.com",
            'department': '',
            'title': '',
            'groups': []
        }
    
    def get_user_groups(self, username: str) -> list:
        """获取用户所属组"""
        try:
            from ldap3 import Server, Connection, SUBTREE, AUTO_BIND_NO_TLS
            
            user_dn = f"CN={username},{self.base_dn}"
            server = Server(self.server, get_info=AUTO_BIND_NO_TLS)
            conn = Connection(server, user=self.user_dn, password=self.password, auto_bind=True)
            
            conn.search(
                search_base=user_dn,
                search_filter='(objectClass=user)',
                attributes=['memberOf']
            )
            
            if conn.entries:
                groups = conn.entries[0].memberOf
                return [str(g).split(',')[0].replace('CN=', '') for g in groups]
                
        except Exception as e:
            logger.error(f"获取用户组失败: {e}")
            
        return []
    
    def sync_user_from_ad(self, username: str) -> Optional[Dict]:
        """从 AD 同步用户信息到本地数据库"""
        # 这个方法在实际环境中会调用数据库服务更新用户信息
        pass


# 单例实例
ldap_service = LDAPAuthService()


def authenticate_with_ldap(username: str, password: str) -> Optional[Dict]:
    """便捷的 LDAP 认证函数"""
    return ldap_service.authenticate(username, password)


def is_ldap_enabled() -> bool:
    """检查 LDAP 是否启用"""
    return ldap_service.is_enabled()
