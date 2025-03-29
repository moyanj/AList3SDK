import pytest
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
