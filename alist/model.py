import aiohttp


class AListFile:
    def __init__(self, path, init):
        self.path = path
        self.name = init["name"]
        self.provider = init["provider"]
        self.size = init["size"]
        self.modified = init["modified"]
        self.created = init["created"]
        self.url = init["raw_url"]
        self.sign = init["sign"]
        self.content = None
        self.position = 0  # 文件读取位置

    def __len__(self):
        return self.size

    def __str__(self):
        return self.path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass

    async def download(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as res:
                self.content = res.content

    async def read(self, n=-1):
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

    def seek(self, offset, whence=0):
        if whence == 0:
            self.position = offset
        elif whence == 1:
            self.position += offset
        elif whence == 2:
            self.position = max(0, self.size + offset)  # 防止移动到文件末尾之后

        # 确保位置不会超出文件大小
        self.position = min(self.position, self.size)

    async def save(self, path):
        if self.content is None:
            await self.download()

        with open(path, "wb") as f:
            f.write(self.content)

    def close(self):
        pass


class AListFolder:
    """
    AList文件夹
    """

    def __init__(self, path: str, init: dict):
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

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path
