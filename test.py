from alist import AList, AListUser
import asyncio


async def run():
    await alist.login(user)
    r = alist.list_dir("/test")
    print([item async for item in r])
    


asyncio.run(run())
