from dataclasses import dataclass


@dataclass
class ProductCode:
    product_code: str


@dataclass
class ProductDetail(ProductCode):
    src: str | None


@dataclass
class ProductImage(ProductCode):
    idx: int
    src: str | None
    alt: str | None
    media_type: str = "img"


@dataclass
class ProductHashtag(ProductCode):
    hashtag: str


@dataclass
class ProductPromotion(ProductCode):
    promotion_code: str | None
    promotion_name: str


@dataclass
class ProductReview(ProductCode):
    product_code: str
    product_eval_no: str | None  # 리뷰 작성 일자로 추정

    starpoint: int | None
    liked_cnt: int | None

    reviewer_name: str
    created_at: str

    reviewer_info: str | None
    option_info: str | None

    review_text: str | None

    review_rate_type_1: str | None
    review_rate_text_1: str | None

    review_rate_type_2: str | None
    review_rate_text_2: str | None

    review_rate_type_3: str | None
    review_rate_text_3: str | None


@dataclass
class ReviewImage(ProductCode):
    product_eval_no: str
    idx: int
    src: str | None
    alt: str | None
    media_type: str = "img"


@dataclass
class ProductColor(ProductCode):
    color_value: str | None


@dataclass
class ProductSize(ProductCode):
    size_value: str | None


@dataclass
class ProductOption(ProductCode):
    size_value: str | None
    color_value: str | None
    option_name: str


@dataclass
class ProductQNA(ProductCode):
    bedge: str | None
    text: str | None
    user: str | None
    created_at: str | None
    product_option: str | None
    question: str | None
    answer: str | None


@dataclass
class ProductData:
    product_info: dict
    product_detail: ProductDetail
    product_images: list[ProductImage]
    product_hashtags: list[ProductHashtag]
    related_promotions: list[ProductPromotion]
    product_reviews: list[ProductReview]
    review_images: list[ReviewImage]
    product_deliveries: list[dict]
    product_gifts: list[dict]
    gift_items: list[dict]
    product_colors: list[ProductColor]
    product_sizes: list[ProductSize]
    product_options: list[ProductOption]
    product_qnas: list[ProductQNA]
