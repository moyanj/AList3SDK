import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Generic, Optional, Type, TypeVar, Union, get_type_hints

from .main import AList
from .model import AListFile, AListFolder

T = TypeVar("T")  # 异步类泛型


class Sync(Generic[T]):
    """
    同步代理基类
    """

    # 指定需要代理的异步类（子类必须重写）
    ASYNC_CLASS: Type[T] = None  # type: ignore

    def __init__(self, *args, async_obj: Optional[T] = None, **kwargs):
        if self.ASYNC_CLASS is None:
            raise NotImplementedError("Subclass must define ASYNC_CLASS")

        # 类型检查
        if async_obj is not None:
            if not isinstance(async_obj, self.ASYNC_CLASS):
                raise TypeError(
                    f"async_obj must be instance of {self.ASYNC_CLASS.__name__}"
                )
            self._async_obj = async_obj
        else:
            # 自动推导异步类构造参数类型
            type_hints = get_type_hints(self.ASYNC_CLASS.__init__)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in type_hints}
            self._async_obj = self.ASYNC_CLASS(*args, **filtered_kwargs)

    def __getattr__(self, name: str) -> Any:
        # 委托给异步对象
        attr = getattr(self._async_obj, name)

        # 自动包装协程方法
        if asyncio.iscoroutinefunction(attr):

            def sync_wrapper(*args, **kwargs):
                return self._run_async(attr(*args, **kwargs))

            return sync_wrapper

        # 处理异步属性（如 @property 修饰的协程）
        if isinstance(attr, property) and asyncio.iscoroutinefunction(attr.fget):
            return attr.fget(self._async_obj)

        return attr

    def _run_async(self, coroutine) -> Any:
        """执行异步代码（自动处理事件循环上下文）"""
        try:
            asyncio.get_running_loop()
            # 在已有事件循环中启动新线程执行
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coroutine)
                return future.result()
        except RuntimeError:
            # 直接运行新事件循环
            return asyncio.run(coroutine)

    def __enter__(self) -> "Sync[T]":
        """同步上下文管理器入口"""
        if hasattr(self._async_obj, "__aenter__"):
            self._run_async(self._async_obj.__aenter__())  # type: ignore
        return self

    def __exit__(self, *exc_info) -> None:
        """同步上下文管理器出口"""
        if hasattr(self._async_obj, "__aexit__"):
            self._run_async(self._async_obj.__aexit__(*exc_info))  # type: ignore

    def to_async(self) -> T:
        """返回异步对象"""
        return self._async_obj

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} of {self._async_obj!r}>"


class AListSync(Sync[AList]):
    """AList 的同步代理类"""

    ASYNC_CLASS = AList

    def open(
        self, path: str, password: str = ""
    ) -> Union["AListFileSync", AListFolder]:
        """打开文件或文件夹"""
        obj = self.__getattr__("open")(path, password)
        if isinstance(obj, AListFile):
            return AListFileSync(async_obj=obj)
        else:
            return obj


class AListFileSync(Sync[AListFile]):
    """AListFile 的同步代理类"""

    ASYNC_CLASS = AListFile
