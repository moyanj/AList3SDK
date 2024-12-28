# pylint:disable=W0707
import aiohttp
import os
import sys

from platform import platform
from urllib.parse import quote, urljoin
from typing import Union

from . import error, model, utils

try:
    import ujson as json
except ImportError:
    import json

StrNone = Union[str, None]
File = Union[str, model.AListFile]
Floder = Union[str, model.AListFolder]
Paths = Union[File, model.AListFolder]
ALFS = Union[model.AListFile, model.AListFolder]


class AList:
    """
    AList的SDK，此为主类。

    Attributes:
        endpoint (str):AList地址
        headers (dict):全局请求头
        token (str):JWT Token
    """

    endpoint: str
    headers: dict[str, StrNone]
    token: str

    def __init__(self, endpoint: str):
        """
        初始化

        Args:
            endpoint (str):AList地址
        """
        if "http" not in endpoint:
            raise ValueError(endpoint + "不是有效的uri")

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
            "User-Agent": f"AListSDK/1.3.4 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    def _isBadRequest(self, r, msg):
        # 是否为不好的请求
        if r["code"] != 200:
            raise error.ServerError(msg + ":" + r["message"])

    async def _request(self, method: str, path: str, headers=None, **kwargs) -> dict:
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
        except:
            return False

        if data != "pong":
            return False
        return True

    def Test(self):
        raise error.DeprecationError("请使用test函数")

    async def login(self, user: utils.AListUser, otp_code: str = "") -> bool:
        """
        登录

        Args:
            user (AListUser): AList用户

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
        self.headers["Authorization"] = self.token
        return True

    def Login(self, *args, **kwargs):
        raise error.DeprecationError("请使用login函数")

    async def user_info(self) -> utils.ToClass:
        """
        获取当前登录的用户的信息

        Returns:
            (ToClass):一个字典，包含了当前用户的信息。

        """

        r = await self._request("GET", "/api/me")
        return utils.ToClass(r).data

    def UserInfo(self):
        raise error.DeprecationError("请使用user_info函数")

    async def list_dir(
        self,
        path: Floder,
        page: int = 1,
        per_page: int = 50,
        refresh: bool = False,
        password: str = "",
    ):
        """
        列出指定目录下的所有文件或文件夹。

        Args:
            path (str,AListFolder): 需要列出的目录
            page (int): 页数
            per_page (int): 每页的数量
            refresh (bool): 是否强制刷新
            password (str): 目录密码

        Returns:
            (generator):指定目录下的文件

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

    def ListDir(self, *args, **kwargs):
        raise error.DeprecationError("请使用list_dir函数")

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

    async def mkdir(self, path: Floder) -> bool:
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

    def Mkdir(self, *args, **kwargs):
        raise error.DeprecationError("请使用mkdir函数")

    async def upload(self, path: File, local: str) -> bool:
        """
        上传文件

        Args:
            path (str, AListFile): 上传的路径
            local (str): 本地路径

        Returns:
            (bool): 是否成功

        """

        files = open(local, "rb").read()
        FilePath = quote(str(path))

        headers = self.headers.copy()
        headers["File-Path"] = FilePath
        headers["Content-Length"] = str(len(files))
        del headers["Content-Type"]

        r = await self._request("PUT", "/api/fs/put", data=files, headers=headers)
        self._isBadRequest(r, "上传失败")

        return True

    def Upload(self, *args, **kwargs):
        raise error.DeprecationError("请使用upload函数")

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

    def Rename(self, *args, **kwargs):
        raise error.DeprecationError("请使用rename函数")

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

    def Remove(self, *args, **kwargs):
        raise error.DeprecationError("请使用remove函数")

    async def remove_folder(self, path: Floder) -> bool:
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

    def RemoveFolder(self, *args, **kwargs):
        raise error.DeprecationError("请使用remove_folder函数")

    async def copy(self, src: File, dstDir: Floder) -> bool:
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

    def Copy(self, *args, **kwargs):
        raise error.DeprecationError("请使用copy函数")

    async def move(self, src: File, dstDir: Floder) -> bool:
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

    def Move(self, *args, **kwargs):
        raise error.DeprecationError("请使用move函数")

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

    def SiteConfig(self, *args, **kwargs):
        raise error.DeprecationError("请使用site_config函数")


class AListAdmin(AList):
    """
    管理员操作

    Attributes:
        endpoint (str):AList地址
        headers (dict):全局请求头
        token (string):JWT Token
    """

    def __init__(self, user: utils.AListUser, endpoint: str):
        """
        初始化

        Args:
            user (AListUser) : 用户
            endpoint (str) : api端点
        """
        super().__init__(endpoint)
        self.Login(user)
        if self.UserInfo().id != 1:
            raise error.AuthenticationError("无管理员权限")

    async def list_meta(self, page: Union[int, None] = None, per_page=None):
        """
        列出元数据

        Args:
            page (int) : 页数
            per_page (int) : 每页的数量

        Return:
            (ToClass) 数据
        """

        prams = utils.clear_dict({"page": page, "per_page": per_page})

        r = await self._request("GET", "/api/admin/meta/list", params=prams)
        self._isBadRequest(r, "无法列出元数据")
        return utils.ToClass(r).data

    def ListMeta(self, *args, **kwargs):
        raise error.DeprecationError("请使用list_meta函数")

    async def get_meta(self, idx: int):
        """
        获取元数据

        Args:
            idx (int) : 元数据id

        Return:
            (ToClass) 数据
        """

        url = "/api/admin/meta/get"
        r = await self._request("GET", url, params={"id": idx})
        self._isBadRequest(r, "无法找到该元数据")
        return utils.ToClass(r).data

    def GetMeta(self, *args, **kwargs):
        raise error.DeprecationError("请使用get_meta函数")

    async def get_users(self):
        """
        获取用户列表

        Returns:
            (ToClass) 数据
        """
        url = "/api/admin/user/list"
        r = await self._request("GET", url)
        self._isBadRequest(r, "无法获取用户列表")
        return utils.ToClass(r).data

    async def get_user(self, idx: int):
        """
        获取用户

        Args:
            idx (int) : 用户id

        Returns:
            (ToClass) 数据
        """
        url = "/api/admin/user/get"
        r = await self._request("GET", url, params={"id": idx})
        self._isBadRequest(r, "无法找到该用户")
        return utils.ToClass(r).data

    async def create_user(
        self,
        username: str,
        password: StrNone = None,
        base_path: StrNone = None,
        role: StrNone = None,
        permission: Union[int, None] = None,
        disabled: Union[bool, None] = None,
        sso_id: StrNone = None,
    ):
        """
        创建用户
        Args:
            user (AListUser) : 用户
        Returns:
            (bool) 是否成功
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
        password: StrNone = None,
        base_path: StrNone = None,
        role: StrNone = None,
        permission: Union[int, None] = None,
        disabled: Union[bool, None] = None,
        sso_id: StrNone = None,
    ):
        """
        更新用户
        Args:
            user (AListUser) : 用户
        Returns:
            (bool) 是否成功
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

    async def delete_user(self, idx: int):
        """
        删除用户
        Args:
            idx (int) : 用户id
        Returns:
            (bool) 是否成功
        """
        url = "/api/admin/user/delete"
        r = await self._request("POST", url, data=json.dumps({"id": idx}))
        self._isBadRequest(r, "无法删除用户")
        return True
