from dataclasses import asdict
import json
import os
import concurrent.futures
import re
from bs4 import BeautifulSoup

from dataclass import (
    ProductColor,
    ProductData,
    ProductDetail,
    ProductHashtag,
    ProductImage,
    ProductOption,
    ProductPromotion,
    ProductQNA,
    ProductReview,
    ProductSize,
    ReviewImage,
)

p_product_info = re.compile(r"data\s*:\s*JSON\.parse\('([^']*)'")
p_promotion_code = re.compile(r"disp_ctg_no\s*:\s*'([^']*)'")

dir_path = "./product_detail_m"


def save_product_data(args):
    [product_code, item] = args
    [key, value] = item
    if not os.path.exists(f"./data/{key}"):
        try:
            os.makedirs(f"./data/{key}")
        except:
            ...

    with open(f"./data/{key}/{product_code}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(value, indent=4, ensure_ascii=False))


def process_file(args):
    [idx, file_path] = args
    print(idx)
    product_code = file_path.split("/")[-1].split(".")[-2]

    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "lxml")

    # 상품 기본 정보
    _product_info = re.search(p_product_info, html)
    _product_info = (
        _product_info.group(1)
        if _product_info
        else '{"info": { "price": {}, "brand": {}, "deli": {} } }'
    )

    product_info = json.loads(_product_info).get("info")

    product_deliveries = [
        {"product_code": product_code, **deli} for deli in product_info.get("deli", [])
    ]
    product_info.pop("deli", None)

    product_gifts = [
        {"product_code": product_code, **gift} for gift in product_info.get("gift", [])
    ]
    product_info.pop("gift", None)

    gift_items = []
    for product_gift in product_gifts:
        gift_items.extend(
            [
                {"gift_mgmt_no": product_gift["gift_mgmt_no"], **item}
                for item in product_gift.pop("items", [])
            ]
        )

    product_info.update(product_info.get("price"))
    product_info.pop("price", None)
    
    product_info.update(product_info.get("brand"))
    product_info.pop("brand", None)

    # 상품 색상 / 사이즈 / 옵션

    colors = [
        inp.attrs.get("value")
        for inp in soup.select("input[type='radio'][name='color']")
    ]
    sizes = [
        (button.attrs.get("data-opt_val_nm") or "/").split("/")[-1]
        for button in soup.select("button[data-opt_val_nm]")
    ]

    product_colors = [
        ProductColor(product_code=product_code, color_value=color) for color in colors
    ]
    product_sizes = [
        ProductSize(product_code=product_code, size_value=size) for size in sizes
    ]

    product_options = [
        ProductOption(
            product_code=product_code,
            color_value=color,
            size_value=size,
            option_name=f"{color}/{size}",
        )
        for size in sizes
        for color in colors
    ]

    # 제품 상세 설명
    product_detail_iframe = soup.select_one("iframe#m2-frame")
    product_detail_src = (
        product_detail_iframe.attrs.get("src") if product_detail_iframe else None
    )

    product_detail = ProductDetail(product_code=product_code, src=product_detail_src)

    # 제품 이미지
    product_images = [
        ProductImage(
            product_code=product_code,
            idx=idx,
            src=slide.attrs.get("src"),
            alt=slide.attrs.get("alt"),
        )
        for idx, slide in enumerate(soup.select("div.detail__vi-slide>img"))
    ]

    # 해시태그
    product_hashtags = [
        ProductHashtag(product_code=product_code, hashtag=btn.text.strip())
        for btn in soup.select("button.detail__hashtag-btn")
    ]

    # 관련 기획전
    related_promotions = []
    for a in soup.select("ul.related__list>li>a"):
        promotion_code = re.search(p_promotion_code, a.attrs.get("onclick") or "")
        promotion_code = promotion_code.group(1) if promotion_code else None
        related_promotions.append(
            ProductPromotion(
                product_code=product_code,
                promotion_code=promotion_code,
                promotion_name=a.text.strip(),
            )
        )

    # 리뷰
    review_contnets = soup.select("div.review-content")

    product_reviews = []
    review_images = []

    for review_content in review_contnets:
        _starpoint = review_content.select_one("p.starpoint__now")
        starpoint = int(_starpoint.text.strip()) if _starpoint else None

        [reviewer_name, created_at, *_] = [
            *[span.text.strip() for span in review_content.select("p.user-info>span")],
            None,
            None,
            None,
        ]

        review_info = review_content.select("div.review-size-info>p")
        if len(review_info) >= 2:
            [reviewer_info, option_info] = [p.text.strip() for p in review_info]
        elif len(review_info) == 1:
            reviewer_info = None
            option_info = review_info[0].text.strip()
        else:
            [reviewer_info, option_info] = [None, None]

        _like_btn = review_content.select_one("button.like-review-btn")
        product_eval_no = (
            _like_btn.attrs.get("data-goods_eval_no") if _like_btn else None
        )
        _liked_cnt = _like_btn.select_one("span.text") if _like_btn else None
        liked_cnt = int(_liked_cnt.text.strip()) if _liked_cnt else None

        _review_text = review_content.select_one("div.review-text")
        review_text = _review_text.text.strip() if _review_text else None

        [review_rate_type_1, review_rate_type_2, review_rate_type_3, *_] = [
            *[
                p.text.strip()
                for p in review_content.select("p.detail__tab-review-rate-bedge")
            ],
            None,
            None,
            None,
            None,
        ]
        [review_rate_text_1, review_rate_text_2, review_rate_text_3, *_] = [
            *[
                p.text.strip()
                for p in review_content.select("p.detail__tab-review-rate-text")
            ],
            None,
            None,
            None,
            None,
        ]

        product_reviews.append(
            ProductReview(
                product_code=product_code,
                product_eval_no=product_eval_no,
                starpoint=starpoint,
                liked_cnt=liked_cnt,
                reviewer_name=reviewer_name,
                created_at=created_at,
                reviewer_info=reviewer_info,
                option_info=option_info,
                review_text=review_text,
                review_rate_type_1=review_rate_type_1,
                review_rate_type_2=review_rate_type_2,
                review_rate_type_3=review_rate_type_3,
                review_rate_text_1=review_rate_text_1,
                review_rate_text_2=review_rate_text_2,
                review_rate_text_3=review_rate_text_3,
            )
        )

        review_images.extend(
            [
                ReviewImage(
                    product_code=img.attrs.get("data-goods_no") or "",
                    product_eval_no=img.attrs.get("data-goods_eval_no") or "",
                    idx=idx,
                    src=img.attrs.get("src"),
                    alt=img.attrs.get("alt"),
                )
                for (idx, img) in enumerate(
                    review_content.select("button.review-image>img"), 1
                )
            ]
        )

    # QNA
    product_qnas = []
    for qna in soup.select("li.detail__tab-qna-item"):
        _qna_bedge = qna.select_one("p.detail__tab-qna-bedge")
        qna_bedge = _qna_bedge.text.strip() if _qna_bedge else None

        _qna_text = qna.select_one("p.detail__tab-qna-text")
        qna_text = _qna_text.text.strip() if _qna_text else None

        _qna_product_option = qna.select_one("div.detail__tab-qna-answer-product")
        qna_product_option = (
            _qna_product_option.text.strip() if _qna_product_option else None
        )

        [qna_user, qna_created_at, *_] = [
            *[span.text.strip() for span in qna.select("p.detail__tab-qna-user>span")],
            None,
            None,
            None,
        ]

        [qna_question, qna_answer, *_] = [
            *[p.text.strip() for p in qna.select("p.detail__tab-qna-answer-text")],
            None,
            None,
            None,
        ]

        product_qnas.append(
            ProductQNA(
                product_code=product_code,
                bedge=qna_bedge,
                text=qna_text,
                user=qna_user,
                created_at=qna_created_at,
                product_option=qna_product_option,
                question=qna_question,
                answer=qna_answer,
            )
        )

    product_data = ProductData(
        product_info=product_info,
        product_detail=product_detail,
        product_images=product_images,
        product_hashtags=product_hashtags,
        related_promotions=related_promotions,
        product_reviews=product_reviews,
        review_images=review_images,
        product_deliveries=product_deliveries,
        product_gifts=product_gifts,
        gift_items=gift_items,
        product_colors=product_colors,
        product_sizes=product_sizes,
        product_options=product_options,
        product_qnas=product_qnas,
    )

    try:
        product_data_items = [[product_code, item] for item in asdict(product_data).items()]
    except:
        print(type(product_data))
        return

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(product_data_items)
    ) as executor:
        result = list(executor.map(save_product_data, product_data_items))


def main():
    file_paths = [f"{dir_path}/{file_name}" for file_name in os.listdir(dir_path)]
    cpu_count = os.cpu_count()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
        result = list(executor.map(process_file, [*enumerate(file_paths)]))

    print(len(result))


if __name__ == "__main__":
    main()
