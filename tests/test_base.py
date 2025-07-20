import pytest
from aioresponses import aioresponses

import alist


def test_error_endpoint():
    with pytest.raises(ValueError):
        alist.AList("111")


def test_is_bad_request():
    alis = alist.AList("http://")
    with pytest.raises(alist.error.ServerError):
        alis._isBadRequest({"code": 400, "message": "test"}, "test")


@pytest.mark.asyncio
async def test_request():
    with aioresponses() as m:
        m.get("http://test/1", payload={"code": 200, "message": "test"})
        alis = alist.AList("http://test")
        resp = await alis._request("GET", "/1")
        assert resp["code"] == 200
        assert resp["message"] == "test"


@pytest.mark.asyncio
async def test_ping():
    with aioresponses() as m:
        m.get("http://test/ping", body="pong")
        alis = alist.AList("http://test")
        resp = await alis.test()
        assert resp


@pytest.mark.asyncio
async def test_login():
    with aioresponses() as m:
        m.post(
            "http://test/api/auth/login/hash",
            payload={"code": 200, "message": "success", "data": {"token": "abcd"}},
        )
        alis = alist.AList("http://test")
        resp = await alis.login(alist.AListUser("admin", "123456"))
        assert resp
        assert alis.token == "abcd"
        assert alis.headers["Authorization"] == "abcd"


@pytest.mark.asyncio
async def test_list_dir():
    with aioresponses() as m:
        m.post(
            "http://test/api/fs/list",
            payload={
                "code": 200,
                "message": "success",
                "data": {
                    "content": [
                        {
                            "name": "Alist V3.md",
                            "is_dir": False,
                        }
                    ]
                },
            },
        )
        alis = alist.AList("http://test")
        async for i in alis.list_dir("/"):
            assert i.path == "/Alist V3.md"
            assert i.is_dir is False


@pytest.mark.asyncio
async def test_list_dir_folder():
    with aioresponses() as m:
        m.post(
            "http://test/api/fs/list",
            payload={
                "code": 200,
                "message": "success",
                "data": {
                    "content": [
                        {
                            "name": "Alist V3.md",
                            "is_dir": False,
                        }
                    ]
                },
            },
        )
        alis = alist.AList("http://test")
        async for i in alis.list_dir(
            alist.AListFolder(
                "/",
                {
                    "name": "Alist V3.md",
                    "size": 2618,
                    "modified": "2024-05-17T16:05:36.4651534+08:00",
                    "created": "2024-05-17T16:05:29.2001008+08:00",
                    "provider": "Local",
                },
            )
        ):
            assert i.path == "/Alist V3.md"
            assert i.is_dir is False
