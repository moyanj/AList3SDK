# 基础

## API类型

AList3SDK 支持两种类型的 API：异步 API 和同步 API。下面是对这两种 API 使用方式的详细说明。

### 异步API

异步 API 是 AList3SDK 的默认使用方式，通常适用于需要高性能和并发操作的场景。你可以使用 `AList` 类进行异步操作。(1.3.0以下不支持)

```python
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

### 同步API

在较老版本（1.3.3 及以下）中，默认是同步 API，适用于不需要并发执行的简单应用场景。在新版本中，你可以使用 `AListSync` 类进行同步操作。

```python
from alist import AListSync, AListUser

# 初始化 AList3SDK 客户端
user = AListUser("<your-user-name>", "<your-password>")  # 用户名和密码
client = AListSync("<your-server-url>")  # 服务器 URL

def main():
    # 登录
    client.login(user)
    
    # 列出指定目录下的文件
    res = client.list_dir("/test")
    
    # 打印目录内容
    for item in res:
        print(item)

# 运行同步任务
main()
```

### 提示
- **异步 API**：适合需要高并发操作的场景。通过 `async/await` 关键字，异步操作能够更高效地处理多个请求。
- **同步 API**：适用于简单的任务，当你不需要并发处理时可以使用同步版本，代码更加直观和易于理解，但是同步API没有类型注解。

### 版本差异
- **1.3.0 以下版本**：仅支持同步API
- **1.3.3 及以下版本**：同步 API 是默认的。如果你使用这些版本，默认导入的是 `AList`(同步API)，如果需要异步操作，则可能需要手动使用 `AListAsync`。
- **1.3.3 及以上版本**：默认使用异步 API (`AList`)，但仍保留了同步 API (`AListSync`) 以支持老版本的使用场景。

### 注意
1. 如果你使用的是 **1.3.3 或以上版本**，你可以直接使用 `AList` 进行异步操作。如果你使用的是 **1.3.3 以下版本**，你需要手动使用 `AListAsync` 来进行异步操作。
2. 异步操作需要 `asyncio` 运行事件循环，而同步操作不需要。


## 文件操作

要从 AList 服务操作文件，我们需要获取 [`AListFile`](../apis/model.md#alist.model.AListFile) 类的实例。可以通过以下方式实现：

```python
f: AListFile = ... 
await f.save("./1.txt")
```

那么，如何获取 `AListFile` 对象呢？我们可以使用 SDK 提供的 [`open`](../apis/main.md#alist.main.AList.open) 函数。

```python
...

async def main():
    # 获取指定文件的 AListFile 对象
    file = await client.open("/test.txt")
    
    # 将文件保存到本地
    await file.save("./test.txt")

# 执行异步任务
import asyncio
asyncio.run(main())
```

`AListFile` 类提供了三个基本的方法：`read`、`seek` 和 `close`，它允许你异步地读取文件内容，并在文件中进行定位操作。以下是一个简单的示例，展示如何使用这些方法：

```python
import asyncio

async def main():
    # 创建 AList 客户端实例
    client = AList("<your-server-url>")  # 替换为你的 AList 服务地址
    
    # 登录到 AList 服务
    await client.login("<your-username>", "<your-password>")  # 替换为你的用户名和密码
    
    # 获取指定路径的 AListFile 对象
    file = await client.open("/path/to/your/file.txt")
    
    # 读取整个文件内容
    content = await file.read()  # 读取文件所有内容
    print("File Content:", content)
    
    # 将文件指针移动到位置 1
    await file.seek(1)
    
    # 继续读取从位置 1 开始的内容
    content_from_pos = await file.read()  # 从当前位置继续读取文件
    print("Content from position:", content_from_pos)
    
    # 关闭文件
    await file.close()
    print("File closed")

# 执行异步任务
asyncio.run(main())
```

### 注意
- **字节流返回**：`read()` 返回的是字节串（`bytes`），如果你需要将其转换为字符串，可以在读取后进行解码，例如 `content.decode('utf-8')`。
- **关闭文件**：当你完成文件操作后，应该调用 `close()` 来释放资源(因为他会将整个文件下载到内存中)。

