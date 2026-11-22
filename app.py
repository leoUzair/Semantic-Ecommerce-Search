from pathlib import Path
import html
import math
import re
from urllib.parse import quote

import requests
import streamlit as st

from src.semantic_search import build_search_engine


# ============================================================
# 1. PAGE CONFIGURATION AND THEME
# ============================================================
st.set_page_config(
    page_title="Findly | Semantic Shopping",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent
IMAGE_DIR = PROJECT_ROOT / "assets" / "products"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #697386;
        --brand: #5b5ce2;
        --brand-dark: #4546c8;
        --surface: #ffffff;
        --canvas: #f5f7fb;
        --line: #e8ebf2;
        --soft: #f0f1ff;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(245,247,251,.92); }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { max-width: 1450px; padding-top: 1.25rem; padding-bottom: 3rem; }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }

    h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; color: var(--ink); }
    h1 { letter-spacing: -1.3px; }
    p, label, li { color: var(--ink); }

    .topbar {
        display:flex; align-items:center; justify-content:space-between;
        gap:16px; padding: 13px 18px; margin-bottom: 24px;
        background: #fff; border:1px solid var(--line); border-radius:16px;
        box-shadow: 0 4px 18px rgba(28,39,70,.035);
    }
    .brandmark { display:flex; align-items:center; gap:10px; font-weight:800;
        font-family:'Manrope',sans-serif; font-size:20px; color:var(--ink); }
    .brand-icon { width:36px; height:36px; display:grid; place-items:center;
        border-radius:11px; background:linear-gradient(135deg,#7778f5,#4e50d5); color:#fff; }
    .topnav { color:#697386; font-size:13px; font-weight:600; }
    .topnav span { margin-left:20px; }
    .hero {
        padding: 30px 32px; border-radius:22px; margin-bottom:22px;
        background: radial-gradient(circle at 87% 15%, rgba(255,255,255,.20), transparent 25%),
                    linear-gradient(120deg,#292b70 0%,#5354d7 58%,#7879ef 100%);
        color:#fff; box-shadow:0 15px 35px rgba(75,76,190,.18);
    }
    .hero-kicker { color:#dedefe; text-transform:uppercase; letter-spacing:1.6px;
        font-size:11px; font-weight:800; margin-bottom:10px; }
    .hero-title { color:#fff !important; font-family:'Manrope',sans-serif;
        font-size: clamp(27px,3.2vw,42px); line-height:1.12; font-weight:800;
        letter-spacing:-1.5px; margin:0 0 10px 0; }
    .hero-copy { color:#ececff; font-size:15px; max-width:720px; margin:0; }
    .hero-pill { display:inline-block; margin-top:17px; padding:7px 12px;
        border:1px solid rgba(255,255,255,.28); border-radius:99px;
        color:#fff; font-size:12px; background:rgba(255,255,255,.10); }

    .section-eyebrow { color:var(--brand); font-size:11px; font-weight:800;
        letter-spacing:1.2px; text-transform:uppercase; margin-bottom:5px; }
    .section-title { font-family:'Manrope',sans-serif; font-size:23px;
        font-weight:800; letter-spacing:-.5px; color:var(--ink); margin-bottom:3px; }
    .section-subtitle { color:var(--muted); font-size:13px; }
    .metric-card { background:#fff; border:1px solid var(--line); border-radius:15px;
        padding:15px 17px; min-height:91px; box-shadow:0 3px 12px rgba(28,39,70,.025); }
    .metric-label { color:var(--muted); font-size:12px; font-weight:600; }
    .metric-value { font-family:'Manrope',sans-serif; color:var(--ink);
        font-size:25px; font-weight:800; margin-top:4px; }

    div[data-testid="stForm"] { background:#fff; padding:16px 18px 12px;
        border:1px solid var(--line); border-radius:16px; }
    div[data-testid="stTextInput"] input { border-radius:11px; min-height:48px; }
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {
        border-radius:10px; font-weight:700; min-height:40px; }
    div[data-testid="stFormSubmitButton"] button {
        background:var(--brand); border-color:var(--brand); color:#fff; }
    div[data-testid="stFormSubmitButton"] button:hover { background:var(--brand-dark); color:#fff; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background:#fff; border:1px solid var(--line); border-radius:16px;
        box-shadow:0 5px 18px rgba(28,39,70,.035); }
    .product-visual { height:165px; width:100%; display:flex; align-items:center;
        justify-content:center; border-radius:12px; margin-bottom:12px;
        background:linear-gradient(145deg,#f0f1ff,#f8f9fd); font-size:66px; }
    .product-category { display:inline-block; background:var(--soft); color:#5152c9;
        border-radius:99px; padding:4px 9px; font-size:10px; font-weight:800;
        text-transform:uppercase; letter-spacing:.45px; margin:2px 0 8px; }
    .product-name { color:var(--ink); font-family:'Manrope',sans-serif;
        font-size:16px; line-height:1.35; font-weight:800; min-height:43px; }
    .product-brand { color:var(--muted); font-size:12px; margin:4px 0 9px; }
    .product-desc { color:#667085; font-size:12px; line-height:1.5; min-height:55px; }
    .product-price { color:var(--ink); font-family:'Manrope',sans-serif;
        font-size:22px; font-weight:800; margin-top:10px; }
    .score-label { display:flex; justify-content:space-between; color:var(--muted);
        font-size:11px; margin-top:8px; }
    .trust-note { padding:12px 15px; border:1px solid #e8e9ff; border-radius:12px;
        background:#f7f7ff; color:#5b5d86; font-size:12px; }
    .empty-state { text-align:center; padding:35px 15px; border:1px dashed #d6daea;
        background:#fff; border-radius:16px; }
    .empty-icon { font-size:40px; }
    .empty-title { color:var(--ink); font-family:'Manrope',sans-serif;
        font-weight:800; font-size:18px; margin:8px 0 3px; }
    .empty-copy { color:var(--muted); font-size:13px; }
    .footer-note { text-align:center; color:#8a92a4; font-size:11px; padding:20px 0 5px; }

    [data-testid="stMetric"] { background:#fff; border:1px solid var(--line);
        border-radius:13px; padding:12px 14px; }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    [data-testid="stMetricValue"] { color:var(--ink); }
    [data-testid="stProgressBar"] > div > div { background-color:var(--brand); }
    [data-testid="stExpander"] { border-color:var(--line); border-radius:10px; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; }
    .stTabs [data-baseweb="tab"] { border-radius:9px; padding:9px 15px; }

    @media (max-width: 700px) {
        .block-container { padding-left:1rem; padding-right:1rem; }
        .hero { padding:23px 20px; }
        .topnav { display:none; }
        .product-visual { height:130px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. LOAD THE EXISTING NLP SEARCH ENGINE
# ============================================================
@st.cache_resource(show_spinner="Loading NLP search engine...")
def get_search_engine():
    return build_search_engine()


search_engine = get_search_engine()
products = search_engine.products.copy()

required_columns = {
    "product_id", "product_name", "category", "brand",
    "price", "description", "semantic_score",
    "keyword_score", "similarity_score"
}
missing_columns = required_columns - set(
    search_engine.search("test", top_k=1).columns
)
if missing_columns:
    st.error(
        "The search engine is missing required result columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

products["price"] = products["price"].astype(float)
min_price = int(products["price"].min())
max_price = int(products["price"].max())


# ============================================================
# 3. AUTOMATIC REAL PRODUCT PHOTOS (OPENVERSE)
# ============================================================
# Openverse provides anonymous access to openly licensed images.
# We search using product-specific terms, retrieve real photographs,
# and show creator/licence attribution below each image.

CATEGORY_VISUALS = {
    "clothing": ("🧥", "#EEF0FF"),
    "footwear": ("👟", "#EAF5F1"),
    "electronics": ("💻", "#EAF1FF"),
    "bags": ("🎒", "#FFF1E8"),
    "accessories": ("🕶️", "#F4EEFF"),
    "outdoor gear": ("🏕️", "#EAF4EA"),
    "home": ("🏠", "#FFF4E8"),
    "home appliances": ("🏠", "#FFF4E8"),
    "kitchen appliances": ("🍳", "#FFF4E8"),
    "stationery": ("📚", "#EEF4FF"),
    "furniture": ("🪑", "#F5F0EA"),
    "personal care": ("🧴", "#FDEEF3"),
    "tools": ("🛠️", "#EEF0F5"),
    "automotive": ("🚗", "#EEF2F7"),
    "fitness": ("🏋️", "#EAF5F1"),
    "travel accessories": ("🧳", "#FFF1E8"),
}

IMAGE_STOP_WORDS = {
    "a", "an", "the", "and", "or", "for", "with", "of", "to",
    "in", "on", "by", "new", "product", "products", "premium",
}

IMAGE_TOKEN_FORMS = {
    "boots": "boot", "shoes": "shoe", "sneakers": "sneaker",
    "backpacks": "backpack", "headphones": "headphone",
    "sunglasses": "sunglass", "gloves": "glove", "socks": "sock",
    "jeans": "jean", "watches": "watch", "batteries": "battery",
    "laptops": "laptop", "tents": "tent", "bottles": "bottle",
    "jackets": "jacket", "blankets": "blanket",
}

# Product types that should not be confused with one another.
IMAGE_TYPE_FAMILIES = {
    "shoe": {"shoe", "sneaker", "trainer"},
    "boot": {"boot"},
    "sandal": {"sandal"},
    "laptop": {"laptop", "notebook computer"},
    "headphone": {"headphone", "earphone", "headset"},
    "tent": {"tent"},
    "bottle": {"bottle", "flask"},
    "watch": {"watch"},
    "sunglass": {"sunglass", "eyewear"},
    "backpack": {"backpack", "rucksack"},
    "umbrella": {"umbrella"},
    "chair": {"chair"},
    "pillow": {"pillow"},
    "mattress": {"mattress"},
    "kettle": {"kettle"},
    "heater": {"heater"},
    "camera": {"camera"},
}


def image_tokens(text):
    words = re.findall(r"[a-z0-9]+", str(text).lower())
    return {
        IMAGE_TOKEN_FORMS.get(word, word)
        for word in words
        if word not in IMAGE_STOP_WORDS
    }


def required_image_type(product_name):
    tokens = image_tokens(product_name)
    for token, family in IMAGE_TYPE_FAMILIES.items():
        if token in tokens:
            return family
    return set()


@st.cache_data(ttl=7 * 24 * 60 * 60, show_spinner=False)
def search_openverse_photos(query):
    """Search Openverse for openly licensed photographs; cached for 7 days."""
    params = {
        "q": query,
        "page_size": 30,
        "category": "photograph",
        "mature": "false",
        "license_type": "commercial",
    }
    headers = {
        "User-Agent": "FindlyAI/1.0 (student NLP e-commerce project)"
    }
    try:
        response = requests.get(
            "https://api.openverse.org/v1/images/",
            params=params,
            headers=headers,
            timeout=18,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", [])
    except (requests.RequestException, ValueError):
        return []


def find_product_photo(product):
    """Find a relevant real photo and return URL plus attribution."""
    product_name = str(product.get("product_name", "")).strip()
    category = str(product.get("category", "")).strip()
    if not product_name:
        return None

    target_tokens = image_tokens(product_name)
    required_type = required_image_type(product_name)

    # Search the product title first. Add the category only as a fallback.
    queries = [product_name, f"{product_name} {category} product photo"]
    seen_urls = set()
    best = None
    best_score = 0.0

    for query in queries:
        candidates = search_openverse_photos(query)
        for item in candidates:
            title = str(item.get("title", ""))
            tags = item.get("tags", []) or []
            tag_text = " ".join(
                str(tag.get("name", "")) if isinstance(tag, dict) else str(tag)
                for tag in tags
            )
            searchable_text = f"{title} {tag_text} {item.get('attribution', '')}"
            candidate_tokens = image_tokens(searchable_text)
            if not candidate_tokens:
                continue

            # If the product has a clear physical type (e.g. boot, tent,
            # laptop), do not substitute a different type (e.g. heels).
            if required_type and not candidate_tokens.intersection(required_type):
                continue

            matched = target_tokens.intersection(candidate_tokens)
            coverage = len(matched) / max(len(target_tokens), 1)
            # Openverse already ranks by full-text relevance; use title/tag
            # overlap to reject unrelated search hits instead of guessing.
            title_tokens = image_tokens(title)
            title_coverage = len(target_tokens.intersection(title_tokens)) / max(len(target_tokens), 1)
            score = 0.65 * coverage + 0.35 * title_coverage

            image_url = item.get("thumbnail") or item.get("url")
            if not isinstance(image_url, str) or not image_url.startswith("https://"):
                continue
            if image_url in seen_urls:
                continue
            seen_urls.add(image_url)

            # Require at least one product-specific match and a modest score.
            if matched and score > best_score:
                best_score = score
                best = {
                    "url": image_url,
                    "title": title or product_name,
                    "creator": item.get("creator") or "Unknown creator",
                    "creator_url": item.get("creator_url") or "",
                    "license": item.get("license") or "See source licence",
                    "license_version": item.get("license_version") or "",
                    "license_url": item.get("license_url") or "",
                    "source_url": item.get("foreign_landing_url") or item.get("detail_url") or "https://openverse.org/",
                    "source": item.get("source") or item.get("provider") or "Openverse",
                }

        if best is not None and best_score >= 0.55:
            break

    return best if best_score >= 0.35 else None


def get_product_image_data(product):
    """Prefer explicit product images, then fetch a real Openverse photo."""
    product_id = int(product["product_id"])

    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        local_image = IMAGE_DIR / f"{product_id}{extension}"
        if local_image.is_file():
            return {"url": str(local_image), "source": "Local product image"}

    if "image_url" in product.index:
        image_url = product.get("image_url")
        if isinstance(image_url, str) and image_url.startswith("https://"):
            return {"url": image_url, "source": "Product image URL"}

    return find_product_photo(product)


def render_product_visual(product):
    image_data = get_product_image_data(product)
    if image_data:
        st.image(image_data["url"], use_container_width=True)
        if image_data.get("source"):
            st.caption(image_data["source"])
        else:
            creator = html.escape(str(image_data.get("creator", "Unknown creator")))
            license_name = html.escape(str(image_data.get("license", "See source licence")))
            source_url = html.escape(str(image_data.get("source_url", "https://openverse.org/")), quote=True)
            creator_url = image_data.get("creator_url") or ""
            creator_link = (
                f'<a href="{html.escape(creator_url, quote=True)}" target="_blank">{creator}</a>'
                if creator_url.startswith("https://") else creator
            )
            license_url = image_data.get("license_url") or ""
            license_link = (
                f'<a href="{html.escape(license_url, quote=True)}" target="_blank">{license_name}</a>'
                if license_url.startswith("https://") else license_name
            )
            st.markdown(
                f'<div style="font-size:10px;color:#697386;margin-top:-8px;">'
                f'<a href="{source_url}" target="_blank">Photo source</a> · '
                f'Photo by {creator_link} · {license_link}</div>',
                unsafe_allow_html=True,
            )
        return

    category = str(product.get("category", "")).strip().lower()
    emoji, background = CATEGORY_VISUALS.get(category, ("🛍️", "#F0F1FF"))
    st.markdown(
        f'<div class="product-visual" style="background:{background};">{emoji}</div>',
        unsafe_allow_html=True,
    )
    st.caption("No matching open-licence photo was returned for this item.")


# ============================================================
# 4. SESSION STATE
# ============================================================
def reset_filters():
    st.session_state.category_filter = []
    st.session_state.brand_filter = []
    st.session_state.price_filter = (min_price, max_price)
    st.session_state.sort_filter = "Best match"
    st.session_state.min_score_filter = 0.0
    st.session_state.result_page = 1


state_defaults = {
    "active_query": "",
    "search_history": [],
    "wishlist": [],
    "category_filter": [],
    "brand_filter": [],
    "price_filter": (min_price, max_price),
    "sort_filter": "Best match",
    "min_score_filter": 0.0,
    "per_page": 9,
    "result_page": 1,
    "use_cross_encoder": False,
    "search_result_cache": {},
}
for state_key, default_value in state_defaults.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# ============================================================
# 5. TOP NAVIGATION AND HERO
# ============================================================
st.markdown(
    """
    <div class="topbar">
      <div class="brandmark"><span class="brand-icon">✦</span> FINDLY <span style="color:#7778e8">AI</span></div>
      <div class="topnav"><span>SMART PRODUCT DISCOVERY</span><span>SEMANTIC SEARCH</span><span>POWERED BY NLP</span></div>
    </div>
    <section class="hero">
      <div class="hero-kicker">A smarter way to shop</div>
      <div class="hero-title">Find what you mean.<br>Not just what you type.</div>
      <p class="hero-copy">Describe a need in your own words. Find products by combining sentence meaning and keyword relevance.</p>
      <span class="hero-pill">✦ AI-powered semantic + keyword search</span>
    </section>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6. SIDEBAR FILTERS
# ============================================================
with st.sidebar:
    st.markdown("### Refine your results")
    st.caption("Filters are optional. Leave them unchanged to search the full catalogue.")
    if st.button("↺  Reset all filters", use_container_width=True):
        reset_filters()
        st.rerun()

    category_options = sorted(products["category"].dropna().unique().tolist())
    brand_options = sorted(products["brand"].dropna().unique().tolist())

    st.multiselect(
        "Category", category_options, key="category_filter",
        placeholder="All categories"
    )
    st.multiselect(
        "Brand", brand_options, key="brand_filter",
        placeholder="All brands"
    )
    st.slider(
        "Price range (₹)", min_value=min_price, max_value=max_price,
        key="price_filter", step=1
    )
    st.slider(
        "Minimum relevance", min_value=0.0, max_value=1.0,
        key="min_score_filter", step=0.05,
        help="Optional threshold applied to the first-stage hybrid retrieval score."
    )
    st.checkbox(
        "Use Cross-Encoder re-ranking",
        key="use_cross_encoder",
        help=(
            "Runs a second neural model on retrieved query-product pairs. "
            "The model downloads the first time and makes each search slower, "
            "but can improve ranking. It is optional."
        ),
    )
    st.selectbox(
        "Sort products", ["Best match", "Price: low to high", "Price: high to low"],
        key="sort_filter"
    )
    st.selectbox(
        "Products per page", [6, 9, 12, 18, 24], key="per_page"
    )

    st.markdown("---")
    st.markdown("**Your saved items**")
    st.caption(f"{len(st.session_state.wishlist)} product(s) in your wishlist")
    if st.session_state.search_history:
        with st.expander("Recent searches"):
            for old_query in st.session_state.search_history[:6]:
                st.write(f"• {old_query}")


# ============================================================
# 7. SEARCH FORM AND QUICK SEARCHES
# ============================================================
with st.form("main_search_form", clear_on_submit=False):
    search_col, action_col = st.columns([5, 1])
    with search_col:
        query_input = st.text_input(
            "Describe what you are looking for",
            placeholder="e.g. waterproof shoes for a rainy mountain trek",
            label_visibility="collapsed",
        )
    with action_col:
        submitted = st.form_submit_button("Search  →", use_container_width=True)

if submitted:
    cleaned_query = query_input.strip()
    if cleaned_query:
        st.session_state.active_query = cleaned_query
        history = st.session_state.search_history
        st.session_state.search_history = [cleaned_query] + [
            item for item in history if item.lower() != cleaned_query.lower()
        ]
        st.session_state.result_page = 1
    else:
        st.warning("Please enter a search query.")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.caption("Popular ways to search")
quick_queries = [
    "Waterproof shoes for hiking",
    "A laptop for programming",
    "Warm clothes for winter",
    "Gear for camping outdoors",
]
quick_cols = st.columns(4)
for index, quick_query in enumerate(quick_queries):
    with quick_cols[index]:
        if st.button(quick_query, key=f"quick_{index}", use_container_width=True):
            st.session_state.active_query = quick_query
            history = st.session_state.search_history
            st.session_state.search_history = [quick_query] + [
                item for item in history if item.lower() != quick_query.lower()
            ]
            st.session_state.result_page = 1
            st.rerun()


# ============================================================
# 8. TOP-LEVEL TABS
# ============================================================
search_tab, saved_tab, about_tab = st.tabs(
    ["⌕  Discover products", "♡  Wishlist", "ⓘ  About this project"]
)

with search_tab:
    active_query = st.session_state.active_query

    if not active_query:
        st.markdown(
            """
            <div class="empty-state">
              <div class="empty-icon">⌕</div>
              <div class="empty-title">Your next great find starts here</div>
              <div class="empty-copy">Search in natural language or choose one of the popular searches above.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        use_reranker = bool(st.session_state.use_cross_encoder)
        cache_key = (active_query, use_reranker)

        with st.spinner("Understanding your request and ranking products..."):
            result_cache = st.session_state.search_result_cache

            if cache_key in result_cache:
                all_results = result_cache[cache_key].copy()
            else:
                if use_reranker:
                    try:
                        # The current catalogue is small, so rerank every product
                        # retrieved by the first-stage hybrid search. For a larger
                        # catalogue, use a bounded candidate_k (e.g. 50 or 100).
                        all_results = search_engine.search_reranked(
                            active_query,
                            top_k=len(products),
                            candidate_k=len(products),
                        )
                    except Exception as exc:
                        st.warning(
                            "Cross-Encoder could not be loaded or executed. "
                            "Falling back to hybrid search. "
                            f"Details: {type(exc).__name__}: {exc}"
                        )
                        all_results = search_engine.search(
                            active_query, top_k=len(products)
                        )
                else:
                    all_results = search_engine.search(
                        active_query, top_k=len(products)
                    )

                result_cache[cache_key] = all_results.copy()
                # Keep the session cache bounded.
                while len(result_cache) > 12:
                    result_cache.pop(next(iter(result_cache)))
                st.session_state.search_result_cache = result_cache

            filtered_results = all_results.copy()

            selected_categories = st.session_state.category_filter
            selected_brands = st.session_state.brand_filter
            selected_price = st.session_state.price_filter
            min_score = st.session_state.min_score_filter

            if selected_categories:
                filtered_results = filtered_results[
                    filtered_results["category"].isin(selected_categories)
                ]
            if selected_brands:
                filtered_results = filtered_results[
                    filtered_results["brand"].isin(selected_brands)
                ]

            filtered_results = filtered_results[
                (filtered_results["price"] >= selected_price[0])
                & (filtered_results["price"] <= selected_price[1])
                & (filtered_results["similarity_score"] >= min_score)
            ]

            sort_choice = st.session_state.sort_filter
            if sort_choice == "Price: low to high":
                filtered_results = filtered_results.sort_values("price", ascending=True)
            elif sort_choice == "Price: high to low":
                filtered_results = filtered_results.sort_values("price", ascending=False)

        total_matches = len(filtered_results)
        per_page = st.session_state.per_page
        total_pages = max(1, (total_matches + per_page - 1) // per_page)
        current_page = min(st.session_state.result_page, total_pages)
        st.session_state.result_page = current_page

        start_index = (current_page - 1) * per_page
        page_results = filtered_results.iloc[start_index:start_index + per_page]

        st.markdown(
            f"<div class='section-eyebrow'>SEARCH RESULTS</div>"
            f"<div class='section-title'>Results for “{html.escape(active_query)}”</div>"
            f"<div class='section-subtitle'>{'Hybrid retrieval with Cross-Encoder re-ranking.' if 'rerank_score' in filtered_results.columns else 'Ranked using hybrid semantic and keyword relevance.'}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        metric_cols = st.columns(4)
        metric_values = [
            ("CATALOGUE", f"{len(products)}", "Products indexed"),
            ("MATCHES", f"{total_matches}", "After filters"),
            ("CATEGORIES", f"{products['category'].nunique()}", "Shopping departments"),
            ("WISHLIST", f"{len(st.session_state.wishlist)}", "Saved products"),
        ]
        for col, (label, value, detail) in zip(metric_cols, metric_values):
            with col:
                st.markdown(
                    f"<div class='metric-card'><div class='metric-label'>{label}</div>"
                    f"<div class='metric-value'>{value}</div><div class='metric-label'>{detail}</div></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        if total_matches == 0:
            st.warning("No products match the current filters. Reset or loosen the filters to see more results.")
        else:
            st.caption(
                f"Showing {start_index + 1}–{start_index + len(page_results)} "
                f"of {total_matches} matching products · Page {current_page} of {total_pages}"
            )

            # Three-column responsive product grid.
            grid_columns = st.columns(3, gap="medium")
            for index, (_, product) in enumerate(page_results.iterrows()):
                with grid_columns[index % 3]:
                    product_id = int(product["product_id"])
                    with st.container(border=True):
                        render_product_visual(product)

                        st.markdown(
                            f"<div class='product-category'>{html.escape(str(product['category']))}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<div class='product-name'>{html.escape(str(product['product_name']))}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<div class='product-brand'>{html.escape(str(product['brand']))}</div>",
                            unsafe_allow_html=True,
                        )
                        description = str(product["description"])
                        if len(description) > 118:
                            description = description[:115].rsplit(" ", 1)[0] + "..."
                        st.markdown(
                            f"<div class='product-desc'>{html.escape(description)}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<div class='product-price'>₹{float(product['price']):,.0f}</div>",
                            unsafe_allow_html=True,
                        )
                        score = float(product["similarity_score"])
                        st.markdown(
                            f"<div class='score-label'><span>Hybrid retrieval score</span><b>{score:.3f}</b></div>",
                            unsafe_allow_html=True,
                        )
                        st.progress(max(0.0, min(1.0, score)))

                        if product_id in st.session_state.wishlist:
                            if st.button("♥  Saved", key=f"wish_remove_{product_id}", use_container_width=True):
                                st.session_state.wishlist.remove(product_id)
                                st.rerun()
                        else:
                            if st.button("♡  Add to wishlist", key=f"wish_add_{product_id}", use_container_width=True):
                                st.session_state.wishlist.append(product_id)
                                st.rerun()

                        with st.expander("Product details"):
                            st.write(str(product["description"]))
                            st.write(f"Product ID: {product_id}")
                            st.write(f"Semantic score: {float(product['semantic_score']):.4f}")
                            st.write(f"Keyword score: {float(product['keyword_score']):.4f}")
                            st.write(f"Hybrid score: {score:.4f}")
                            if "rerank_score" in product.index:
                                st.write(
                                    "Cross-Encoder raw ranking score: "
                                    f"{float(product['rerank_score']):.4f}"
                                )
                                st.caption(
                                    "Cross-Encoder scores are ranking logits, "
                                    "not probabilities."
                                )

            page_left, page_mid, page_right = st.columns([1, 2, 1])
            with page_left:
                if st.button("← Previous", disabled=current_page <= 1, use_container_width=True):
                    st.session_state.result_page = current_page - 1
                    st.rerun()
            with page_mid:
                st.markdown(
                    f"<div style='text-align:center;color:#697386;padding:8px'>Page {current_page} / {total_pages}</div>",
                    unsafe_allow_html=True,
                )
            with page_right:
                if st.button("Next →", disabled=current_page >= total_pages, use_container_width=True):
                    st.session_state.result_page = current_page + 1
                    st.rerun()

            export_columns = [
                column for column in [
                    "product_id", "product_name", "category", "brand", "price",
                    "description", "semantic_score", "keyword_score", "similarity_score"
                ] if column in filtered_results.columns
            ]
            csv_data = filtered_results[export_columns].to_csv(index=False).encode("utf-8")
            st.download_button(
                "↓  Download all filtered results (CSV)",
                data=csv_data,
                file_name="findly_search_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.markdown(
                "<div class='trust-note'>ⓘ Photos are retrieved from Openverse when a relevant openly licensed photograph is available. Creator and licence information is shown below each photo.</div>",
                unsafe_allow_html=True,
            )

with saved_tab:
    st.markdown("<div class='section-eyebrow'>YOUR COLLECTION</div><div class='section-title'>Saved products</div>", unsafe_allow_html=True)
    wishlist_ids = set(st.session_state.wishlist)
    saved_products = products[products["product_id"].astype(int).isin(wishlist_ids)]
    if saved_products.empty:
        st.markdown(
            "<div class='empty-state'><div class='empty-icon'>♡</div>"
            "<div class='empty-title'>Your wishlist is empty</div>"
            "<div class='empty-copy'>Save products from the Discover tab to collect them here.</div></div>",
            unsafe_allow_html=True,
        )
    else:
        saved_cols = st.columns(3, gap="medium")
        for index, (_, product) in enumerate(saved_products.iterrows()):
            with saved_cols[index % 3]:
                with st.container(border=True):
                    render_product_visual(product)
                    st.markdown(f"**{html.escape(str(product['product_name']))}**")
                    st.caption(f"{product['category']} · {product['brand']}")
                    st.markdown(f"### ₹{float(product['price']):,.0f}")
                    product_id = int(product["product_id"])
                    if st.button("Remove from wishlist", key=f"saved_remove_{product_id}", use_container_width=True):
                        st.session_state.wishlist.remove(product_id)
                        st.rerun()

with about_tab:
    st.markdown("<div class='section-eyebrow'>PROJECT OVERVIEW</div><div class='section-title'>How Findly works</div>", unsafe_allow_html=True)
    st.write(
        "Findly is an NLP-based e-commerce product discovery prototype. "
        "It compares the meaning of a natural-language query with product text, "
        "then combines semantic similarity and keyword similarity to rank catalogue items."
    )
    about_cols = st.columns(2)
    with about_cols[0]:
        st.markdown("#### Search pipeline")
        st.write("1. Product information is loaded from the CSV catalogue.")
        st.write("2. Product fields are combined into searchable text.")
        st.write("3. Sentence Transformers creates semantic embeddings.")
        st.write("4. TF-IDF creates a keyword index.")
        st.write("5. The two similarity signals are combined for first-stage ranking.")
        st.write("6. Optionally, a Cross-Encoder reranks candidate query-product pairs.")
    with about_cols[1]:
        st.markdown("#### Technology stack")
        st.write("- Python and Streamlit")
        st.write("- Sentence Transformers: all-MiniLM-L6-v2")
        st.write("- Scikit-learn: TF-IDF and cosine similarity")
        st.write("- Sentence Transformers CrossEncoder: optional second-stage reranking")
        st.write("- Pandas and NumPy for data handling")
        st.write("- CSV catalogue with optional product images")
    st.info(
        "This is a prototype over the products in the local catalogue. "
        "It does not search Amazon, Flipkart, or live retailer inventory."
    )


# ============================================================
# 9. FOOTER
# ============================================================
st.markdown(
    "<div class='footer-note'>FINDLY AI · Semantic E-Commerce Search · Built with NLP, Python & Streamlit</div>",
    unsafe_allow_html=True,
)
