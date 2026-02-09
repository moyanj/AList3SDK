import os
import pickle
from typing import Optional, Tuple

from alist import AList, AListUser
from ._data import dirs, console


async def get_client(username: Optional[str] = None) -> Tuple[AList, str]:
    """
    获取 AList 客户端和当前路径
    """
    auth_dir = dirs.auths
    if not os.path.exists(auth_dir):
        raise RuntimeError("CLI 未初始化，请先使用 'alist3 auth add' 添加用户")

    user_file = None
    if username:
        # 查找指定用户
        if os.path.exists(os.path.join(auth_dir, username)):
            user_file = username
        elif os.path.exists(os.path.join(auth_dir, f"{username}.__default")):
            user_file = f"{username}.__default"
    else:
        # 查找默认用户
        for f in os.listdir(auth_dir):
            if f.endswith(".__default"):
                user_file = f
                break

    if not user_file:
        if username:
            raise RuntimeError(f"未找到用户: {username}")
        else:
            raise RuntimeError(
                "未设置默认用户，请指定用户或使用 'alist3 auth add --default' 设置默认用户"
            )

    with open(os.path.join(auth_dir, user_file), "rb") as f:
        data = pickle.load(f)

    endpoint = data["endpoint"]
    user_bytes = data["user"]
    user = AListUser.loads(user_bytes)

    client = AList(endpoint)
    if not await client.login(user):
        raise RuntimeError(f"登录失败: {endpoint}")

    return client, "/"  # 默认从根目录开始
