import asyncio
from .main import AList, AListAdmin
from .model import AListFile


class AListSync:
    """
    AList的同步代理类
    """

    def __init__(self, *args, **kwargs):
        self._async_obj = AList(*args, **kwargs)

    def __getattr__(self, name):
        # 获取异步对象的属性（方法）
        func = getattr(self._async_obj, name)

        # 如果该方法是异步的（即协程函数），我们需要创建同步包装
        if asyncio.iscoroutinefunction(func):

            def sync_func(*args, **kwargs):
                # 获取当前事件循环
                loop = asyncio.get_event_loop()

                # 如果当前没有事件循环在运行，手动创建并运行一个新的事件循环
                if loop.is_running():
                    # 在当前事件循环中运行异步函数
                    return loop.run_until_complete(func(*args, **kwargs))
                else:
                    # 如果没有活动的事件循环，使用 asyncio.run() 来启动新的事件循环
                    return asyncio.run(func(*args, **kwargs))

            return sync_func
        else:
            # 如果方法不是异步的，直接返回它
            return func


class AListAdminSync(AListSync):
    """
    AListAdmin的同步代理类
    """

    def __init__(self, *args, **kwargs):
        self._async_obj = AListAdmin(*args, **kwargs)


class AListFileSync(AListSync):
    """
    AListFile的同步代理类
    """

    def __init__(self, *args, **kwargs):
        self._async_obj = AListFile(*args, **kwargs)
