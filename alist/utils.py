from typing import Union, Any
import pickle
import base64
import hashlib
import warnings

from . import error


class ToClass:
    """
    字典转class

    Attributes:
        _conf_Dict (dict):原始字典
    """

    def __init__(self, conf: dict):
        self._conf_Dict = conf
        self.__name__ = "<Standard Dictionary>"
        self._update()

    def __getattr__(self, name):
        if name in self._conf_Dict:
            return self._conf_Dict[name]
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def _update(self, conf: Union[dict, None] = None):
        """
        更新字典内容

        Args:
            conf (dict):要更新的字典
        """
        if conf:
            self._conf_Dict = conf
        # 更新字典
        for k, v in self._conf_Dict.items():
            if isinstance(v, dict):
                setattr(self, k, ToClass(v))
            elif isinstance(v, list):
                setattr(
                    self,
                    k,
                    [ToClass(item) if isinstance(item, dict) else item for item in v],
                )
            else:
                setattr(self, k, v)

    def __str__(self):
        return str(self._conf_Dict)

    def __repr__(self):
        return str(self._conf_Dict)


class AListUser:
    """
    AList用户类
    """

    un: str
    pwd: str
    rawpwd: str

    def __init__(self, username: str, rawpwd: str = "", pwd=None):
        """
        初始化

        Args:
            username (str):AList的用户名
            rawpwd (str):AList的密码(明文)
            pwd (str):AList的密码(密文)

        """
        self.un = username

        if pwd:
            self.pwd = pwd
            self.rawpwd = pwd
        else:
            self.rawpwd = rawpwd
            self.pwd = ""
            sha = hashlib.sha256()
            sha.update(self.rawpwd.encode())
            sha.update(b"-https://github.com/alist-org/alist")
            self.pwd = sha.hexdigest()

    def dump(self, fp: Any, rawpwd: bool = False):
        """
        保存

        Args:
            fp (文件对象):将要保存的文件
            rawpwd (bool):保存明文密码

        """

        data = {
            "username": base64.b64encode(self.un.encode()),
            "pwd": base64.b64encode(self.pwd.encode()),
        }
        if rawpwd and self.rawpwd:
            warnings.warn(
                "Saving plaintext passwords to files is not secure",
                error.SecurityWarning,
            )
            data["raw"] = base64.b64encode(self.rawpwd.encode())

        pickle.dump(data, fp)

    def dumps(self, rawpwd: bool = False) -> bytes:
        """
        保存(返回二进制)

        Args:
            rawpwd (bool):保存明文密码

        """

        data = {
            "username": base64.b64encode(self.un.encode()),
            "pwd": base64.b64encode(self.pwd.encode()),
        }
        if rawpwd and self.rawpwd:
            warnings.warn(
                "Saving plaintext passwords to files is not secure",
                error.SecurityWarning,
            )
            data["raw"] = base64.b64encode(self.rawpwd.encode())

        return pickle.dumps(data)

    @classmethod
    def load(cls, fp: Any) -> "AListUser":
        """
        加载

        Args:
            fp (文件对象):将要加载的文件

        """

        data = pickle.load(fp)
        un = base64.b64decode(data["username"]).decode()
        pwd = base64.b64decode(data["pwd"]).decode()
        raw = None
        if "raw" in data:
            raw = base64.b64decode(data["raw"]).decode()
        return cls(un, pwd, raw)

    @classmethod
    def loads(cls, byte) -> "AListUser":
        """
        加载(从字节)

        Args:
            byte (bytes): 将要加载的字节

        """

        data = pickle.loads(byte)
        un = base64.b64decode(data["username"]).decode()
        pwd = base64.b64decode(data["pwd"]).decode()
        raw = None
        if "raw" in data:
            raw = base64.b64decode(data["raw"]).decode()
        return AListUser(un, pwd, raw)

    def __str__(self):
        return f"AListUser({self.un})"

    def __repr__(self):
        return self.__str__()


def clear_dict(dic):
    return {k: v for k, v in dic.items() if v is not None}
