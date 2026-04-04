"""
认证模块

提供密码哈希、用户认证等功能。
"""
from datetime import datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from behavior_core.security.jwt import TokenData, decode_access_token

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        哈希密码
    """
    return pwd_context.hash(password)


def authenticate_user(
    username: str,
    password: str,
    user_db: dict[str, Any],  # 模拟用户数据库
) -> dict[str, Any] | None:
    """
    认证用户

    Args:
        username: 用户名
        password: 密码
        user_db: 用户数据库 (user_id -> user_info)

    Returns:
        用户信息，认证失败返回 None
    """
    user = user_db.get(username)
    if user is None:
        return None
    if not verify_password(password, user.get("hashed_password", "")):
        return None
    return user


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> TokenData:
    """
    获取当前用户 (FastAPI 依赖)

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        TokenData 用户信息

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    token_data = decode_access_token(token)

    if token_data is None:
        raise credentials_exception

    # 检查是否过期
    if token_data.exp and token_data.exp < datetime.now():
        raise credentials_exception

    return token_data


async def get_current_active_user(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    """
    获取当前活跃用户 (FastAPI 依赖)

    Args:
        current_user: 当前用户

    Returns:
        TokenData 用户信息

    Raises:
        HTTPException: 用户已禁用
    """
    # 可以在这里添加用户状态检查逻辑
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(*required_roles: str):
    """
    创建角色检查依赖

    Args:
        *required_roles: 需要的角色列表

    Returns:
        FastAPI 依赖函数
    """
    async def role_checker(
        current_user: Annotated[TokenData, Depends(get_current_user)],
    ) -> TokenData:
        """检查用户是否具有所需角色"""
        user_roles = set(current_user.roles)
        required = set(required_roles)

        if not required.intersection(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return role_checker


# 常用角色依赖
RequireAdmin = Depends(require_roles("ADMIN"))
RequireAnalyst = Depends(require_roles("ADMIN", "ANALYST"))
RequireAuditor = Depends(require_roles("ADMIN", "AUDITOR"))
