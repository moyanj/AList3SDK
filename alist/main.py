from typing import Union, BinaryIO, Dict, List, Optional, AsyncGenerator
from . import error, model, utils
import sys
from platform import platform
import os
import aiohttp
from urllib.parse import urljoin, quote

try:
    import ujson as json
except ImportError:
    import json

StrNone = Union[str, None]
File = Union[str, model.AListFile]
Folder = Union[str, model.AListFolder]
Paths = Union[File, Folder]
ALFS = Union[model.AListFile, model.AListFolder]


class AList:
    """
    AList的SDK，此为主类。

    Attributes:
        endpoint (str): AList地址
        headers (Dict[str, StrNone]): 全局请求头
        token (str): JWT Token
    """

    endpoint: str
    headers: Dict[str, StrNone]
    token: str

    def __init__(self, endpoint: str):
        """
        初始化

        Args:
            endpoint (str): AList地址
        """
        if "http" not in endpoint:
            raise ValueError(f"{endpoint} 不是有效的uri")

        self.endpoint = endpoint  # alist地址
        self.token = ""  # JWT Token

        # 构建UA
        ver = ".".join(
            [
                str(sys.version_info.major),
                str(sys.version_info.minor),
                str(sys.version_info.micro),
            ]
        )
        pf = platform().split("-")

        self.headers = {
            "User-Agent": f"AListSDK/1.3.6 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    def _isBadRequest(self, r: Dict, msg: str) -> None:
        # 是否为不好的请求
        if r["code"] != 200:
            raise error.ServerError(f"{msg}: {r['message']}")

    async def _request(
        self, method: str, path: str, headers: Optional[Dict] = None, **kwargs
    ) -> Dict:
        url = urljoin(self.endpoint, path)
        if headers is None:
            headers = self.headers
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, **kwargs) as response:  # type: ignore
                return await response.json()

    async def test(self) -> bool:
        """
        测试服务器可用性

        Returns:
            (bool): 是否可用
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(urljoin(self.endpoint, "/ping")) as response:
                    data = await response.text()
        except Exception as e:
            print(f"Error: {e}")
            return False

        if data != "pong":
            return False
        return True

    async def login(self, user: utils.AListUser, otp_code: str = "") -> bool:
        """
        登录

        Args:
            user (AListUser): AList用户
            otp_code (str): OTP验证码

        Returns:
            (bool): 是否成功
        """
        password = user.pwd
        username = user.un

        # 构建json数据
        data = {"username": username, "password": password, "otp_code": otp_code}
        payload = json.dumps(data)

        res = await self._request("POST", "/api/auth/login/hash", data=payload)
        # 处理返回数据
        self._isBadRequest(res, "Account or password error")

        # 保存
        self.token = res["data"]["token"]
        self.headers["Authorization"] = f"Bearer {self.token}"
        return True

    async def user_info(self) -> utils.ToClass:
        """
        获取当前登录的用户的信息

        Returns:
            (ToClass): 一个字典，包含了当前用户的信息。
        """
        r = await self._request("GET", "/api/me")
        return utils.ToClass(r).data

    async def list_dir(
        self,
        path: Folder,
        page: int = 1,
        per_page: int = 50,
        refresh: bool = False,
        password: str = "",
    ) -> AsyncGenerator[utils.ToClass, None]:
        """
        列出指定目录下的所有文件或文件夹。

        Args:
            path (str, AListFolder): 需要列出的目录
            page (int): 页数
            per_page (int): 每页的数量
            refresh (bool): 是否强制刷新
            password (str): 目录密码

        Returns:
            (Generator[utils.ToClass, None, None]): 指定目录下的文件
        """
        data = json.dumps(
            {
                "path": str(path),
                "password": password,
                "page": page,
                "per_page": per_page,
                "refresh": refresh,
            }
        )
        r = await self._request("POST", "/api/fs/list", data=data)
        self._isBadRequest(r, "获取失败")

        for item in r["data"]["content"]:
            i = {
                "path": os.path.join(str(path), item["name"]),
                "is_dir": item["is_dir"],
            }
            yield utils.ToClass(i)

    async def open(self, path: Paths, password: str = "") -> ALFS:
        """
        打开文件/文件夹

        Args:
            path (str, AListFolder, AListFile): 路径
            password (str): 密码

        Returns:
            (AListFolder): AList目录对象
            (AListFile): AList文件对象
        """
        data = json.dumps({"path": str(path), "password": password})
        rjson = await self._request("POST", "/api/fs/get", data=data)

        if rjson["data"]["is_dir"]:
            return model.AListFolder(str(path), rjson["data"])
        else:
            return model.AListFile(str(path), rjson["data"])

    async def mkdir(self, path: Folder) -> bool:
        """
        创建文件夹

        Args:
            path (str): 要创建的目录

        Returns:
            (bool): 是否成功
        """
        data = json.dumps({"path": str(path)})

        r = await self._request("POST", "/api/fs/mkdir", data=data)
        self._isBadRequest(r, "创建失败")

        return True

    async def upload(
        self, path: Union[str, model.AListFile], local: Union[str, bytes, BinaryIO]
    ) -> bool:
        """
        上传文件

        Args:
            path (str, AListFile): 上传的路径
            local (str, bytes, BinaryIO): 本地路径或字节数据或文件指针

        Returns:
            (bool): 是否成功
        """
        if isinstance(local, bytes):
            files = local
        elif isinstance(local, BinaryIO):
            files = local.read()
        else:
            with open(local, "rb") as f:
                files = f.read()

        FilePath = quote(str(path))

        headers = self.headers.copy()
        headers["File-Path"] = FilePath
        headers["Content-Length"] = str(len(files))
        del headers["Content-Type"]

        r = await self._request("PUT", "/api/fs/put", data=files, headers=headers)
        self._isBadRequest(r, "上传失败")

        return True

    async def rename(self, src: Paths, dst: str) -> bool:
        """
        重命名

        Args:
            src (str, AListFolder, AListFile): 原名
            dst (str): 要更改的名字

        Returns:
            (bool): 是否成功
        """
        data = json.dumps({"path": str(src), "name": dst})

        r = await self._request("POST", "/api/fs/rename", data=data)
        self._isBadRequest(r, "重命名失败")
        return True

    async def remove(self, path: File) -> bool:
        """
        删除

        Args:
            path (str, AListFile): 要删除的文件

        Returns:
            (bool): 是否成功
        """
        payload = json.dumps(
            {
                "names": [str(os.path.basename(str(path)))],
                "dir": str(os.path.dirname(str(path))),
            }
        )

        r = await self._request("POST", "/api/fs/remove", data=payload)
        self._isBadRequest(r, "删除失败")
        return True

    async def remove_folder(self, path: Folder) -> bool:
        """
        删除文件夹(需为空)

        Args:
            path (str, AListFolder): 文件夹路径

        Returns:
            (bool): 是否成功
        """
        data = json.dumps({"src_dir": str(path)})
        r = await self._request("POST", "/api/fs/remove_empty_directory", data=data)
        self._isBadRequest(r, "删除失败")
        return True

    async def copy(self, src: File, dstDir: Folder) -> bool:
        """
        复制文件

        Args:
            src (str, AListFile): 源文件
            dstDir (str): 要复制到的路径

        Returns:
            (bool): 是否成功
        """
        data = json.dumps(
            {
                "src_dir": os.path.dirname(str(src)),
                "dst_dir": str(dstDir),
                "names": [os.path.basename(str(src))],
            }
        )
        r = await self._request("POST", "/api/fs/copy", data=data)
        self._isBadRequest(r, "复制失败")
        return True

    async def move(self, src: File, dstDir: Folder) -> bool:
        """
        移动文件

        Args:
            src (str, AListFile): 源文件
            dstDir (str): 要移动到的路径

        Returns:
            (bool): 是否成功
        """
        data = json.dumps(
            {
                "src_dir": os.path.dirname(str(src)),
                "dst_dir": str(dstDir),
                "names": [os.path.basename(str(src))],
            }
        )
        r = await self._request("POST", "/api/fs/move", data=data)
        self._isBadRequest(r, "移动失败")
        return True

    async def site_config(self) -> utils.ToClass:
        """
        获取公开站点配置

        Returns:
            (ToClass): 配置
        """
        url = "/api/public/settings"
        r = await self._request("GET", url)
        self._isBadRequest(r, "AList配置信息获取失败")
        return utils.ToClass(r).data

    async def list_meta(
        self, page: Optional[int] = None, per_page: Optional[int] = None
    ) -> utils.ToClass:
        """
        列出元数据

        Args:
            page (int): 页数
            per_page (int): 每页的数量

        Returns:
            (ToClass): 数据
        """
        prams = utils.clear_dict({"page": page, "per_page": per_page})

        r = await self._request("GET", "/api/admin/meta/list", params=prams)
        self._isBadRequest(r, "无法列出元数据")
        return utils.ToClass(r).data

    async def get_meta(self, idx: int) -> utils.ToClass:
        """
        获取元数据

        Args:
            idx (int): 元数据id

        Returns:
            (ToClass): 数据
        """
        url = "/api/admin/meta/get"
        r = await self._request("GET", url, params={"id": idx})
        self._isBadRequest(r, "无法找到该元数据")
        return utils.ToClass(r).data

    async def get_users(self) -> utils.ToClass:
        """
        获取用户列表

        Returns:
            (ToClass): 数据
        """
        url = "/api/admin/user/list"
        r = await self._request("GET", url)
        self._isBadRequest(r, "无法获取用户列表")
        return utils.ToClass(r).data

    async def get_user(self, idx: int) -> utils.ToClass:
        """
        获取用户

        Args:
            idx (int): 用户id

        Returns:
            (ToClass): 数据
        """
        url = "/api/admin/user/get"
        r = await self._request("GET", url, params={"id": idx})
        self._isBadRequest(r, "无法找到该用户")
        return utils.ToClass(r).data

    async def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        base_path: Optional[str] = None,
        role: Optional[str] = None,
        permission: Optional[int] = None,
        disabled: Optional[bool] = None,
        sso_id: Optional[str] = None,
    ) -> bool:
        """
        创建用户

        Args:
            username (str): 用户名
            password (Optional[str]): 密码
            base_path (Optional[str]): 基础路径
            role (Optional[str]): 角色
            permission (Optional[int]): 权限
            disabled (Optional[bool]): 是否禁用
            sso_id (Optional[str]): SSO ID

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/user/create"
        data = json.dumps(
            utils.clear_dict(
                {
                    "username": username,
                    "password": password,
                    "base_path": base_path,
                    "role": role,
                    "permission": permission,
                    "disabled": disabled,
                    "sso_id": sso_id,
                }
            )
        )
        r = await self._request("POST", url, data=data)
        self._isBadRequest(r, "无法创建用户")
        return True

    async def update_user(
        self,
        idx: int,
        username: str,
        password: Optional[str] = None,
        base_path: Optional[str] = None,
        role: Optional[str] = None,
        permission: Optional[int] = None,
        disabled: Optional[bool] = None,
        sso_id: Optional[str] = None,
    ) -> bool:
        """
        更新用户

        Args:
            idx (int): 用户ID
            username (str): 用户名
            password (Optional[str]): 密码
            base_path (Optional[str]): 基础路径
            role (Optional[str]): 角色
            permission (Optional[int]): 权限
            disabled (Optional[bool]): 是否禁用
            sso_id (Optional[str]): SSO ID

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/user/update"
        data = json.dumps(
            utils.clear_dict(
                {
                    "id": idx,
                    "username": username,
                    "password": password,
                    "base_path": base_path,
                    "role": role,
                    "permission": permission,
                    "disabled": disabled,
                    "sso_id": sso_id,
                }
            )
        )
        r = await self._request("POST", url, data=data)
        self._isBadRequest(r, "无法更新用户")
        return True

    async def delete_user(self, idx: int) -> bool:
        """
        删除用户

        Args:
            idx (int): 用户ID

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/user/delete"
        r = await self._request("POST", url, data=json.dumps({"id": idx}))
        self._isBadRequest(r, "无法删除用户")
        return True
