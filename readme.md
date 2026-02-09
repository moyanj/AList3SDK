# AList3SDK
![PyPI - Downloads](https://img.shields.io/pypi/dw/alist3)
![PyPI - Version](https://img.shields.io/pypi/v/alist3)
![GitHub Repo stars](https://img.shields.io/github/stars/moyanj/AList3SDK)
![GitHub last commit](https://img.shields.io/github/last-commit/moyanj/AList3SDK)
![GitHub License](https://img.shields.io/github/license/moyanj/AList3SDK)
[![Documentation Status](https://readthedocs.org/projects/alist3sdk/badge/?version=latest)](https://alist3sdk.readthedocs.io/zh-cn/latest/?badge=latest)

[!WARNING]
本SDK目前遵循的API文档为[OpenList](https://github.com/OpenListTeam/OpenList)，暂未对可能的其他分支进行适配

AList3SDK 是一个高性能的 Python SDK，用于与 OpenList/AList 服务轻松交互 🚀。它支持异步和同步 API ⚡，并提供完善的类型注解 📝，让开发更高效！

## 安装

您可以使用 pip 安装 AList3SDK：

```bash
pip install alist3
```

## 快速开始

使用 AList3SDK，您可以轻松地与 OpenList/AList 服务进行交互。以下是一个快速示例：

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
    res = client.list_dir("/test")
    
    # 打印目录内容
    async for item in res:
        print(item)

# 运行异步任务
asyncio.run(main())

```

## 示例代码

有关示例代码，请参阅我们的 [文档📄](https://alist3sdk.readthedocs.io/examples)。

## API 文档
请参阅我们的 [文档📄](https://alist3sdk.readthedocs.io)。


## 常见问题解答

Q: 如果遇到身份验证问题应该怎么办？

A: 请确保您的 OpenList 地址和账号密码正确，并具有足够的权限。

## 贡献指南

我们欢迎社区贡献者为改进和完善 AList3SDK 做出贡献。如果发现任何 bug 或有新的功能建议，请提交 issue 或 PR。

## 版本历史

- 1.0.0 (2024-02-16): 初始版本发布。
- 1.1 (2024-05-10) : 改了一大堆东西
- 1.1.1 (2024-05-20)： 修改文档与修复bug
- 1.1.2 (2024-07-04)：适配部分admin操作,添加一多线程下载器
- 1.1.3 (2024-07-05): 更新文档，增加用户类加载
- 1.1.4 (2024-08-11): 修复已知问题，优化用户体验
- 1.2.0 (2024-11-04): 修改大量命名风格
- 1.3.0 (2024-11-09): 增加异步支持
- 1.3.1 (2024-11-09): 修复已知问题，优化用户体验
- 1.3.2 (2024-11-15): 添加类型注解
- 1.3.3 (2024-11-15): 切换默认api至异步
- 1.3.4 (2024-12-29): 修复已知问题，支持用户管理
- 1.3.5 (2025-01-22): 修复AListFile自动下载问题
- 1.3.6 (2025-03-07): 增加对上传字节数据和文件指针的支持
- 1.3.7 (2025-03-29): 修复issue:[#6](https://github.com/moyanj/AList3SDK/issues/6)
- 1.3.8 (2025-05-01): 添加网络代理设置:[#8](https://github.com/moyanj/AList3SDK/issues/8)
- 1.4.0 (2025-07-20): 适配更多api
- 1.4.1 (2025-07-20): 修复类型注释并清理代码
- 1.4.2 (2025-11-19): 修复部分参数传递问题，支持登出
- 1.5.0 (2026-02-09): 完善 CLI 工具，增强同步代理对生成器的支持，优化文档与测试
