"""
凭据加密模块
==============
节点的 SSH 密码/私钥使用 Fernet（AES-128 + HMAC-SHA256）对称加密后存入数据库。
密钥来源：环境变量 DISKBENCH_SECRET_KEY，未设置时从 `./.secret.key` 文件读取/生成。

使用方式：
    from core.crypto import encrypt, decrypt, is_encrypted

    ciphertext = encrypt(plain_password)   # 存库
    plain      = decrypt(ciphertext)       # 用到时解

对历史明文数据的兼容：
    如果传入的值看起来不是密文（没有 ENC: 前缀），视为"旧的明文数据"，
    直接返回，不报错。这样上线后 SSH 仍能工作，后续可由脚本批量加密补齐。
"""
from __future__ import annotations

import base64
import os
import secrets
from pathlib import Path
from typing import Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "缺少 cryptography 包，请 `pip install cryptography>=41`"
    ) from e


# 密文前缀：用它来区分"已加密"和"历史明文"
_ENC_PREFIX = "ENC:v1:"

_SECRET_ENV_VAR = "DISKBENCH_SECRET_KEY"
_SECRET_FILE = Path.home() / ".diskbench" / "secret.key"


def _load_or_create_key() -> bytes:
    """
    获取加密密钥（32 字节 base64）
    优先级：环境变量 > 本地文件 > 新建并保存到文件
    """
    # 1. 环境变量（推荐生产使用）
    env_key = os.environ.get(_SECRET_ENV_VAR)
    if env_key:
        try:
            # 验证密钥格式
            Fernet(env_key.encode() if isinstance(env_key, str) else env_key)
            return env_key.encode() if isinstance(env_key, str) else env_key
        except Exception as e:
            raise RuntimeError(
                f"{_SECRET_ENV_VAR} 格式错误：{e}。"
                "请使用 `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` 生成。"
            )

    # 2. 本地文件（dev 环境自动管理）
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_bytes().strip()

    # 3. 都没有 —— 生成新的密钥并持久化
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    new_key = Fernet.generate_key()
    _SECRET_FILE.write_bytes(new_key)
    try:
        os.chmod(_SECRET_FILE, 0o600)
    except Exception:
        pass
    print(
        f"[crypto] 生成新的加密密钥并保存到 {_SECRET_FILE}。"
        f"生产环境建议通过 {_SECRET_ENV_VAR} 环境变量管理。"
    )
    return new_key


# 模块加载时初始化 Fernet 实例（单例）
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def is_encrypted(value: Optional[str]) -> bool:
    """判断一个字符串是否是本模块加密过的密文"""
    if not value:
        return False
    return value.startswith(_ENC_PREFIX)


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    """
    加密明文。空值直接返回，已经加密过的字符串也直接返回（幂等）。
    """
    if plaintext is None or plaintext == "":
        return plaintext
    if is_encrypted(plaintext):
        return plaintext  # 幂等
    token = _get_fernet().encrypt(plaintext.encode("utf-8"))
    return _ENC_PREFIX + token.decode("ascii")


def decrypt(ciphertext: Optional[str]) -> Optional[str]:
    """
    解密密文。
    对于历史明文（没有 ENC: 前缀）直接返回原值，保证向前兼容。
    对于真正解密失败的值，记录日志后返回 None（而不是整个系统崩溃）。
    """
    if ciphertext is None or ciphertext == "":
        return ciphertext
    if not is_encrypted(ciphertext):
        # 历史明文或误存内容，按明文对待
        return ciphertext
    token = ciphertext[len(_ENC_PREFIX):]
    try:
        return _get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        print("[crypto] 解密失败：密钥可能已变更或数据被篡改")
        return None


def generate_key_for_deployment() -> str:
    """辅助工具：生成一个新的 Fernet 密钥字符串（用于部署时设置环境变量）"""
    return Fernet.generate_key().decode("ascii")


def mask_secret(value: Optional[str], show_last: int = 0) -> str:
    """用于日志：把密码/密钥脱敏显示"""
    if not value:
        return ""
    if show_last <= 0 or len(value) <= show_last:
        return "*" * 8
    return "*" * 8 + value[-show_last:]
