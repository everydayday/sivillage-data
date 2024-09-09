from dataclasses import asdict, dataclass, fields
import json
import os
from fetch import fetch_all
from bs4 import BeautifulSoup
import bs4
import asyncio
import csv


@dataclass
class Category:
    ctg_name: str
    ctg_no: str

    depth: int

    parent_ctg_name: str | None = None
    parent_ctg_no: str | None = None

    is_leaf: bool = False



def get_all_root_ctgs(html) -> list[Category]:
    soup = BeautifulSoup(html, "html.parser")

    root_ctgs = []
    for root_ctg in soup.select("div.nav__item > a[data-disp_ctg_no]"):
        root_ctgs.append(
            Category(
                depth=0,
                ctg_name=root_ctg.text.strip(),
                ctg_no=root_ctg.get_attribute_list("data-disp_ctg_no")[0].strip(),
            )
        )

    return root_ctgs


def ctg_from(tag: bs4.Tag, parent: Category) -> Category:

    ctg_name = tag.text.strip()
    ctg_no = tag.get_attribute_list("data-disp_ctg_no")[0].strip()

    return Category(
        depth=parent.depth + 1,
        ctg_name=ctg_name,
        ctg_no=ctg_no,
        parent_ctg_name=parent.ctg_name,
        parent_ctg_no=parent.ctg_no,
    )


def get_sub_ctgs(root_ctg: Category, html) -> list[Category]:
    soup = BeautifulSoup(html, "html.parser")

    ctgs = []

    big_list = soup.select("ul.list-big > li")
    for big in big_list:
        if not (big_tag := big.select_one("a")):
            continue

        big_ctg = ctg_from(big_tag, root_ctg)

        if not (medium_list := big.select("ul.list-medium > li")):
            big_ctg.is_leaf = True
        ctgs.append(big_ctg)

        for medium in medium_list:

            if not (medium_tag := medium.select_one("a")):
                continue
            medium_ctg = ctg_from(medium_tag, big_ctg)

            if not (small_list := medium.select("ul.list-small > li")):
                medium_ctg.is_leaf = True
            ctgs.append(medium_ctg)

            for small in small_list:
                if not (small_tag := small.select_one("a")):
                    continue
                small_ctg = ctg_from(small_tag, medium_ctg)

                small_ctg.is_leaf = True
                ctgs.append(small_ctg)

    return ctgs


async def category():
    url = "https://www.sivillage.com/main/initMain.siv"
    html = (await fetch_all([url]))[0]
    
    root_ctgs = get_all_root_ctgs(html)

    urls = [
        f"https://www.sivillage.com/dispctg/initDispCtg.siv?disp_ctg_no={root_ctg.ctg_no}{"&disp_clss_cd=20" if root_ctg.ctg_name=='뷰티' else ''}"
        for root_ctg in root_ctgs
    ]

    htmls = await fetch_all(urls)

    # ctgs = [*root_ctgs]
    ctgs = [asdict(root_ctg) for root_ctg in root_ctgs]

    for root_ctg, html in zip(root_ctgs, htmls):
        sub_ctgs = get_sub_ctgs(root_ctg, html)
        ctgs.extend([asdict(sub_ctg) for sub_ctg in sub_ctgs])
    
    csv_dir = f"./csv_data"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    try:
        with open(f"{csv_dir}/category.csv", "w", newline="", encoding="utf-8") as f:
            fieldnames = [field.name for field in fields(Category)]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ctgs)

    except IOError as e:
        print(e)
    
    json_dir = f"./json_data"
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    try:
        with open(f"{json_dir}/category.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(ctgs, indent=4, ensure_ascii=False))

    except IOError as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(category())
