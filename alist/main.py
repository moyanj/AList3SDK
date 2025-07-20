from token import OP
from typing import Union, BinaryIO, Dict, Optional, AsyncGenerator
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

File = Union[str, model.AListFile]
Folder = Union[str, model.AListFolder]
Paths = Union[File, Folder]
ALFS = Union[model.AListFile, model.AListFolder]


class AList:
    """
    AList的SDK，此为主类。

    Attributes:
        endpoint (str): AList地址
        headers (Dict[str, Optional[str]]): 全局请求头
        token (str): JWT Token
    """

    endpoint: str
    headers: Dict[str, Optional[str]]
    token: str
    proxy_url: Optional[str]

    def __init__(self, endpoint: str, proxy: Optional[str] = None):
        """
        初始化

        Args:
            endpoint (str): AList地址
        """
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            pass
        else:
            raise ValueError(f"{endpoint} 不是有效的uri")

        self.endpoint = endpoint  # alist地址
        self.proxy_url = proxy
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
            "User-Agent": f"AListSDK/1.3.8 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
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
        async with aiohttp.ClientSession(proxy=self.proxy_url) as session:
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

        if data == "pong":
            return True
        return False

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
        self.headers["Authorization"] = f"{self.token}"
        return True

    async def search_file(
        self,
        keywords,
        parent: str = "",
        scope: int = 0,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        password: str = "",
    ) -> utils.ToClass:
        url = "/api/fs/search"
        data = {
            "parent": parent,
            "scope": scope,
            "page": page,
            "per_page": per_page,
            "password": password,
            "keywords": keywords,
        }
        r = await self._request("POST", url, data=json.dumps(utils.clear_dict(data)))
        self._isBadRequest(r, "文件搜索失败")
        return utils.ToClass(r).data

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

    async def rename_regex(
        self, src_dir: str, src_name_regex: str, dst_name_regex: str
    ):
        """
        正则重命名
        """
        url = "/api/fs/regex_rename"
        data = {
            "src_dir": src_dir,
            "src_name_regex": src_name_regex,
            "dst_name_regex": dst_name_regex,
        }
        r = await self._request("POST", url, data=json.dumps(data))
        self._isBadRequest(r, "正则重命名失败")
        return True

    async def rename_batch(self, src_dir, src: list[File], dst: list[File]) -> bool:
        """
        批量重命名
        """
        url = "/api/fs/batch_rename"
        data = {
            "src_dir": src_dir,
            "rename_object": [
                {"src": str(src[i]), "dst": str(dst[i])} for i in range(len(src))
            ],
        }
        r = await self._request("POST", url, data=json.dumps(data))
        self._isBadRequest(r, "批量重命名失败")
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

    async def recursive_move(self, src: Folder, dstDir: Folder) -> bool:
        """
        递归移动文件夹
        """
        url = "/api/fs/recursive_move"
        data = {
            "src_dir": str(src),
            "dst_dir": str(dstDir),
        }
        r = await self._request("POST", url, data=json.dumps(data))
        self._isBadRequest(r, "递归移动失败")
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

    async def create_meta(
        self,
        path: str,
        password: Optional[str],
        p_sub: Optional[bool],
        write: Optional[bool],
        w_sub: Optional[bool],
        hide: Optional[bool],
        h_sub: Optional[bool],
        readme: Optional[bool],
        r_sub: Optional[bool],
    ):
        """
        更新元数据
        Args:
            path (str): 元数据路径
            password (Optional[str]): 密码
            p_sub (Optional[bool]): 密码是否应用到子文件夹
            write (Optional[bool]): 是否开启写入
            w_sub (Optional[bool]): 开启写入是否应用到子文件夹
            hide (Optional[bool]): 是否隐藏
            h_sub (Optional[bool]): 隐藏是否应用到子文件夹
            readme (Optional[bool]): 说明
            r_sub (Optional[bool]): 说明是否应用到子文件夹

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/meta/create"
        data = utils.clear_dict(
            {
                "path": path,
                "password": password,
                "p_sub": p_sub,
                "write": write,
                "w_sub": w_sub,
                "hide": hide,
                "h_sub": h_sub,
                "readme": readme,
                "r_sub": r_sub,
            }
        )
        r = await self._request("POST", url, json=data)
        self._isBadRequest(r, "无法创建元数据")
        return True

    async def update_meta(
        self,
        path: str,
        password: Optional[str],
        p_sub: Optional[bool],
        write: Optional[bool],
        w_sub: Optional[bool],
        hide: Optional[bool],
        h_sub: Optional[bool],
        readme: Optional[str],
        r_sub: Optional[bool],
    ):
        """
        更新元数据
        Args:
            path (str): 元数据路径
            password (Optional[str]): 密码
            p_sub (Optional[bool]): 密码是否应用到子文件夹
            write (Optional[bool]): 是否开启写入
            w_sub (Optional[bool]): 开启写入是否应用到子文件夹
            hide (Optional[bool]): 是否隐藏
            h_sub (Optional[bool]): 隐藏是否应用到子文件夹
            readme (Optional[bool]): 说明
            r_sub (Optional[bool]): 说明是否应用到子文件夹

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/meta/update"
        data = utils.clear_dict(
            {
                "path": path,
                "password": password,
                "p_sub": p_sub,
                "write": write,
                "w_sub": w_sub,
                "hide": hide,
                "h_sub": h_sub,
                "readme": readme,
                "r_sub": r_sub,
            }
        )
        r = await self._request("POST", url, json=data)
        self._isBadRequest(r, "无法创建元数据")
        return True

    async def delete_meta(self, idx: int) -> bool:
        """
        删除元数据

        Args:
            idx (int): 元数据ID

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/meta/delete"
        r = await self._request("POST", url, param={"id": idx})
        self._isBadRequest(r, "无法删除元数据")
        return True

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

    async def delete_user_cache(self, username: str) -> bool:
        """
        删除用户缓存

        Args:
            username (str): 用户名

        Returns:
            (bool): 是否成功
        """
        url = "/api/admin/user/delete_cache"
        r = await self._request("POST", url, param={"username": username})
        self._isBadRequest(r, "无法删除用户缓存")
        return True

    async def craete_storage(
        self,
        mount_path: str,
        driver: str,
        addition: dict,
        order: int = 0,
        remark: str = "",
        cache_expires: Optional[int] = None,
        web_proxy: bool = False,
        webdav_policy: str = "native_proxy",
        down_proxy_url: Optional[str] = None,
        order_by: str = "name",
        extract_folder: Optional[str] = None,
        order_direction: str = "asc",
        enable_sign: bool = False,
    ) -> bool:
        """
        创建存储

        Args:
            mount_path (str): 挂载路径
            driver (str): 驱动
            addition (dict): 额外参数
            order (int, optional): 排序. Defaults to 0.
            remark (str, optional): 备注.
            cache_expires (int, optional): 缓存过期时间.
            web_proxy (bool, optional): 是否开启web代理.
            webdav_policy (str, optional): webdav策略.
            down_proxy_url (str, optional): 下载代理地址.
            order_by (str, optional): 排序字段.
            extract_folder (str, optional): 解压文件夹.
            order_direction (str, optional): 排序方向.
            enable_sign (bool, optional): 是否开启签名.

        Returns:
            bool: 是否成功
        """
        url = "/api/admin/storage/create"
        addition_str = json.dumps(addition)
        data = {
            "mount_path": mount_path,
            "driver": driver,
            "addition": addition_str,
            "order": order,
            "remark": remark,
            "cache_expires": cache_expires,
            "web_proxy": web_proxy,
            "webdav_policy": webdav_policy,
            "down_proxy_url": down_proxy_url,
            "order_by": order_by,
            "extract_folder": extract_folder,
            "order_direction": order_direction,
            "enable_sign": enable_sign,
        }
        r = await self._request("POST", url, data=json.dumps(utils.clear_dict(data)))
        self._isBadRequest(r, "创建存储失败")
        return True

    async def update_storage(
        self,
        mount_path: Optional[str] = None,
        driver: Optional[str] = None,
        addition: Optional[dict] = None,
        order: int = 0,
        remark: str = "",
        cache_expires: Optional[int] = None,
        web_proxy: bool = False,
        webdav_policy: str = "native_proxy",
        down_proxy_url: Optional[str] = None,
        order_by: str = "name",
        extract_folder: Optional[str] = None,
        order_direction: str = "asc",
        enable_sign: bool = False,
    ) -> bool:
        """
        更新存储

        Args:
            mount_path (str, optional): 挂载路径
            driver (str, optional): 驱动
            addition (dict, optional): 额外参数
            order (int, optional): 排序. Defaults to 0.
            remark (str, optional): 备注.
            cache_expires (int, optional): 缓存过期时间.
            web_proxy (bool, optional): 是否开启web代理.
            webdav_policy (str, optional): webdav策略.
            down_proxy_url (str, optional): 下载代理地址.
            order_by (str, optional): 排序字段.
            extract_folder (str, optional): 解压文件夹.
            order_direction (str, optional): 排序方向.
            enable_sign (bool, optional): 是否开启签名.

        Returns:
            bool: 是否成功
        """
        url = "/api/admin/storage/update"
        addition_str = json.dumps(addition)
        data = {
            "mount_path": mount_path,
            "driver": driver,
            "addition": addition_str,
            "order": order,
            "remark": remark,
            "cache_expires": cache_expires,
            "web_proxy": web_proxy,
            "webdav_policy": webdav_policy,
            "down_proxy_url": down_proxy_url,
            "order_by": order_by,
            "extract_folder": extract_folder,
            "order_direction": order_direction,
            "enable_sign": enable_sign,
        }
        r = await self._request("POST", url, data=json.dumps(utils.clear_dict(data)))
        self._isBadRequest(r, "创建存储失败")
        return True

    async def enable_storage(self, storage_id: int):
        """
        启用存储
        """
        url = "/api/admin/storage/enable"
        r = await self._request("POST", url, data={"id": storage_id})
        self._isBadRequest(r, "启用存储失败")
        return True

    async def disable_storage(self, storage_id: int):
        """
        禁用存储
        """
        url = "/api/admin/storage/disable"
        r = await self._request("POST", url, data={"id": storage_id})
        self._isBadRequest(r, "禁用存储失败")
        return True

    async def list_storages(
        self, page: Optional[int] = None, per_page: Optional[int] = None
    ):
        """
        获取存储列表
        """
        url = "/api/admin/storage/list"
        r = await self._request(
            "GET", url, params=utils.clear_dict({"page": page, "per_page": per_page})
        )
        self._isBadRequest(r, "获取存储列表失败")
        return utils.ToClass(r).data

    async def get_storage(self, storage_id: int):
        """
        获取存储

        Args:
            storage_id (str): 存储ID
        """
        url = "/api/admin/storage/get"
        r = await self._request("GET", url, params={"id": storage_id})
        self._isBadRequest(r, "获取存储失败")
        return utils.ToClass(r).data

    async def reload_storage(self):
        """
        重载存储
        """
        url = "/api/admin/storage/load_all"
        r = await self._request("POST", url)
        self._isBadRequest(r, "重载存储失败")
        return True

    async def delete_storage(self, storage_id: int):
        """
        删除存储
        """
        url = "/api/admin/storage/delete"
        r = await self._request("POST", url, params={"id": storage_id})
        self._isBadRequest(r, "删除存储失败")
        return True

    async def list_driver(self):
        """
        获取驱动列表
        """
        url = "/api/admin/driver/list"
        r = await self._request("GET", url)
        self._isBadRequest(r, "获取驱动列表失败")
        return utils.ToClass(r).data

    async def list_driver_names(self):
        """
        获取驱动名称列表
        """
        url = "/api/admin/driver/names"
        r = await self._request("GET", url)
        self._isBadRequest(r, "获取驱动名称列表失败")
        return utils.ToClass(r).data

    async def get_driver_info(self, driver_name: str):
        """
        获取驱动信息
        """
        url = "/api/admin/driver/info"
        r = await self._request("GET", url, params={"name": driver_name})
        self._isBadRequest(r, "获取驱动信息失败")
        return utils.ToClass(r).data

    async def add_offline_download(
        self,
        urls: list[str],
        path: str,
        tool: str = "SimpleHttp",
        delete_policy: str = "delete_on_upload_succeed",
    ):
        """
        添加离线下载
        """
        url = "/api/fs/add_offline_download"
        data = {
            "urls": urls,
            "path": path,
            "tool": tool,
            "delete_policy": delete_policy,
        }
        r = await self._request(
            "POST",
            url,
            data=json.dumps(data),
        )
        self._isBadRequest(r, "添加离线下载失败")
        return utils.ToClass(r).data

    def to_sync(self):
        """
        转换为同步对象"
        """
        from . import sync

        return sync.AListSync(async_obj=self)
