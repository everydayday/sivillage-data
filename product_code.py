import json
import os
import aiohttp
import asyncio

from bs4 import BeautifulSoup

# 초당 요청 수 제한
MAX_REQUESTS_PER_SECOND = 60


async def fetch(session, ctg_no, page_idx):
    url = f"https://www.sivillage.com/dispctg/initDispCtg.siv?page_idx={page_idx}&outlet_yn=N&disp_ctg_no={ctg_no}&sort_type=90"

    async with session.get(url) as response:
        print(ctg_no, page_idx)

        html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        product_datas = soup.select("div.product__thum > button")

        product_codes = []
        for product_data in product_datas:
            product_code = product_data.attrs.get("data-goods-no")
            product_codes.append(product_code)

        if not os.path.exists(f"./product_code/{ctg_no}"):
            try:
                os.makedirs(f"./product_code/{ctg_no}")
            except Exception as e:
                print(e)

        print(len(product_codes))

        if product_codes:
            with open(
                f"./product_code/{ctg_no}/{page_idx}.json", "w", encoding="utf-8"
            ) as f:
                f.write(json.dumps(product_codes, indent=4, ensure_ascii=False))


async def limited_fetch(sem, session, ctg_no, page_idx):
    async with sem:  # 세마포어로 동시 요청 제한
        await asyncio.sleep(1 / MAX_REQUESTS_PER_SECOND)  # 요청 간격 유지
        return await fetch(session, ctg_no, page_idx)


async def fetch_product_codes():
    with open("./json_data/category.json", "r", encoding="utf-8") as f:
        ctg_nos = [
            category["ctg_no"]
            for category in json.loads(f.read())
            if category["is_leaf"] == True
        ]

    sem = asyncio.Semaphore(MAX_REQUESTS_PER_SECOND)  # 세마포어 설정

    print(len(ctg_nos))

    async with aiohttp.ClientSession() as session:
        pairs = [(ctg_no, page_idx) for page_idx in range(1, 3) for ctg_no in ctg_nos]

        tasks = [
            limited_fetch(sem, session, ctg_no, page_idx)
            for (ctg_no, page_idx) in pairs
        ]
        results = await asyncio.gather(*tasks)

    print(len(results))


def merge_product_codes():
    product_codes = []
    
    dir = './product_code'
    ctg_nos = os.listdir(dir)
    for ctg_no in ctg_nos:
        files = os.listdir(f"{dir}/{ctg_no}")
        for file in files:
            with open(f"{dir}/{ctg_no}/{file}", "r", encoding="utf-8") as f:
                product_codes.extend(json.loads(f.read()))
    
    with open("./product_codes.json", 'w', encoding="utf-8") as f:
        f.write(json.dumps(product_codes, indent=4, ensure_ascii=False))
        
    print(len(product_codes))


async def product_code():
  await fetch_product_codes()
  merge_product_codes()

if __name__ == "__main__":
    asyncio.run(product_code())