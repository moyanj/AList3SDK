import os
import pickle
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from alist.cli.utils import get_client


@pytest.mark.asyncio
async def test_get_client_no_init():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(RuntimeError, match="CLI 未初始化"):
            await get_client()


@pytest.mark.asyncio
async def test_get_client_default_user():
    # Mocking necessary parts
    with (
        patch("os.path.exists", return_value=True),
        patch("os.listdir", return_value=["admin.__default"]),
        patch("builtins.open", MagicMock()),
        patch(
            "pickle.load",
            return_value={"endpoint": "http://test", "user": b"mock_user_bytes"},
        ),
        patch("alist.cli.utils.AListUser.loads") as mock_loads,
        patch("alist.cli.utils.AList") as mock_alist,
    ):
        mock_user = MagicMock()
        mock_user.un = "admin"
        mock_user.pwd = "hashed_pwd"
        mock_loads.return_value = mock_user

        mock_client = MagicMock()
        mock_client.login = AsyncMock(return_value=True)
        mock_alist.return_value = mock_client

        client, path = await get_client()

        assert client == mock_client
        assert path == "/"
        mock_client.login.assert_called_once()
