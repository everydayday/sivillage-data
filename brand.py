import os
from attr import asdict, dataclass, fields
from fetch import fetch_all
from bs4 import BeautifulSoup
import asyncio
import re
import csv
import json


@dataclass
class Brand:
    brand_list_type: str
    brand_index_letter: str

    brand_name: str
    brand_name_ko: str

    ctg_no: str


async def brand():
    brand_A_to_Z_url = "https://m.sivillage.com/dispctg/brandAtoZTab.siv"
    html = (await fetch_all([brand_A_to_Z_url]))[0]

    soup = BeautifulSoup(html, "html.parser")

    brands = []

    for brand_tab in soup.select("div.brand-tab__brand-list"):
        brand_list_type = brand_tab.get_attribute_list("class")[-1]

        for brand_list in brand_tab.select("div.brand-index__letter"):
            brand_index_letter = brand_list.select_one("h3.brand-index__title")

            for brand in brand_list.select("li.brand-index__item"):
                ctg_no = brand.select_one("a.brand-index__item-text")
                brand_name = brand.select_one("p.brand-index__item-text-strong")
                brand_name_ko = brand.select_one("p.brand-index__item-text-description")

                if not (brand_index_letter and ctg_no and brand_name and brand_name_ko):
                    continue

                ctg_no = re.search(
                    r"'disp_ctg_no'\s*:\s*'([^']*)'",
                    str(ctg_no.get_attribute_list("href")[0]),
                )

                if not (ctg_no):
                    continue

                ctg_no = ctg_no.group(1)

                brand = Brand(
                    brand_list_type=brand_list_type,
                    brand_index_letter=brand_index_letter.text.strip(),
                    ctg_no=ctg_no,
                    brand_name=brand_name.text.strip(),
                    brand_name_ko=brand_name_ko.text.strip(),
                )

                brands.append(asdict(brand))

    csv_dir = f"./csv_data"
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    try:
        with open(f"{csv_dir}/brand.csv", "w", newline="", encoding="utf-8") as f:
            fieldnames = [field.name for field in fields(Brand)]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(brands)

    except IOError as e:
        print(e)

    json_dir = f"./json_data"
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    try:
        with open(f"{json_dir}/brand.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(brands, indent=4, ensure_ascii=False))

    except IOError as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(brand())
