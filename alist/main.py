# pylint:disable=W0707
from hashlib import sha256 as _sha256
import requests as _req
from urllib.parse import urljoin as _urljoin
import json as _json
from sys import version_info as _version_info
from platform import platform as _pf
from os.path import join as _pathjoin
from urllib.parse import quote as _quote
from typing import Union as _Union
from os.path import dirname as _dirname
from os.path import basename as _basename

from . import Error, file, folder


class AList:
    def __init__(self, endpoint: str):
        """
        AList的SDK，此为主类。

        Args:
            endpoint (str):AList地址
        """
        if "http" not in endpoint:
            raise ValueError(endpoint + "不是有效的uri")

        self.endpoint = endpoint
        self.user = ""

        # 构建UA
        ver = [
            str(_version_info.major),
            str(_version_info.minor),
            str(_version_info.micro),
        ]
        ver = ".".join(ver)
        pf = _pf().split("-")
        self.headers = {
            "User-Agent": f"AListSDK/1.0 (Python{ver};{pf[3]}) {pf[0]}/{pf[1]}",
            "Content-Type": "application/json",
            "Authorization": "",
        }

    def _isBadRequest(self, r, msg):
        # 是否为不好的请求
        try:
            j = _json.loads(r.text)
        except _json.JSONDecodeError:
            raise ValueError("服务器返回数据不是JSON数据")
        if j["code"] != 200:
            raise Error.ServerError(msg + ":" + j["message"])

    def _getURL(self, path):
        # 获取api端点
        return _urljoin(self.endpoint, path)

    def login(self, username: str, password: str, otp_code: str = None):
        """
        登录

        Args:
            username (str): AList的用户名
            password (str): AList的密码
            otp_code (str): OTP

        Returns:
            (bool): 是否成功


        """

        URL = self._getURL("/api/auth/login/hash")

        # 对密码进行sha256摘要
        sha = _sha256()
        sha.update(password.encode())
        sha.update(b"-https://github.com/alist-org/alist")
        sha256Password = sha.hexdigest()
        # 构建json数据
        data = {"username": username, "password": sha256Password, "otp_code": otp_code}
        data = _json.dumps(data)

        r = _req.post(URL, headers=self.headers, data=data)
        # 处理返回数据
        self._isBadRequest(r, "账号或密码错误")
        # 保存
        self.user = _json.loads(r.text)["data"]["token"]
        self.headers["Authorization"] = self.user
        return True

    def userInfo(self):
        """
        获取当前登录的用户的信息

        Returns:
            (dict):一个字典，包含了当前用户的信息。

        """

        URL = self._getURL("/api/me")
        r = _req.get(URL, headers=self.headers)
        return r.json()["data"]

    def listdir(
        self,
        path: _Union[str, folder.AListFolder],
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

        URL = self._getURL("/api/fs/list")

        data = _json.dumps(
            {
                "path": str(path),
                "password": password,
                "page": page,
                "per_page": per_page,
                "refresh": refresh,
            }
        )
        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, "上传失败")

        for item in _json.loads(r.text)["data"]["content"]:
            i = {"path": _pathjoin(str(path), item["name"]), "is_dir": item["is_dir"]}
            yield i

    def open(
        self, path: _Union[str, folder.AListFolder, file.AListFile], password: str = ""
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

        URL = self._getURL("/api/fs/get")
        
        data = _json.dumps({"path": str(path), "password": password})
        r = _req.post(URL, headers=self.headers, data=data)
        
        r_json = _json.loads(r.text)
        if r_json["data"]["is_dir"]:
            return folder.AListFolder(str(path), r_json["data"])
        else:
            return file.AListFile(str(path), r_json["data"])

    def mkdir(self, path:str):
        """
        创建文件夹

        Args:
            path (str): 要创建的目录
            
        Returns:
            (bool): 是否成功


        """
        URL = self._getURL("/api/fs/mkdir")
        data = _json.dumps({"path": path})

        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, "创建失败")

        return True

    def upload(self, path: _Union[str, file.AListFile], local: str):
        """
        上传文件

        Args:
            path (str, AListFile): 上传的路径
            locel (str): 本地路径
            
        Returns:
            (bool): 是否成功


        """
        URL = self._getURL("/api/fs/put")

        files = open(local, "rb").read()
        FilePath = _quote(str(path))

        headers = self.headers.copy()
        headers["File-Path"] = FilePath
        headers["Content-Length"] = str(len(files))
        del headers["Content-Type"]

        r = _req.put(URL, data=files, headers=headers)
        self._isBadRequest(r, "上传失败")
        
        return True

    def rename(self, src: _Union[str, folder.AListFolder, file.AListFile], dst: str):
        """
        重命名

        Args:
            src (str, AListFolder, AListFile): 原名
            dst (str): 要更改的名字
            
        Returns:
            (bool): 是否成功


        """
        URL = self._getURL("/api/fs/rename")

        data = _json.dumps({"path": str(src), "name": dst})

        r = _req.post(URL, headers=self.headers, data=data)
        self._isBadRequest(r, "重命名失败")
        return True

    def remove(self, path: _Union[str, file.AListFile]):
        URL = self._getURL("/api/fs/remove")
        payload = _json.dumps(
            {"names": [str(_basename(str(path)))], "dir": str(_dirname(str(path)))}
        )

        r = _req.post(URL, data=payload, headers=self.headers)
        self._isBadRequest(r, "删除失败")
        return True

    def removeFolder(self, path: _Union[str, folder.AListFolder]):
        URL = self._getURL("/api/fs/remove_empty_directory")
        data = _json.dumps({"src_dir": str(path)})
        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, "删除失败")
        return True

    def copy(
        self, src: _Union[str, file.AListFile], dstDir: _Union[str, folder.AListFolder]
    ):
        URL = self._getURL("/api/fs/copy")
        data = _json.dumps(
            {
                "src_dir": _dirname(str(src)),
                "dst_dir": str(dstDir),
                "names": [_basename(str(src))],
            }
        )
        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, "复制失败")
        return True

    def move(
        self, src: _Union[str, file.AListFile], dstDir: _Union[str, folder.AListFolder]
    ):
        URL = self._getURL("/api/fs/move")
        data = _json.dumps(
            {
                "src_dir": _dirname(str(src)),
                "dst_dir": str(dstDir),
                "names": [_basename(str(src))],
            }
        )
        r = _req.post(URL, data=data, headers=self.headers)
        self._isBadRequest(r, "移动失败")
        return True

    def GetConfig(self):
        url = self._getURL('/api/public/settings')
        r = _req.get(url, headers=self.headers)
        self._isBadRequest(r,'AList配置信息获取失败')
        return r.json['data']
