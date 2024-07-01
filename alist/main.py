# pylint:disable=W0707
import json
import os
from hashlib import sha256
from platform import platform
from sys import version_info
from typing import Union
from urllib.parse import quote
from urllib.parse import urljoin

import requests

from .error import ServerError, AuthenticationError
from .file import AListFile
from .folder import AListFolder
from .utils import ToClass


class AListUser:
    def __init__(self, username: str, password: str, otp_code=None):
        """
        AList用户类

        Args:
            username (str): AList的用户名
            password (str): AList的密码
            otp_code (str): OTP

        """
        self.un = username
        self.pwd = password
        self.oc = otp_code


class AList:
    def __init__(self, endpoint: str):
        """
        AList的SDK，此为主类。

        Args:
            endpoint (str):AList地址
        """
        if "http" not in endpoint:
            raise ValueError(endpoint + "不是有效的uri")

        self.endpoint = endpoint  # alist地址
        self.token = ""  # JWT Token

        # 构建UA
        ver = [
            str(version_info.major),
            str(version_info.minor),
            str(version_info.micro),
        ]
        ver = ".".join(ver)
        pf = platform().split("-")

        self.headers = {
            "User-Agent": f"AListSDK/1.0 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    @classmethod
    def _is_bad_request(cls, r, msg):
        # 是否为不好的请求
        try:
            j = json.loads(r.text)
        except json.JSONDecodeError:
            raise ValueError("服务器返回数据不是JSON数据")

        if j["code"] != 200:
            raise ServerError(msg + ":" + j["message"])

    def _get_url(self, path):
        # 获取api端点
        return urljoin(self.endpoint, path)

    @classmethod
    def _parser_json(cls, js):
        return ToClass(json.loads(js))

    def login(self, user: AListUser):
        """
        登录

        Args:
            user (AListUser): AList用户

        Returns:
            (bool): 是否成功


        """
        password = user.pwd
        username = user.un
        otp_code = user.oc
        url = self._get_url("/api/auth/login/hash")

        # 对密码进行sha256摘要
        sha = sha256()
        sha.update(password.encode())
        sha.update(b"-https://github.com/alist-org/alist")
        sha256_password = sha.hexdigest()
        # 构建json数据
        data = {"username": username, "password": sha256_password, "otp_code": otp_code}
        data = json.dumps(data)

        r = requests.post(url, headers=self.headers, data=data)
        # 处理返回数据
        self._is_bad_request(r, "账号或密码错误")
        # 保存
        self.token = json.loads(r.text)["data"]["token"]
        self.headers["Authorization"] = self.token
        return True

    def user_info(self):
        """
        获取当前登录的用户的信息

        Returns:
            (dict):一个字典，包含了当前用户的信息。

        """

        url = self._get_url("/api/me")
        r = requests.get(url, headers=self.headers)
        return self._parser_json(r.text).data

    def list_dir(
            self,
            path: Union[str, AListFolder],
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

        url = self._get_url("/api/fs/list")

        data = json.dumps(
            {
                "path": str(path),
                "password": password,
                "page": page,
                "per_page": per_page,
                "refresh": refresh,
            }
        )
        r = requests.post(url, data=data, headers=self.headers)
        self._is_bad_request(r, "上传失败")

        for item in json.loads(r.text)["data"]["content"]:
            i = {"path": os.path.join(str(path), item["name"]), "is_dir": item["is_dir"]}
            yield ToClass(i)

    def open(self, path: Union[str, AListFolder, AListFile], password: str = ""):
        """
        打开文件/文件夹

        Args:
            path (str, AListFolder, AListFile): 路径
            password (str): 密码

        Returns:
            (AListFolder): AList目录对象
            (AListFile): AList文件对象


        """

        url = self._get_url("/api/fs/get")

        data = json.dumps({"path": str(path), "password": password})
        r = requests.post(url, headers=self.headers, data=data)

        r_json = json.loads(r.text)
        if r_json["data"]["is_dir"]:
            return AListFolder(str(path), r_json["data"])
        else:
            return AListFile(str(path), r_json["data"])

    def mkdir(self, path: str):
        """
        创建文件夹

        Args:
            path (str): 要创建的目录

        Returns:
            (bool): 是否成功


        """
        url = self._get_url("/api/fs/mkdir")
        data = json.dumps({"path": path})

        r = requests.post(url, data=data, headers=self.headers)
        self._is_bad_request(r, "创建失败")

        return True

    def upload(self, path: Union[str, AListFile], local: str):
        """
        上传文件

        Args:
            path (str, AListFile): 上传的路径
            local (str): 本地路径

        Returns:
            (bool): 是否成功


        """
        url = self._get_url("/api/fs/put")

        files = open(local, "rb").read()
        FilePath = quote(str(path))

        headers = self.headers.copy()
        headers["File-Path"] = FilePath
        headers["Content-Length"] = str(len(files))
        del headers["Content-Type"]

        r = requests.put(url, data=files, headers=headers)
        self._is_bad_request(r, "上传失败")

        return True

    def rename(self, src: Union[str, AListFolder, AListFile], dst: str):
        """
        重命名

        Args:
            src (str, AListFolder, AListFile): 原名
            dst (str): 要更改的名字

        Returns:
            (bool): 是否成功


        """
        url = self._get_url("/api/fs/rename")

        data = json.dumps({"path": str(src), "name": dst})

        r = requests.post(url, headers=self.headers, data=data)
        self._is_bad_request(r, "重命名失败")
        return True

    def remove(self, path: Union[str, AListFile]):
        url = self._get_url("/api/fs/remove")
        payload = json.dumps(
            {"names": [str(os.path.basename(str(path)))], "dir": str(os.path.dirname(str(path)))}
        )

        r = requests.post(url, data=payload, headers=self.headers)
        self._is_bad_request(r, "删除失败")
        return True

    def remove_folder(self, path: Union[str, AListFolder]):
        url = self._get_url("/api/fs/remove_empty_directory")
        data = json.dumps({"src_dir": str(path)})
        r = requests.post(url, data=data, headers=self.headers)
        self._is_bad_request(r, "删除失败")
        return True

    def copy(self, src: Union[str, AListFile], dst_dir: Union[str, AListFolder]):
        url = self._get_url("/api/fs/copy")
        data = json.dumps(
            {
                "src_dir": os.path.dirname(str(src)),
                "dst_dir": str(dst_dir),
                "names": [os.path.basename(str(src))],
            }
        )
        r = requests.post(url, data=data, headers=self.headers)
        self._is_bad_request(r, "复制失败")
        return True

    def move(
            self, src: Union[str, AListFile], dst_dir: Union[str, AListFolder]
    ):
        url = self._get_url("/api/fs/move")
        data = json.dumps(
            {
                "src_dir": os.path.dirname(str(src)),
                "dst_dir": str(dst_dir),
                "names": [os.path.basename(str(src))],
            }
        )
        r = requests.post(url, data=data, headers=self.headers)
        self._is_bad_request(r, "移动失败")
        return True

    def site_config(self):
        url = self._get_url("/api/public/settings")
        r = requests.get(url, headers=self.headers)
        self._is_bad_request(r, "AList配置信息获取失败")
        return self._parser_json(r.text).data


class AListAdmin(AList):
    def __init__(self, user, endpoint):
        super().__init__(endpoint)
        self.login(user)
        if self.user_info().id != 1:
            raise AuthenticationError("无权限")

    def list_meta(self, page=None, per_page=None):
        url = self._get_url("/api/admin/meta/list")
        prams = {"page": page, "per_page": per_page}
        r = requests.get(url, params=prams, headers=self.headers)
        self._is_bad_request(r, "无法列出元数据")
        return self._parser_json(r.text)
