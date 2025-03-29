import pytest
import alist
from aioresponses import aioresponses


def test_AListUser():
    user = alist.AListUser("admin", "123456")
    assert (
        user.pwd == "e166b45e39301021e897e3a6713e11171893217ad2901cf28c2c09c8d54e55d9"
    )
    assert user.rawpwd == "123456"


def test_error_endpoint():
    with pytest.raises(ValueError):
        alist.AList("111")


def test_is_bad_request():
    alis = alist.AList("http")
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
async def test_user_info():
    with aioresponses() as m:
        m.get(
            "http://test/api/me",
            payload={
                "code": 200,
                "message": "success",
                "data": {
                    "id": 1,
                    "username": "admin",
                    "password": "",
                    "base_path": "/",
                    "role": 2,
                    "disabled": False,
                    "permission": 0,
                    "sso_id": "",
                    "otp": True,
                },
            },
        )
        alis = alist.AList("http://test")
        resp = await alis.user_info()
        assert resp.id == 1
        assert resp.username == "admin"
        assert resp.password == ""
        assert resp.base_path == "/"
        assert resp.role == 2
        assert resp.disabled == False
        assert resp.permission == 0
        assert resp.sso_id == ""
        assert resp.otp == True
