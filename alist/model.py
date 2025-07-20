from typing import Any, AsyncGenerator, Mapping, Optional, Union

import aiofiles
import aiohttp
from aiofiles import tempfile


class AListFile:
    """
    AList文件（兼容异步文件对象）

    Attributes:
        path (str): 文件路径
        name (str): 文件名
        size (int): 文件大小
        provider (int): 存储类型
        modified (str): 修改时间
        created (str): 创建时间
        url (str): 文件下载URL
        sign (str): 签名
        raw (dict): 原始返回信息
    """

    def __init__(self, path: str, init: Mapping[str, Any]):
        # 初始化元数据
        self.path = path
        self.name = init.get("name", "")
        self.provider = init.get("provider", 0)
        self._size = init.get("size", 0)  # 私有变量用于跟踪实际大小
        self.modified = init.get("modified", "")
        self.created = init.get("created", "")
        self.url = init.get("raw_url", "")
        self.sign = str(init.get("sign", ""))
        self.raw = init

        # 文件操作相关
        self._file = None
        self._closed = False

    def __len__(self) -> int:
        return self._size

    def __repr__(self) -> str:
        return f"<AListFile {self.path}>"

    def __str__(self) -> str:
        return self.path

    async def __aenter__(self):
        if self._closed:
            raise ValueError("Cannot reopen closed file")
        self._file = await tempfile.SpooledTemporaryFile(
            max_size=10 * 1024 * 1024
        ).__aenter__()
        await self.download()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        """关闭文件并释放资源"""
        if self._file and not self._closed:
            await self._file.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        """检查文件是否已关闭"""
        return self._closed

    async def tell(self) -> int:
        """获取当前文件指针位置"""
        self._check_open()
        return await self._file.tell()  # type: ignore

    async def seek(self, offset: int, whence: int = 0) -> int:
        """
        移动文件指针
        :param offset: 偏移量
        :param whence: 0=文件头, 1=当前位置, 2=文件尾
        :return: 新的绝对位置
        """
        self._check_open()
        new_pos = await self._file.seek(offset, whence)  # type: ignore
        # 更新内部_size跟踪（如果通过truncate改变大小）
        if whence == 2:
            self._size = max(0, self._size + offset)
        return new_pos

    async def read(self, n: int = -1) -> bytes:
        """读取指定字节数"""
        self._check_open()
        return await self._file.read(n)  # type: ignore

    async def readline(self) -> bytes:
        """读取单行（直到换行符）"""
        self._check_open()
        return await self._file.readline()  # type: ignore

    async def readlines(self) -> list[bytes]:
        """读取所有行"""
        self._check_open()
        return await self._file.readlines()  # type: ignore

    async def truncate(self, size: Optional[int] = None) -> int:
        """截断/扩展文件到指定大小"""
        self._check_open()
        new_size = await self._file.truncate(size)  # type: ignore
        self._size = new_size
        return new_size

    async def flush(self) -> None:
        """强制刷写缓冲区到磁盘"""
        self._check_open()
        await self._file.flush()  # type: ignore

    def fileno(self) -> int:
        """获取文件描述符（同步方法）"""
        self._check_open()
        return self._file.fileno()  # type: ignore

    @property
    def mode(self) -> str:
        """获取文件打开模式"""
        return "r+b"  # SpooledTemporaryFile固定模式

    @property
    def size(self) -> int:
        """获取当前文件大小（动态计算）"""
        return self._size

    async def download(self, chunk_size: int = 1024 * 1024) -> None:
        """流式下载文件到临时文件"""
        self._check_open()

        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                response.raise_for_status()

                # 清空已有内容
                await self.seek(0)
                await self.truncate(0)  # type: ignore

                # 流式写入
                async for chunk in response.content.iter_chunked(chunk_size):
                    await self._file.write(chunk)  # type: ignore

                # 重置指针
                await self.seek(0)
                self._size = await self._get_actual_size()

    async def save(self, path: str, chunk_size: int = 1024 * 1024) -> None:
        """异步保存文件到本地"""
        self._check_open()
        await self.seek(0)  # 确保从头读取

        async with aiofiles.open(path, "wb") as f:
            while True:
                chunk = await self.read(chunk_size)
                if not chunk:
                    break
                await f.write(chunk)

        await self.seek(0)  # 重置指针

    async def iter_chunks(self, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """异步迭代文件内容"""
        self._check_open()
        await self.seek(0)

        while True:
            chunk = await self.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def _check_open(self) -> None:
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if self._file is None:
            raise ValueError("File not opened in async context")

    async def _get_actual_size(self) -> int:
        """获取实际文件大小（兼容内存和磁盘模式）"""
        current_pos = await self.tell()
        await self.seek(0, 2)  # 移动到文件尾
        size = await self.tell()
        await self.seek(current_pos)  # 恢复原位置
        return size

    def to_sync(self):
        """转换为同步文件对象"""
        from alist.sync import AListFileSync

        return AListFileSync(async_obj=self)


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
