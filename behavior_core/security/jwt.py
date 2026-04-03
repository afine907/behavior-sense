"""
JWT Token 处理模块

提供 JWT Token 的创建和解码功能。
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from behavior_core.config.settings import get_settings


class TokenData(BaseModel):
    """Token 数据模型"""
    sub: str  # 用户ID
    username: str | None = None
    roles: list[str] = []
    exp: datetime | None = None


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: str
    username: str | None = None
    roles: list[str] = []
    exp: int


def create_access_token(
    subject: str,
    username: str | None = None,
    roles: list[str] | None = None,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    创建 JWT Access Token

    Args:
        subject: 用户ID
        username: 用户名
        roles: 角色列表
        expires_delta: 过期时间增量
        additional_claims: 额外的声明

    Returns:
        JWT Token 字符串
    """
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.jwt_expire_hours
        )

    to_encode: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
    }

    if username:
        to_encode["username"] = username
    if roles:
        to_encode["roles"] = roles
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenData | None:
    """
    解码 JWT Access Token

    Args:
        token: JWT Token 字符串

    Returns:
        TokenData 对象，解码失败返回 None
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )

        token_data = TokenData(
            sub=payload.get("sub", ""),
            username=payload.get("username"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc),
        )
        return token_data

    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """
    验证 Token 是否有效

    Args:
        token: JWT Token 字符串

    Returns:
        Token 是否有效
    """
    token_data = decode_access_token(token)
    if token_data is None:
        return False

    # 检查是否过期
    if token_data.exp and token_data.exp < datetime.now(timezone.utc):
        return False

    return True
