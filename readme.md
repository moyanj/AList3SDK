# AList3SDK
## 这个是开发分支，正在实现异步
[!WARNING]
本SDK已发生重大更新，完全不兼容上一个版本(v1.1.4)

AList3SDK 是用于与 AList 服务集成和交互的 Python SDK。它旨在简化开发人员与 AList 服务进行集成和交互的过程。

## 安装

您可以使用 pip 安装 AList3SDK：

```bash
pip install alist3
```

## 快速开始

使用 AList3SDK，您可以轻松地与 AList 服务进行交互。以下是一个快速示例，演示如何使用 AList3SDK 查询 AList 服务：

```python
from alist import AList, AListUser

# 初始化 AList3SDK 客户端
user = AListUser("<your-user-name>","<your-password>")
alist = AList("<your-server-url>")

# 登录 AList 服务
client.login(user)
response = client.list_dir("/")
# 处理响应
print('AList 服务查询结果:', list(response))
```

## 示例代码

有关示例代码，请参阅我们的 [文档📄](https://alist3sdk.readthedocs.io/examples)。

## API 文档
请参阅我们的 [文档📄](https://alist3sdk.readthedocs.io)。


## 常见问题解答

Q: 如果遇到身份验证问题应该怎么办？

A: 请确保您的 AList地址和账号密码正确，并具有足够的权限。

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
