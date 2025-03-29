import alist
from aioresponses import aioresponses


def test_async2sync_AList():
    al = alist.AList("http").to_sync()
    assert isinstance(al, alist.sync.AListSync)


def test_async2sync_AListFile():
    al = alist.AListFile("", {}).to_sync()
    assert isinstance(al, alist.sync.AListFileSync)


def test_sync2async_AList():
    al = alist.sync.AListSync("http").to_async()
    assert isinstance(al, alist.AList)


def test_sync2async_AListFile():
    al = alist.sync.AListFileSync("", {}).to_async()
    assert isinstance(al, alist.AListFile)


def test_sync_open():
    with aioresponses() as m:
        m.post(
            "http://1/api/fs/get",
            status=200,
            payload={
                "code": 200,
                "message": "success",
                "data": {
                    "name": "Alist V3.md",
                    "size": 2618,
                    "is_dir": False,
                    "modified": "2024-05-17T16:05:36.4651534+08:00",
                    "created": "2024-05-17T16:05:29.2001008+08:00",
                    "sign": "",
                    "thumb": "",
                    "type": 4,
                    "hashinfo": "null",
                    "hash_info": None,
                    "raw_url": "http://127.0.0.1:5244/p/local/Alist%20V3.md",
                    "readme": "",
                    "header": "",
                    "provider": "Local",
                    "related": None,
                },
            },
        )
        al = alist.sync.AListSync("http://1/")
        r = al.open("121")
        assert isinstance(r, alist.AListFileSync)
