import aiohttp
import asyncio


async def fetch(session: aiohttp.ClientSession, url):
    async with session.get(url) as resp:
        return await resp.text()


async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

