
import json
import re
from urllib.request import urlopen

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from streamlit_folium import st_folium
from streamlit_plotly_events import plotly_events

st.set_page_config(
    page_title="서울, 처음이니? : 어디서 자취할까?",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISTRICTS = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
    "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
    "용산구","은평구","종로구","중구","중랑구"
]

GEOJSON_URL = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"

SEOUL_RENT_FALLBACK = {
  "avg_monthly_rent": 74.5,
  "median_monthly_rent": 55.0,
  "monthly_count": 661645
}

DISTRICT_RENT_FALLBACK = {
  "강남구": {"avg_monthly_rent": 131.7, "median_monthly_rent": 90.0, "avg_deposit": 21681.8, "monthly_count": 40200},
  "강동구": {"avg_monthly_rent": 60.4, "median_monthly_rent": 48.0, "avg_deposit": 10152.1, "monthly_count": 35426},
  "강북구": {"avg_monthly_rent": 54.4, "median_monthly_rent": 50.0, "avg_deposit": 3379.9, "monthly_count": 13578},
  "강서구": {"avg_monthly_rent": 56.3, "median_monthly_rent": 54.0, "avg_deposit": 7715.4, "monthly_count": 46463},
  "관악구": {"avg_monthly_rent": 54.5, "median_monthly_rent": 50.0, "avg_deposit": 4833.3, "monthly_count": 45896},
  "광진구": {"avg_monthly_rent": 75.8, "median_monthly_rent": 65.0, "avg_deposit": 8408.9, "monthly_count": 22839},
  "구로구": {"avg_monthly_rent": 52.2, "median_monthly_rent": 46.0, "avg_deposit": 6033.4, "monthly_count": 24860},
  "금천구": {"avg_monthly_rent": 52.2, "median_monthly_rent": 50.0, "avg_deposit": 6627.1, "monthly_count": 18744},
  "노원구": {"avg_monthly_rent": 56.9, "median_monthly_rent": 48.0, "avg_deposit": 6815.8, "monthly_count": 17668},
  "도봉구": {"avg_monthly_rent": 54.5, "median_monthly_rent": 45.0, "avg_deposit": 3855.8, "monthly_count": 12373},
  "동대문구": {"avg_monthly_rent": 65.9, "median_monthly_rent": 55.0, "avg_deposit": 6679.4, "monthly_count": 24731},
  "동작구": {"avg_monthly_rent": 65.9, "median_monthly_rent": 57.0, "avg_deposit": 7631.6, "monthly_count": 26126},
  "마포구": {"avg_monthly_rent": 92.1, "median_monthly_rent": 70.0, "avg_deposit": 8909.2, "monthly_count": 28505},
  "서대문구": {"avg_monthly_rent": 66.4, "median_monthly_rent": 57.0, "avg_deposit": 6273.9, "monthly_count": 19089},
  "서초구": {"avg_monthly_rent": 127.2, "median_monthly_rent": 84.0, "avg_deposit": 25223.9, "monthly_count": 21351},
  "성동구": {"avg_monthly_rent": 89.9, "median_monthly_rent": 70.0, "avg_deposit": 12918.7, "monthly_count": 18222},
  "성북구": {"avg_monthly_rent": 58.7, "median_monthly_rent": 50.0, "avg_deposit": 5100.0, "monthly_count": 22348},
  "송파구": {"avg_monthly_rent": 86.9, "median_monthly_rent": 68.0, "avg_deposit": 14084.1, "monthly_count": 40044},
  "양천구": {"avg_monthly_rent": 63.7, "median_monthly_rent": 53.0, "avg_deposit": 10255.1, "monthly_count": 20325},
  "영등포구": {"avg_monthly_rent": 86.4, "median_monthly_rent": 70.0, "avg_deposit": 10709.9, "monthly_count": 36689},
  "용산구": {"avg_monthly_rent": 119.4, "median_monthly_rent": 90.0, "avg_deposit": 13674.3, "monthly_count": 17458},
  "은평구": {"avg_monthly_rent": 59.1, "median_monthly_rent": 53.0, "avg_deposit": 8069.1, "monthly_count": 34761},
  "종로구": {"avg_monthly_rent": 91.4, "median_monthly_rent": 70.0, "avg_deposit": 8147.9, "monthly_count": 19059},
  "중구": {"avg_monthly_rent": 106.8, "median_monthly_rent": 85.0, "avg_deposit": 9957.7, "monthly_count": 20562},
  "중랑구": {"avg_monthly_rent": 51.1, "median_monthly_rent": 45.0, "avg_deposit": 6382.3, "monthly_count": 21060}
}

DISTRICT_CENTERS = {
    "강남구": [37.5172, 127.0473], "강동구": [37.5301, 127.1238], "강북구": [37.6397, 127.0257],
    "강서구": [37.5509, 126.8495], "관악구": [37.4784, 126.9516], "광진구": [37.5385, 127.0822],
    "구로구": [37.4954, 126.8874], "금천구": [37.4602, 126.9006], "노원구": [37.6542, 127.0568],
    "도봉구": [37.6688, 127.0471], "동대문구": [37.5744, 127.0395], "동작구": [37.5124, 126.9393],
    "마포구": [37.5663, 126.9014], "서대문구": [37.5791, 126.9368], "서초구": [37.4837, 127.0324],
    "성동구": [37.5634, 127.0366], "성북구": [37.5894, 127.0167], "송파구": [37.5145, 127.1059],
    "양천구": [37.5169, 126.8664], "영등포구": [37.5264, 126.8962], "용산구": [37.5326, 126.9900],
    "은평구": [37.6027, 126.9291], "종로구": [37.5735, 126.9788], "중구": [37.5640, 126.9970],
    "중랑구": [37.6063, 127.0927]
}

CATEGORY_COLORS = {
    "미술관/갤러리": "#F87171",
    "공연장": "#60A5FA",
    "박물관/기념관": "#34D399",
    "문화원": "#FBBF24",
    "문화예술회관": "#A78BFA",
    "도서관": "#22C55E",
    "기타": "#94A3B8",
}

st.markdown("""
<style>
:root {
  --bg: #F6F8FC;
  --surface: #FFFFFF;
  --text: #14213D;
  --muted: #667085;
  --border: #E5E7EB;
  --primary: #0F62FE;
  --secondary: #7C3AED;
  --good: #10B981;
  --warn: #F59E0B;
}
.stApp {
    background: linear-gradient(180deg, #F7F9FC 0%, #EDF3FF 100%);
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1300px;
}
.hero {
    background: linear-gradient(135deg, rgba(15,98,254,0.98), rgba(124,58,237,0.96));
    color: white;
    border-radius: 24px;
    padding: 28px 30px 24px 30px;
    box-shadow: 0 18px 40px rgba(15,98,254,0.15);
    margin-bottom: 18px;
}
.hero h1 {
    font-size: 2rem;
    margin: 0 0 6px 0;
}
.hero p {
    margin: 0;
    opacity: 0.95;
    font-size: 1rem;
}
.section-card {
    background: rgba(255,255,255,0.95);
    border: 1px solid rgba(229,231,235,0.8);
    border-radius: 22px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.05);
}
.metric-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 16px 18px;
    box-shadow: 0 6px 18px rgba(15,23,42,0.04);
    min-height: 112px;
}
.metric-label {
    color: #667085;
    font-size: 0.88rem;
    margin-bottom: 4px;
}
.metric-value {
    color: #111827;
    font-size: 1.75rem;
    font-weight: 800;
    line-height: 1.2;
}
.metric-sub {
    color: #667085;
    font-size: 0.85rem;
}
.rank-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 8px 22px rgba(15,23,42,0.05);
    min-height: 170px;
}
.rank-badge {
    display:inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: #EEF4FF;
    color: #0F62FE;
    font-weight: 700;
    font-size: 0.8rem;
    margin-bottom: 8px;
}
.rank-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0F172A;
}
.rank-score {
    font-size: 1.9rem;
    font-weight: 800;
    color: #0F62FE;
}
.small-muted { color:#667085; font-size:0.84rem; }
.pill {
    display:inline-block;
    border-radius:999px;
    padding: 4px 10px;
    margin: 0 6px 6px 0;
    background:#F3F4F6;
    color:#334155;
    font-size:0.8rem;
    font-weight:600;
}
.selected-chip {
    display:inline-block;
    border-radius:999px;
    padding:6px 12px;
    background:#E0EAFF;
    color:#0F62FE;
    font-weight:700;
    margin-top:2px;
}
.guide {
    background:#F8FAFC;
    border:1px solid #E2E8F0;
    border-radius:16px;
    padding:12px 14px;
    color:#475467;
    font-size:0.88rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f7faff 100%);
}
div[data-testid="stVerticalBlock"] div:has(> div.map-hint) {
    margin-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_csv_auto(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding_errors="ignore")


@st.cache_data(show_spinner=False)
def read_excel_auto(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def extract_gu(text: str):
    if pd.isna(text):
        return None
    text = str(text)
    m = re.search(r"(강남구|강동구|강북구|강서구|관악구|광진구|구로구|금천구|노원구|도봉구|동대문구|동작구|마포구|서대문구|서초구|성동구|성북구|송파구|양천구|영등포구|용산구|은평구|종로구|중구|중랑구)", text)
    return m.group(1) if m else None


@st.cache_data(show_spinner=False)
def load_geojson():
    with urlopen(GEOJSON_URL, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


@st.cache_data(show_spinner=False)
def load_datasets():
    culture = read_csv_auto("서울시 문화공간 정보.csv")
    library = read_csv_auto("서울시 공공도서관 현황정보.csv")
    subway = read_csv_auto("서울교통공사_역주소 및 전화번호.csv")
    parks = read_excel_auto("서울시 주요 공원현황(2026 상반기).xlsx")
    price = read_csv_auto("생필품 농수축산물 가격 정보(2024년).csv")

    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    culture = culture[culture["자치구"].isin(DISTRICTS)].copy()
    culture["위도"] = pd.to_numeric(culture["위도"], errors="coerce")
    culture["경도"] = pd.to_numeric(culture["경도"], errors="coerce")
    culture["주제분류"] = culture["주제분류"].fillna("기타").replace({"nan": "기타"})

    library["자치구"] = library["구명"].astype(str).str.strip()
    library = library[library["자치구"].isin(DISTRICTS)].copy()
    library["위도"] = pd.to_numeric(library["위도"], errors="coerce")
    library["경도"] = pd.to_numeric(library["경도"], errors="coerce")

    subway["자치구"] = subway["도로명주소"].apply(extract_gu)
    subway["자치구"] = subway["자치구"].fillna(subway["구주소"].apply(extract_gu))
    subway = subway[subway["자치구"].isin(DISTRICTS)].copy()

    parks["자치구"] = parks["지역"].astype(str).str.strip()
    parks = parks[parks["자치구"].isin(DISTRICTS)].copy()
    parks["위도"] = pd.to_numeric(parks["Y좌표(WGS84)"], errors="coerce")
    parks["경도"] = pd.to_numeric(parks["X좌표(WGS84)"], errors="coerce")

    price["자치구"] = price["자치구 이름"].astype(str).str.strip()
    price = price[price["자치구"].isin(DISTRICTS)].copy()
    price["가격(원)"] = pd.to_numeric(price["가격(원)"], errors="coerce")

    return culture, library, subway, parks, price


@st.cache_data(show_spinner=False)
def get_rent_summary():
    try:
        rent = read_csv_auto("서울특별시_전월세가_2025.csv")
        rent["임대료(만원)"] = pd.to_numeric(rent["임대료(만원)"], errors="coerce")
        rent["보증금(만원)"] = pd.to_numeric(rent["보증금(만원)"], errors="coerce")
        month = rent[(rent["전월세구분"] == "월세") & (rent["임대료(만원)"] > 0)].copy()
        district = (
            month.groupby("자치구명")
            .agg(
                avg_monthly_rent=("임대료(만원)", "mean"),
                median_monthly_rent=("임대료(만원)", "median"),
                avg_deposit=("보증금(만원)", "mean"),
                monthly_count=("임대료(만원)", "size"),
            )
            .round(1)
            .reset_index()
            .rename(columns={"자치구명": "자치구"})
        )
        overall = {
            "avg_monthly_rent": round(float(month["임대료(만원)"].mean()), 1),
            "median_monthly_rent": round(float(month["임대료(만원)"].median()), 1),
            "monthly_count": int(len(month)),
        }
        return district, overall, True
    except Exception:
        district = pd.DataFrame(
            [{"자치구": k, **v} for k, v in DISTRICT_RENT_FALLBACK.items()]
        )
        return district, SEOUL_RENT_FALLBACK, False


def minmax_inverse(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.ones(len(s)), index=s.index)
    return 1 - (s - s.min()) / (s.max() - s.min())


def minmax_positive(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if s.max() == s.min():
        return pd.Series(np.ones(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


@st.cache_data(show_spinner=False)
def build_summary(culture, library, subway, parks, price, rent_summary):
    base = pd.DataFrame({"자치구": DISTRICTS})

    latest_month = None
    try:
        parsed = pd.to_datetime(price["년도-월"], format="%b-%y", errors="coerce")
        if parsed.notna().any():
            latest_month = parsed.max()
            price_ref = price[parsed == latest_month].copy()
        else:
            price_ref = price.copy()
    except Exception:
        price_ref = price.copy()

    culture_count = culture.groupby("자치구").size().rename("문화공간수")
    culture_type_count = culture.groupby("자치구")["주제분류"].nunique().rename("문화다양성")
    library_count = library.groupby("자치구").size().rename("도서관수")
    park_count = parks.groupby("자치구").size().rename("공원수")
    station_count = subway.groupby("자치구")["역명"].nunique().rename("지하철역수")
    line_count = subway.groupby("자치구")["호선"].nunique().rename("호선수")
    price_mean = price_ref.groupby("자치구")["가격(원)"].mean().round().rename("생활물가평균")

    summary = (
        base.set_index("자치구")
        .join([culture_count, culture_type_count, library_count, park_count, station_count, line_count, price_mean])
        .fillna(0)
        .reset_index()
    )

    summary["문화공간수"] = summary["문화공간수"].astype(int)
    summary["문화다양성"] = summary["문화다양성"].astype(int)
    summary["도서관수"] = summary["도서관수"].astype(int)
    summary["공원수"] = summary["공원수"].astype(int)
    summary["지하철역수"] = summary["지하철역수"].astype(int)
    summary["호선수"] = summary["호선수"].astype(int)
    summary["생활물가평균"] = summary["생활물가평균"].astype(int)

    summary = summary.merge(rent_summary, on="자치구", how="left")

    top_categories = (
        culture.groupby(["자치구", "주제분류"]).size().reset_index(name="개수")
        .sort_values(["자치구", "개수"], ascending=[True, False])
    )
    top_text = {}
    for gu in DISTRICTS:
        temp = top_categories[top_categories["자치구"] == gu].head(3)
        top_text[gu] = " · ".join([f"{r['주제분류']} {int(r['개수'])}" for _, r in temp.iterrows()]) if not temp.empty else "문화 데이터 없음"
    summary["많은문화생활"] = summary["자치구"].map(top_text)

    line_text = subway.groupby("자치구")["호선"].apply(lambda s: ", ".join(sorted(s.dropna().astype(str).unique()))).to_dict()
    summary["주요호선"] = summary["자치구"].map(line_text).fillna("-")

    if latest_month is not None:
        price_month_label = latest_month.strftime("%Y-%m")
    else:
        price_month_label = "전체 기간 평균"

    return summary, price_month_label


def score_candidates(df, weights):
    work = df.copy()

    work["월세점수"] = minmax_inverse(work["avg_monthly_rent"])
    work["물가점수"] = minmax_inverse(work["생활물가평균"])
    work["교통점수"] = (
        minmax_positive(work["지하철역수"]) * 0.6 + minmax_positive(work["호선수"]) * 0.4
    )
    work["문화점수"] = (
        minmax_positive(work["문화공간수"]) * 0.7 + minmax_positive(work["문화다양성"]) * 0.3
    )
    work["공원점수"] = minmax_positive(work["공원수"])
    work["도서관점수"] = minmax_positive(work["도서관수"])

    total = sum(weights.values())
    if total == 0:
        weights = {k: 1 for k in weights}
        total = len(weights)

    work["추천점수"] = (
        work["월세점수"] * weights["월세"]
        + work["물가점수"] * weights["물가"]
        + work["교통점수"] * weights["교통"]
        + work["문화점수"] * weights["문화"]
        + work["공원점수"] * weights["공원"]
        + work["도서관점수"] * weights["도서관"]
    ) / total * 100

    return work.sort_values(["추천점수", "월세점수"], ascending=[False, False])


def format_money(value, suffix="만원"):
    if pd.isna(value):
        return "-"
    return f"{value:,.1f}{suffix}"


def comparison_text(district_avg, seoul_avg):
    if pd.isna(district_avg):
        return "비교 데이터 없음"
    delta = district_avg - seoul_avg
    pct = abs(delta) / seoul_avg * 100 if seoul_avg else 0
    if delta < 0:
        return f"서울 평균보다 {abs(delta):.1f}만원 저렴 ({pct:.0f}%↓)"
    if delta > 0:
        return f"서울 평균보다 {abs(delta):.1f}만원 높음 ({pct:.0f}%↑)"
    return "서울 평균과 비슷함"


def render_metric_card(label, value, sub):
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


culture, library, subway, parks, price = load_datasets()
rent_summary, seoul_rent, used_uploaded_rent = get_rent_summary()
summary, price_month_label = build_summary(culture, library, subway, parks, price, rent_summary)

if "selected_gu" not in st.session_state:
    st.session_state.selected_gu = "마포구"

preset = st.sidebar.selectbox(
    "추천 모드",
    ["균형형", "가성비 우선", "교통 우선", "문화생활 우선", "공원/힐링 우선", "직접 설정"],
    index=0,
)

preset_weights = {
    "균형형": {"월세": 4, "물가": 3, "교통": 4, "문화": 4, "공원": 2, "도서관": 2},
    "가성비 우선": {"월세": 5, "물가": 5, "교통": 3, "문화": 2, "공원": 1, "도서관": 2},
    "교통 우선": {"월세": 3, "물가": 2, "교통": 5, "문화": 3, "공원": 1, "도서관": 1},
    "문화생활 우선": {"월세": 2, "물가": 2, "교통": 3, "문화": 5, "공원": 3, "도서관": 1},
    "공원/힐링 우선": {"월세": 2, "물가": 2, "교통": 2, "문화": 2, "공원": 5, "도서관": 2},
    "직접 설정": {"월세": 4, "물가": 3, "교통": 4, "문화": 4, "공원": 2, "도서관": 2},
}
default_weights = preset_weights[preset]

st.sidebar.markdown('<div class="guide"><b>중요도 가이드</b><br>1 = 크게 중요하지 않음 · 3 = 보통 · 5 = 매우 중요함<br>예산을 특히 중시하면 <b>월세</b>와 <b>생활물가</b>를 높이고, 놀거리와 전시를 좋아하면 <b>문화생활</b>을 높여 보세요.</div>', unsafe_allow_html=True)
weights = {
    "월세": st.sidebar.slider("월세", 0, 5, default_weights["월세"]),
    "물가": st.sidebar.slider("생활물가", 0, 5, default_weights["물가"]),
    "교통": st.sidebar.slider("지하철/교통", 0, 5, default_weights["교통"]),
    "문화": st.sidebar.slider("문화생활", 0, 5, default_weights["문화"]),
    "공원": st.sidebar.slider("공원/녹지", 0, 5, default_weights["공원"]),
    "도서관": st.sidebar.slider("도서관/공부환경", 0, 5, default_weights["도서관"]),
}

budget_cap = st.sidebar.slider(
    "희망 월세 상한 (만원)",
    40, 140, 85,
    help="자치구 평균 월세 기준으로 필터링됩니다."
)
preferred_line = st.sidebar.selectbox(
    "선호 지하철 호선",
    ["상관없음"] + sorted(subway["호선"].dropna().astype(str).unique().tolist())
)

ranked = score_candidates(summary, weights)
candidates = ranked[ranked["avg_monthly_rent"] <= budget_cap].copy()
if preferred_line != "상관없음":
    candidates = candidates[candidates["주요호선"].str.contains(preferred_line, na=False)].copy()
if candidates.empty:
    candidates = ranked.copy()

selected_gu_from_select = st.sidebar.selectbox(
    "직접 보고 싶은 자치구",
    DISTRICTS,
    index=DISTRICTS.index(st.session_state.selected_gu) if st.session_state.selected_gu in DISTRICTS else 0
)
st.session_state.selected_gu = selected_gu_from_select

top5 = candidates.head(5).copy()
selected_row = ranked[ranked["자치구"] == st.session_state.selected_gu].iloc[0]

st.markdown(
    """
    <div class="hero">
      <h1>서울, 처음이니? : 어디서 자취할까?</h1>
      <p>서울 25개 자치구의 월세, 생활물가, 지하철, 공원, 문화공간, 도서관 데이터를 한눈에 비교해서
      <b>내 취향에 맞는 자취 지역</b>을 찾는 추천 플랫폼입니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("서울 전체 평균 월세", f"{seoul_rent['avg_monthly_rent']:.1f}만원", f"월세 계약 {seoul_rent['monthly_count']:,}건 기준")
with m2:
    render_metric_card("현재 선택 지역", f"{selected_row['자치구']}", comparison_text(selected_row['avg_monthly_rent'], seoul_rent["avg_monthly_rent"]))
with m3:
    render_metric_card("선택 지역 평균 월세", f"{selected_row['avg_monthly_rent']:.1f}만원", f"중앙값 {selected_row['median_monthly_rent']:.1f}만원")
with m4:
    render_metric_card("선택 지역 생활물가 평균", f"{int(round(selected_row['생활물가평균'])):,}원", f"{price_month_label} 기준 평균 가격")

tab1, tab2, tab3, tab4 = st.tabs(["추천 결과", "서울 지도", "문화생활", "데이터 비교"])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("당신에게 맞는 자취 추천 TOP 5")
    st.caption("현재 설정한 중요도와 월세 상한을 바탕으로 계산했습니다.")
    cols = st.columns(5)
    medals = ["🥇", "🥈", "🥉", "4위", "5위"]
    for idx, (_, row) in enumerate(top5.iterrows()):
        with cols[idx]:
            cheap_text = comparison_text(row["avg_monthly_rent"], seoul_rent["avg_monthly_rent"])
            st.markdown(
                f"""
                <div class="rank-card">
                  <div class="rank-badge">{medals[idx]}</div>
                  <div class="rank-title">{row['자치구']}</div>
                  <div class="rank-score">{row['추천점수']:.1f}</div>
                  <div class="small-muted">추천 점수</div>
                  <hr style="border:none;border-top:1px solid #EEF2F7;margin:10px 0 12px 0;">
                  <div class="small-muted">평균 월세 <b>{row['avg_monthly_rent']:.1f}만원</b></div>
                  <div class="small-muted">{cheap_text}</div>
                  <div class="small-muted" style="margin-top:8px;">주요 호선: {row['주요호선']}</div>
                  <div class="small-muted" style="margin-top:8px;">문화생활: {row['많은문화생활']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"{selected_row['자치구']} 한눈에 보기")
        st.markdown(f'<span class="selected-chip">{selected_row["자치구"]}</span>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("지하철 접근성", f"{int(selected_row['지하철역수'])}개 역", f"호선 {int(selected_row['호선수'])}개")
        with c2:
            render_metric_card("문화생활", f"{int(selected_row['문화공간수'])}곳", selected_row["많은문화생활"])
        with c3:
            render_metric_card("공원·도서관", f"공원 {int(selected_row['공원수'])} · 도서관 {int(selected_row['도서관수'])}", "생활 인프라 요약")

        radar_cols = ["월세점수", "물가점수", "교통점수", "문화점수", "공원점수", "도서관점수"]
        current = ranked[ranked["자치구"] == st.session_state.selected_gu].iloc[0]
        radar_fig = go.Figure()
        radar_fig.add_trace(
            go.Scatterpolar(
                r=[current[c] * 100 for c in radar_cols],
                theta=["월세", "물가", "교통", "문화", "공원", "도서관"],
                fill="toself",
                name=st.session_state.selected_gu,
                line=dict(color="#0F62FE", width=3),
                fillcolor="rgba(15,98,254,0.22)",
            )
        )
        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10))),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=360,
        )
        st.plotly_chart(radar_fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("추천 지역 순위표")
        view_cols = ["자치구", "추천점수", "avg_monthly_rent", "생활물가평균", "지하철역수", "문화공간수", "공원수", "도서관수"]
        show = candidates[view_cols].copy()
        show.columns = ["자치구", "추천점수", "평균월세(만원)", "생활물가평균(원)", "지하철역수", "문화공간수", "공원수", "도서관수"]
        show["추천점수"] = show["추천점수"].round(1)
        show["생활물가평균(원)"] = show["생활물가평균(원)"].round().astype(int)
        st.dataframe(show, use_container_width=True, hide_index=True, height=415)
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("서울 자치구 지도")
    st.caption("지도를 클릭하면 해당 자치구를 현재 선택 지역으로 바꿉니다. 지도가 불안정하면 아래 목록 선택으로도 동일하게 볼 수 있습니다.")
    try:
        geojson = load_geojson()
        fig = px.choropleth_mapbox(
            ranked,
            geojson=geojson,
            locations="자치구",
            featureidkey="properties.name",
            color="추천점수",
            color_continuous_scale="Blues",
            mapbox_style="carto-positron",
            center={"lat": 37.56, "lon": 126.99},
            zoom=9.8,
            opacity=0.72,
            hover_name="자치구",
            hover_data={
                "추천점수": ":.1f",
                "avg_monthly_rent": ":.1f",
                "생활물가평균": True,
                "지하철역수": True,
                "문화공간수": True,
                "공원수": True,
            },
            height=620,
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(title="추천점수"),
        )
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>추천점수 %{z:.1f}<br>평균월세 %{customdata[0]:.1f}만원<br>생활물가 %{customdata[1]:,}원<br>지하철역 %{customdata[2]}개<br>문화공간 %{customdata[3]}곳<br>공원 %{customdata[4]}곳<extra></extra>"
        )
        selected_points = plotly_events(
            fig,
            click_event=True,
            hover_event=False,
            select_event=False,
            override_height=620,
            key="district_map"
        )
        if selected_points:
            loc = selected_points[0].get("pointIndex")
            if loc is not None:
                clicked_gu = ranked.iloc[loc]["자치구"]
                st.session_state.selected_gu = clicked_gu
                st.success(f"{clicked_gu}를 선택했어요. 아래 상세 정보가 갱신됩니다.")
                selected_row = ranked[ranked["자치구"] == st.session_state.selected_gu].iloc[0]
        else:
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.warning("구역 지도를 불러오지 못해, 대체 지도로 보여드릴게요.")
        fmap = folium.Map(location=[37.56, 126.99], zoom_start=11, tiles="CartoDB positron")
        for _, row in ranked.iterrows():
            lat, lon = DISTRICT_CENTERS[row["자치구"]]
            popup = folium.Popup(
                f"<b>{row['자치구']}</b><br>추천점수 {row['추천점수']:.1f}<br>평균월세 {row['avg_monthly_rent']:.1f}만원<br>문화공간 {int(row['문화공간수'])}곳",
                max_width=250,
            )
            folium.CircleMarker(
                location=[lat, lon],
                radius=8 + row["추천점수"] / 25,
                color="#0F62FE",
                fill=True,
                fill_opacity=0.75,
                popup=popup,
            ).add_to(fmap)
        st_folium(fmap, width=1200, height=620)
    st.markdown("</div>", unsafe_allow_html=True)

    selected_row = ranked[ranked["자치구"] == st.session_state.selected_gu].iloc[0]
    st.markdown('<div class="section-card" style="margin-top:16px;">', unsafe_allow_html=True)
    st.subheader(f"{st.session_state.selected_gu} 상세 정보")
    col_a, col_b = st.columns([1.1, 0.9])
    with col_a:
        station_list = subway[subway["자치구"] == st.session_state.selected_gu]["역명"].dropna().astype(str).unique().tolist()
        st.markdown(f"**평균 월세**: {selected_row['avg_monthly_rent']:.1f}만원")
        st.markdown(f"**서울 평균 대비**: {comparison_text(selected_row['avg_monthly_rent'], seoul_rent['avg_monthly_rent'])}")
        st.markdown(f"**생활물가 평균**: {int(round(selected_row['생활물가평균'])):,}원")
        st.markdown(f"**지하철역**: {int(selected_row['지하철역수'])}개 / **주요 호선**: {selected_row['주요호선']}")
        st.markdown(f"**역 목록**: {', '.join(station_list[:12]) if station_list else '-'}")
    with col_b:
        bar_df = pd.DataFrame({
            "항목": ["문화공간", "도서관", "공원", "지하철역"],
            "개수": [
                int(selected_row["문화공간수"]),
                int(selected_row["도서관수"]),
                int(selected_row["공원수"]),
                int(selected_row["지하철역수"]),
            ],
        })
        bar_fig = px.bar(
            bar_df,
            x="항목",
            y="개수",
            text="개수",
            color="항목",
            color_discrete_sequence=["#0F62FE", "#7C3AED", "#10B981", "#F59E0B"],
            height=320,
        )
        bar_fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(bar_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(f"{st.session_state.selected_gu}에서 즐길 수 있는 문화생활")
    selected_culture = culture[culture["자치구"] == st.session_state.selected_gu].copy()
    if selected_culture.empty:
        st.info("이 지역의 문화공간 데이터가 없습니다.")
    else:
        category_counts = (
            selected_culture["주제분류"].value_counts().rename_axis("주제분류").reset_index(name="개수")
        )
        c1, c2 = st.columns([0.9, 1.1])
        with c1:
            pie_fig = px.pie(
                category_counts,
                names="주제분류",
                values="개수",
                hole=0.45,
                color="주제분류",
                color_discrete_map=CATEGORY_COLORS,
                height=360,
            )
            pie_fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
            st.plotly_chart(pie_fig, use_container_width=True)
        with c2:
            st.markdown("**많은 문화생활 유형**")
            for _, row in category_counts.head(6).iterrows():
                st.markdown(f'<span class="pill">{row["주제분류"]} {int(row["개수"])}곳</span>', unsafe_allow_html=True)

            free_ratio = (
                (selected_culture["무료구분"].astype(str).str.contains("무료", na=False).mean() * 100)
                if "무료구분" in selected_culture.columns else 0
            )
            st.markdown(f"**무료 이용 가능 비중**: 약 {free_ratio:.0f}%")
            st.markdown(f"**대표 문화공간 예시**: " + ", ".join(selected_culture["문화시설명"].dropna().astype(str).head(8).tolist()))

        detail_cols = ["주제분류", "문화시설명", "주소", "무료구분", "전화번호", "지하철"]
        exist_cols = [c for c in detail_cols if c in selected_culture.columns]
        st.markdown("**문화공간 상세 목록**")
        st.dataframe(selected_culture[exist_cols].sort_values("주제분류"), use_container_width=True, hide_index=True, height=400)
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("서울 전체 자치구 비교")
    compare_cols = st.columns([1.1, 0.9])
    with compare_cols[0]:
        scatter = px.scatter(
            ranked,
            x="avg_monthly_rent",
            y="추천점수",
            size="문화공간수",
            color="생활물가평균",
            hover_name="자치구",
            color_continuous_scale="Viridis",
            height=430,
            labels={
                "avg_monthly_rent": "평균 월세(만원)",
                "추천점수": "추천점수",
                "생활물가평균": "생활물가 평균(원)",
            }
        )
        scatter.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(scatter, use_container_width=True)
    with compare_cols[1]:
        rent_order = ranked.sort_values("avg_monthly_rent")
        line = px.bar(
            rent_order,
            x="자치구",
            y="avg_monthly_rent",
            color="avg_monthly_rent",
            color_continuous_scale="Blues",
            height=430,
            labels={"avg_monthly_rent": "평균 월세(만원)"},
        )
        line.update_layout(margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(line, use_container_width=True)
    st.caption(f"생활물가 평균은 {price_month_label} 기준 가격 데이터를 자치구별로 평균한 값이며, 정수 단위로 반올림해 표시했습니다.")
    st.caption(f"월세 데이터는 {'업로드한 전월세 CSV를 직접 읽어 계산' if used_uploaded_rent else '업로드 때 계산한 요약값을 코드에 내장해 사용'}했습니다.")
    st.markdown("</div>", unsafe_allow_html=True)
