# pylint:disable=W0707
import aiohttp
import json
import os.path
import sys
import asyncio

from platform import platform
from urllib.parse import quote
from typing import Union
from urllib.parse import urljoin

from . import error, file, folder, utils


class AList:
    """
    AList的SDK，此为主类。
    """

    def __init__(self, endpoint: str):
        """
        初始化

        Args:
            endpoint (str):AList地址
            test (bool):是否测试服务器可用性
        """
        if "http" not in endpoint:
            raise ValueError(endpoint + "不是有效的uri")

        self.endpoint = endpoint  # alist地址
        self.token = ""  # JWT Token

        # 构建UA
        ver = [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
        ver = ".".join(ver)
        pf = platform().split("-")

        self.headers = {
            "User-Agent": f"AListSDK/1.3.0 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    def _isBadRequest(self, r, msg):
        # 是否为不好的请求
        if r["code"] != 200:
            raise error.ServerError(msg + ":" + r["message"])

    async def _request(self, method: str, path: str, *args, **kwargs):
        url = urljoin(self.endpoint, path)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, *args, **kwargs) as response:
                return await response.json()

    async def test(self):
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

    async def login(self, user: utils.AListUser, otp_code: str = ""):
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
        data = json.dumps(data)

        data = await self._request(
            "POST", "/api/auth/login/hash", headers=self.headers, data=data
        )
        # 处理返回数据
        self._isBadRequest(data, "Account or password error")

        # 保存
        self.token = data["data"]["token"]
        self.headers["Authorization"] = self.token
        return True

    def Login(self, *args, **kwargs):
        """
        登录

        Args:
            user (AListUser): AList用户

        Returns:
            (bool): 是否成功

        """
        raise error.DeprecationError("请使用login函数")

    async def user_info(self):
        """
        获取当前登录的用户的信息

        Returns:
            (dict):一个字典，包含了当前用户的信息。

        """

        r = await self._request("GET", "/api/me", headers=self.headers)
        return utils.ToClass(r).data

    def UserInfo(self):
        raise error.DeprecationError("请使用user_info函数")

    async def list_dir(
        self,
        path: Union[str, folder.AListFolder],
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
        r = await self._request("POST", "/api/fs/list", data=data, headers=self.headers)
        self._isBadRequest(r, "获取失败")

        for item in r["data"]["content"]:
            i = {
                "path": os.path.join(str(path), item["name"]),
                "is_dir": item["is_dir"],
            }
            yield utils.ToClass(i)

    def ListDir(self, *args, **kwargs):
        raise error.DeprecationError("请使用list_dir函数")

    async def open(
        self, path: Union[str, folder.AListFolder, file.AListFile], password: str = ""
    ):
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
        rjson = await self._request(
            "POST", "/api/fs/get", headers=self.headers, data=data
        )

        if rjson["data"]["is_dir"]:
            return folder.AListFolder(str(path), rjson["data"])
        else:
            return file.AListFile(str(path), rjson["data"])

    async def mkdir(self, path: str):
        """
        创建文件夹

        Args:
            path (str): 要创建的目录

        Returns:
            (bool): 是否成功


        """
        data = json.dumps({"path": path})

        r = await self._request("POST", "/api/fs/mkdir", data=data, headers=self.headers)
        self._isBadRequest(r, "创建失败")

        return True

    def Mkdir(self, *args, **kwargs):
        raise error.DeprecationError("请使用mkdir函数")

    async def upload(self, path: Union[str, file.AListFile], local: str):
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

        r = await self._request("PUT","/api/fs/put", data=files, headers=headers)
        self._isBadRequest(r, "上传失败")

        return True

    def Upload(self, *args, **kwargs):
        raise error.DeprecationError("请使用upload函数")

    async def rename(self, src: Union[str, folder.AListFolder, file.AListFile], dst: str):
        """
        重命名

        Args:
            src (str, AListFolder, AListFile): 原名
            dst (str): 要更改的名字

        Returns:
            (bool): 是否成功


        """

        data = json.dumps({"path": str(src), "name": dst})

        r = await self._request("POST","/api/fs/rename", headers=self.headers, data=data)
        self._isBadRequest(r, "重命名失败")
        return True

    def Rename(self, *args, **kwargs):
        raise error.DeprecationError("请使用rename函数")

    async def remove(self, path: Union[str, file.AListFile]):
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

        r = await self._request("POST","/api/fs/remove", data=payload, headers=self.headers)
        self._isBadRequest(r, "删除失败")
        return True

    def Remove(self, *args, **kwargs):
        raise error.DeprecationError("请使用remove函数")

    async def RemoveFolder(self, path: Union[str, folder.AListFolder]):
        """
        删除文件夹(需为空)

        Args:
            path (str, AListFolder): 文件夹路径

        Returns:
            (bool): 是否成功


        """

        data = json.dumps({"src_dir": str(path)})
        r = await self._request("POST","/api/fs/remove_empty_directory", data=data, headers=self.headers)
        self._isBadRequest(r, "删除失败")
        return True

    def Mkdir(self, *args, **kwargs):
        raise error.DeprecationError("请使用mkdir函数")

    async def copy(
        self, src: Union[str, file.AListFile], dstDir: Union[str, folder.AListFolder]
    ):
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
        r = await self._request("POST","/api/fs/copy", data=data, headers=self.headers)
        self._isBadRequest(r, "复制失败")
        return True

    def Copy(self, *args, **kwargs):
        raise error.DeprecationError("请使用copy函数")

    async def move(
        self, src: Union[str, file.AListFile], dstDir: Union[str, folder.AListFolder]
    ):
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
        r = await self._request("POST","/api/fs/move", data=data, headers=self.headers)
        self._isBadRequest(r, "移动失败")
        return True

    def Move(self, *args, **kwargs):
        raise error.DeprecationError("请使用move函数")

    async def site_config(self):
        """
        获取公开站点配置

        Returns:
            (ToClass): 配置


        """

        url = "/api/public/settings"
        r = await self._request("GET", url, headers=self.headers)
        self._isBadRequest(r, "AList配置信息获取失败")
        return utils.ToClass(r).data

    def SiteConfig(self, *args, **kwargs):
        raise error.DeprecationError("请使用site_config函数")


class AListAdmin(AList):
    """
    管理员操作
    (继承于AList类)

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

    async def list_meta(self, page: int = None, per_page=None):
        """
        列出元数据

        Args:
            page (int) : 页数
            per_page (int) : 每页的数量

        Return:
            (ToClass) 数据
        """

        prams = {"page": page, "per_page": per_page}
        r = await self._request("GET","/api/admin/meta/list", params=prams, headers=self.headers)
        self._isBadRequest(r, "无法列出元数据")
        return utils.ToClass(r).data

    def ListMeta(self, *args, **kwargs):
        raise error.DeprecationError("请使用list_meta函数")

    async def get_meta(self, idx):
        """
        获取元数据

        Args:
            idx (int) : 元数据id

        Return:
            (ToClass) 数据
        """

        url = "/api/admin/meta/get"
        r = await self._request(url, params={"id": idx}, headers=self.headers)
        self._isBadRequest(r, "无法找到该元数据")
        return utils.ToClass(r).data

    def GetMeta(self, *args, **kwargs):
        raise error.DeprecationError("请使用get_meta函数")
