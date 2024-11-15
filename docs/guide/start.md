# 开始

## Python 版本

我们建议使用最新版本的 Python。AList3SDK 支持 Python 3.9 及更高版本。

## 安装

您可以使用 pip 安装 AList3SDK：

```bash
pip install alist3
```

## 快速开始

这是一个最简单的使用异步api的示例：
```python
import asyncio
from alist import AList, AListUser

# 初始化 AList3SDK 客户端
user = AListUser("<your-user-name>", "<your-password>")  # 用户名和密码
client = AList("<your-server-url>")  # 服务器 URL

async def main():
    # 登录
    await client.login(user)
    
    # 列出指定目录下的文件
    res = await client.list_dir("/test")
    
    # 打印目录内容
    async for item in res:
        print(item)

# 运行异步任务
asyncio.run(main())

```