import asyncio, aiohttp
async def main():
    while True:
        try:
            conn = aiohttp.UnixConnector(path="/run/kvmd/kvmd.sock")
            async with aiohttp.ClientSession(connector=conn) as s:
                async with s.ws_connect("http://localhost/ws?stream=1") as ws:
                    async for m in ws: pass
        except Exception as e: print(e)
        await asyncio.sleep(2)
asyncio.run(main())
