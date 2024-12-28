import aiohttp
from typing import Mapping, Union, Any


class AListFile:
    """
    AList文件

    兼容文件对象

    Attributes:
        path (str):文件路径
        name (str):文件名
        size (int):文件大小
        provider (int):存储类型
        modified (str):修改时间
        created (str):创建时间
        url (str):文件下载URL
        sign (str):签名
        content (bytes):文件内容
        position (int):文件读取位置
        raw (dict):原始返回信息
    """

    path: str
    name: str
    provider: int
    size: int
    modified: str
    created: str
    url: str
    sign: int
    content: bytes
    position: int
    raw: Mapping[str, Union[str, int]]

    def __init__(self, path: str, init: Mapping[str, Any]):
        """
        初始化

        Args:
            path (str):文件路径
            init (dict):初始化字典

        """
        self.path = path
        self.name = init["name"]
        self.provider = init["provider"]
        self.size = init["size"]
        self.modified = init["modified"]
        self.created = init["created"]
        self.url = init["raw_url"]
        self.sign = init["sign"]
        self.content = b""
        self.position = 0  # 文件读取位置
        self.raw = init

    def __len__(self):
        return self.size

    def __str__(self):
        return self.path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass

    async def download(self):
        """
        下载文件至内存
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as res:
                self.content = await res.read()

    async def read(self, n: int = -1) -> bytes:
        """
        读文件

        Args:
            n (int):读取的字节大小
        """
        if self.content is None:
            await self.download()

        if n == -1:
            data = self.content[self.position :]
            self.position = self.size  # 移动到文件末尾
            return data
        else:
            end_position = min(self.position + n, self.size)
            data = self.content[self.position : end_position]
            self.position = end_position
            return data

    def seek(self, offset: int, whence: int = 0):
        """
        设置文件指针位置

        Args:
            offset (int):偏移量
            whence (int):基准
        """
        if whence == 0:
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = max(0, self.size + offset)  # 防止移动到文件末尾之后

        # 确保位置不会超出文件大小
        self.position = min(self.position, self.size)

    async def save(self, path: str):
        """
        保存文件至本地

        Args:
            path (str):路径
        """
        if self.content is None:
            await self.download()

        with open(path, "wb") as f:
            f.write(self.content)

    def close(self):
        self.content = b""


class AListFolder:
    """
    AList文件夹

    Attributes:
        path (str):文件路径
        size (int):文件大小
        provider (int):存储类型
        modified (str):修改时间
        created (str):创建时间
        raw (dict):原始返回信息
    """

    path: str
    provider: int
    size: int
    modified: str
    created: str
    raw: Mapping[str, Union[str, int]]

    def __init__(self, path: str, init: Mapping[str, Any]):
        """
        初始化

        Args:
            path (str):文件夹路径
            init (dict):初始化字典
        """
        self.path = path
        self.provider = init["provider"]
        self.size = init["size"]
        self.modified = init["modified"]
        self.created = init["created"]
        self.raw = init

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path
