import alist
import pytest
from aioresponses import aioresponses

alist_file_init = {
    "name": "Alist V3.md",
    "size": 11,
    "is_dir": None,
    "modified": "2024-05-17T16:05:36.4651534+08:00",
    "created": "2024-05-17T16:05:29.2001008+08:00",
    "sign": "",
    "thumb": "",
    "type": 4,
    "hashinfo": "null",
    "hash_info": None,
    "raw_url": "http://1/",
    "readme": "",
    "header": "",
    "provider": "Local",
    "related": None,
}


def test_AListUser():
    user = alist.AListUser("admin", "123456")
    assert (
        user.pwd == "e166b45e39301021e897e3a6713e11171893217ad2901cf28c2c09c8d54e55d9"
    )
    assert user.rawpwd == "123456"


def test_ToClass():
    data = {
        "a": 1,
        "b": 2,
        "c": {
            "a": 1,
        },
        "d": [
            "1",
            2,
            {
                "a": 1,
                "b": 2,
            },
        ],
    }
    tc = alist.utils.ToClass(data)
    assert tc.a == 1
    assert tc.b == 2
    assert tc.c.a == 1
    assert tc.d[0] == "1"
    assert tc.d[1] == 2
    assert tc.d[2].a == 1
    assert tc.d[2].b == 2

    with pytest.raises(AttributeError):
        tc.d[2].c


async def test_AListFile_download():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World",
        )
        async with alist.AListFile("/", alist_file_init) as f:
            assert await f.read() == b"Hello World"


async def test_AListFile_read():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World",
        )
        async with alist.AListFile("/", alist_file_init) as f:

            # 读取一个字节
            d = await f.read(1)
            assert d == b"H"

            # 再次读取两个字节
            d = await f.read(2)
            assert d == b"el"

            # 读取剩下的
            d = await f.read()
            assert d == b"lo World"
            # 读取全部
            await f.seek(0)
            assert await f.read() == b"Hello World"


async def test_AListFile_readline():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World\nHello World",
        )
        async with alist.AListFile("/", alist_file_init) as f:
            d = await f.readline()
            assert d == b"Hello World\n"


async def test_AListFile_readlines():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World\nHello World",
        )


async def test_AListFile_seek():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World",
        )
        async with alist.AListFile("/", alist_file_init) as f:
            # await f.download()
            # 从第五个字符开始读取
            await f.seek(5)
            assert await f.read() == b" World"
            # 剩下的
            assert await f.read() == b""
            assert await f.read(1) == b""
            assert await f.readline() == b""
            assert await f.readlines() == []
            assert await f.tell() == 11
            assert await f.seek(0) == 0
            assert await f.tell() == 0
            assert await f.read() == b"Hello World"
            assert await f.read() == b""
            assert await f.readline() == b""
            assert await f.readlines() == []
            assert await f.tell() == 11
            assert await f.seek(0) == 0
            assert await f.tell() == 0


def test_AListFile_magic():
    with aioresponses() as m:
        m.get(
            "http://1/",
            body=b"Hello World",
        )
        f = alist.AListFile("/", alist_file_init)
        assert len(f) == 11
        assert str(f) == "/"
