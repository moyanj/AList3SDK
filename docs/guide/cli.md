# 命令行工具 (CLI)

AList3SDK 附带了一个强大的命令行工具 `alist3`，可以帮助您在终端直接管理 AList 服务器。

## 安装 CLI

CLI 是作为一个可选依赖提供的。要使用 CLI，您在安装时需要包含 `cli` 选项：

```bash
pip install "alist3[cli]"
```

## 身份验证管理 (auth)

在使用 CLI 之前，您需要添加一个用户。

### 添加用户

```bash
alist3 auth add "username:password@http://your-alist-server.com"
```

选项：
- `--default`, `-d`: 将此用户设置为默认用户。
- `--tag`, `-t`: 为用户添加标签。
- `--cover`, `-c`: 覆盖已存在的同名用户。

### 列出用户

```bash
alist3 auth ls
```

### 移除用户

```bash
alist3 auth rm <username>
```

## 文件操作

大部分文件操作命令支持 `--user` 或 `-u` 选项来指定非默认用户。

### 列出文件 (ls)

```bash
alist3 ls /path/to/dir
```

### 创建目录 (mkdir)

```bash
alist3 mkdir /path/to/new_dir
```

### 删除文件或目录 (rm)

```bash
alist3 rm /path/to/file
# 删除目录需加 -d
alist3 rm /path/to/dir -d
```

### 复制与移动 (cp/mv)

```bash
alist3 cp /src/file /dst/dir/
alist3 mv /src/file /dst/new_name
```

### 上传与下载 (upload/download)

上传：
```bash
alist3 upload ./local_file.txt /remote/path/
```

下载：
```bash
alist3 download /remote/file.txt ./local_file.txt
```

## 个人信息

查看当前登录用户的信息：
```bash
alist3 me
```
