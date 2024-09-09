import json
import os
import aiohttp
import asyncio

# 초당 요청 수 제한
MAX_REQUESTS_PER_SECOND = 60


async def fetch(session, product_code, i):
    url = f"https://m.sivillage.com/goods/initDetailGoods.siv?goods_no={product_code}"

    async with session.get(url) as response:
        if not os.path.exists("./product_detail_m"):
            try:
                os.makedirs("./product_detail_m")
            except:
                ...

        with open(
            f"./product_detail_m/{product_code}.html", "w", encoding="utf-8"
        ) as f:
            f.write(await response.text())
            print(i)


async def limited_fetch(sem, session, product_code, i):
    async with sem:  # 세마포어로 동시 요청 제한
        await asyncio.sleep(1 / MAX_REQUESTS_PER_SECOND)  # 요청 간격 유지
        return await fetch(session, product_code, i)


async def product_detail():
    with open("./product_codes.json", "r", encoding="utf-8") as f:
        product_codes = json.loads(f.read())

    sem = asyncio.Semaphore(MAX_REQUESTS_PER_SECOND)  # 세마포어 설정

    print(len(product_codes))

    async with aiohttp.ClientSession() as session:

        tasks = [
            limited_fetch(sem, session, product_code, i)
            for (i, product_code) in [*enumerate(product_codes)]
        ]
        results = await asyncio.gather(*tasks)

    print(len(results))


if __name__ == "__main__":
    asyncio.run(product_detail())
