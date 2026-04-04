"""
安全模块

提供 JWT 认证、密码哈希等安全功能。
"""
from behavior_core.security.auth import (
    authenticate_user,
    get_current_active_user,
    get_current_user,
    get_password_hash,
    verify_password,
)
from behavior_core.security.jwt import (
    TokenData,
    create_access_token,
    decode_access_token,
)

__all__ = [
    # JWT
    "create_access_token",
    "decode_access_token",
    "TokenData",
    # Auth
    "verify_password",
    "get_password_hash",
    "authenticate_user",
    "get_current_user",
    "get_current_active_user",
]
