
import json
import math
import re
from urllib.request import urlopen

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.features import GeoJsonPopup, GeoJsonTooltip
from sklearn.preprocessing import MinMaxScaler
from streamlit_folium import st_folium

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="서울, 처음이니? : 어디서 자취할까?",
    page_icon="🏠",
    layout="wide",
)

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.15rem;
}
.sub-title {
    color: #4b5563;
    font-size: 1rem;
    margin-bottom: 1.2rem;
}
.hero {
    background: linear-gradient(135deg, #fff7fb 0%, #f7f7ff 45%, #eef8ff 100%);
    border: 1px solid #ececf4;
    border-radius: 22px;
    padding: 1.2rem 1.3rem 1.0rem 1.3rem;
    margin-bottom: 1rem;
}
.metric-card {
    background: white;
    border: 1px solid #ececf4;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 6px 20px rgba(20,20,43,0.04);
    height: 100%;
}
.metric-label {
    color: #6b7280;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
}
.metric-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #111827;
}
.metric-help {
    color: #6b7280;
    font-size: 0.82rem;
    margin-top: 0.35rem;
}
.section-title {
    font-size: 1.15rem;
    font-weight: 800;
    margin: 0.6rem 0 0.7rem 0;
}
.rec-card {
    background: white;
    border: 1px solid #ececf4;
    border-radius: 20px;
    padding: 1rem 1rem 0.9rem 1rem;
    box-shadow: 0 8px 22px rgba(20,20,43,0.05);
    margin-bottom: 0.9rem;
}
.rec-rank {
    display: inline-block;
    background: #111827;
    color: white;
    border-radius: 999px;
    padding: 0.23rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 0.55rem;
}
.rec-name {
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}
.rec-score {
    font-size: 1.6rem;
    font-weight: 800;
    color: #2563eb;
}
.tag {
    display: inline-block;
    padding: 0.22rem 0.58rem;
    margin: 0.12rem 0.2rem 0.12rem 0;
    border-radius: 999px;
    background: #f3f4f6;
    color: #111827;
    font-size: 0.82rem;
}
.small-note {
    color: #6b7280;
    font-size: 0.83rem;
}
.detail-card {
    background: white;
    border: 1px solid #ececf4;
    border-radius: 20px;
    padding: 1rem 1rem;
    box-shadow: 0 8px 22px rgba(20,20,43,0.05);
}
.sidebar-guide {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 0.85rem 0.9rem;
    font-size: 0.86rem;
    color: #374151;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 유틸
# -----------------------------
FALLBACK_RENT = {
    "강남구": 95, "강동구": 72, "강북구": 62, "강서구": 68, "관악구": 60,
    "광진구": 78, "구로구": 63, "금천구": 58, "노원구": 60, "도봉구": 55,
    "동대문구": 68, "동작구": 75, "마포구": 85, "서대문구": 70, "서초구": 92,
    "성동구": 80, "성북구": 65, "송파구": 88, "양천구": 70, "영등포구": 75,
    "용산구": 82, "은평구": 63, "종로구": 75, "중구": 78, "중랑구": 60,
}

SEOUL_DISTRICTS = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
    "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
    "용산구","은평구","종로구","중구","중랑구"
]

DISTRICT_CENTER = {
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

def safe_round_int(value):
    if pd.isna(value):
        return None
    return int(round(float(value)))

@st.cache_data(show_spinner=False)
def read_csv_flexible(path: str) -> pd.DataFrame:
    last_error = None
    for enc in ["utf-8", "utf-8-sig", "cp949", "euc-kr"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_error = e
    raise last_error

@st.cache_data(show_spinner=False)
def read_excel_flexible(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

def extract_district(text):
    if pd.isna(text):
        return None
    text = str(text)
    match = re.search(r"(강남구|강동구|강북구|강서구|관악구|광진구|구로구|금천구|노원구|도봉구|동대문구|동작구|마포구|서대문구|서초구|성동구|성북구|송파구|양천구|영등포구|용산구|은평구|종로구|중구|중랑구)", text)
    return match.group(1) if match else None

def categorize_culture(topic):
    if pd.isna(topic):
        return "기타"
    t = str(topic)
    if "미술" in t or "갤러리" in t:
        return "미술관·갤러리"
    if "박물관" in t or "기념관" in t:
        return "박물관·기념관"
    if "공연" in t or "극장" in t or "연극" in t or "오페라" in t:
        return "공연장"
    if "도서관" in t:
        return "도서관"
    if "문화원" in t or "문화의집" in t or "문화센터" in t or "예술회관" in t:
        return "문화센터·예술회관"
    if "영화" in t or "시네마" in t:
        return "영화관"
    return t if len(t) <= 14 else "기타"

@st.cache_data(show_spinner=False)
def load_geojson():
    url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"
    with urlopen(url, timeout=10) as response:
        return json.load(response)

@st.cache_data(show_spinner=False)
def load_all_data():
    culture = read_csv_flexible("서울시 문화공간 정보.csv").copy()
    library = read_csv_flexible("서울시 공공도서관 현황정보.csv").copy()
    subway = read_csv_flexible("서울교통공사_역주소 및 전화번호.csv").copy()
    parks = read_excel_flexible("서울시 주요 공원현황(2026 상반기).xlsx").copy()
    prices = read_csv_flexible("생필품 농수축산물 가격 정보(2024년).csv").copy()

    # 문화공간
    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    culture = culture[culture["자치구"].isin(SEOUL_DISTRICTS)]
    culture["문화카테고리"] = culture["주제분류"].apply(categorize_culture)
    culture["위도"] = pd.to_numeric(culture["위도"], errors="coerce")
    culture["경도"] = pd.to_numeric(culture["경도"], errors="coerce")

    # 도서관
    library["구명"] = library["구명"].astype(str).str.strip()
    library = library[library["구명"].isin(SEOUL_DISTRICTS)]

    # 지하철
    subway["자치구"] = subway["도로명주소"].apply(extract_district)
    subway["자치구"] = subway["자치구"].fillna(subway["구주소"].apply(extract_district))
    subway = subway[subway["자치구"].isin(SEOUL_DISTRICTS)]

    # 공원
    district_col = "지역" if "지역" in parks.columns else "자치구"
    parks[district_col] = parks[district_col].astype(str).str.strip()
    parks = parks[parks[district_col].isin(SEOUL_DISTRICTS)]
    parks["위도"] = pd.to_numeric(parks["Y좌표(WGS84)"], errors="coerce")
    parks["경도"] = pd.to_numeric(parks["X좌표(WGS84)"], errors="coerce")

    # 생활물가
    prices["자치구 이름"] = prices["자치구 이름"].astype(str).str.strip()
    prices = prices[prices["자치구 이름"].isin(SEOUL_DISTRICTS)]
    prices["가격(원)"] = pd.to_numeric(prices["가격(원)"], errors="coerce")

    # 월세 (있으면 실제 CSV 사용, 없으면 보고서 fallback)
    rent_source = "fallback"
    rent_city_avg = int(round(pd.Series(FALLBACK_RENT).mean()))
    rent_df = pd.DataFrame({"자치구": list(FALLBACK_RENT.keys()), "평균월세": list(FALLBACK_RENT.values())})
    try:
        rent_raw = read_csv_flexible("서울특별시_전월세가_2025.csv").copy()
        rent_raw["전월세구분"] = rent_raw["전월세구분"].astype(str)
        rent_raw["임대료(만원)"] = pd.to_numeric(rent_raw["임대료(만원)"], errors="coerce")
        rent_raw["자치구명"] = rent_raw["자치구명"].astype(str).str.strip()
        monthly = rent_raw[(rent_raw["전월세구분"].str.contains("월세")) & (rent_raw["임대료(만원)"] > 0)]
        monthly = monthly[monthly["자치구명"].isin(SEOUL_DISTRICTS)]
        by_dist = monthly.groupby("자치구명")["임대료(만원)"].mean().round().astype(int).reset_index()
        by_dist.columns = ["자치구", "평균월세"]
        if len(by_dist) >= 20:
            rent_df = by_dist
            rent_city_avg = int(round(monthly["임대료(만원)"].mean()))
            rent_source = "csv"
    except Exception:
        pass

    # 집계
    district_base = pd.DataFrame({"자치구": SEOUL_DISTRICTS})
    district_base["문화공간수"] = district_base["자치구"].map(culture.groupby("자치구").size()).fillna(0).astype(int)
    district_base["도서관수"] = district_base["자치구"].map(library.groupby("구명").size()).fillna(0).astype(int)
    district_base["공원수"] = district_base["자치구"].map(parks.groupby(district_col).size()).fillna(0).astype(int)
    district_base["지하철역수"] = district_base["자치구"].map(subway.groupby("자치구").size()).fillna(0).astype(int)
    district_base["생활물가평균"] = district_base["자치구"].map(prices.groupby("자치구 이름")["가격(원)"].mean()).round().fillna(0).astype(int)
    district_base = district_base.merge(rent_df, on="자치구", how="left")
    district_base["평균월세"] = district_base["평균월세"].fillna(pd.Series(FALLBACK_RENT)).fillna(0).astype(int)

    # 문화 카테고리 요약
    culture_type_counts = (
        culture.groupby(["자치구", "문화카테고리"]).size().reset_index(name="개수")
        .sort_values(["자치구", "개수"], ascending=[True, False])
    )

    # 지하철 호선 문자열
    subway_line_summary = (
        subway.groupby("자치구")["호선"]
        .apply(lambda s: ", ".join(sorted(pd.Series(s).dropna().astype(str).unique().tolist())))
        .reset_index(name="주요호선")
    )
    district_base = district_base.merge(subway_line_summary, on="자치구", how="left")
    district_base["주요호선"] = district_base["주요호선"].fillna("-")

    # 서울 평균 생활물가
    city_price_avg = int(round(prices["가격(원)"].mean()))
    return district_base, culture, library, subway, parks, prices, culture_type_counts, rent_city_avg, rent_source, district_col, city_price_avg

def make_score_frame(base_df, weights):
    score_df = base_df.copy()
    scaler = MinMaxScaler()

    score_columns = ["문화공간수", "도서관수", "공원수", "지하철역수"]
    score_df[[f"{c}_정규화" for c in score_columns]] = scaler.fit_transform(score_df[score_columns])

    # 낮을수록 좋은 값은 뒤집기
    price_scaled = scaler.fit_transform(score_df[["생활물가평균"]])
    rent_scaled = scaler.fit_transform(score_df[["평균월세"]])

    score_df["생활물가점수"] = 1 - price_scaled
    score_df["월세점수"] = 1 - rent_scaled
    score_df["문화점수"] = score_df["문화공간수_정규화"]
    score_df["도서관점수"] = score_df["도서관수_정규화"]
    score_df["공원점수"] = score_df["공원수_정규화"]
    score_df["교통점수"] = score_df["지하철역수_정규화"]

    total = sum(weights.values())
    if total == 0:
        total = 1

    score_df["추천점수"] = (
        score_df["월세점수"] * weights["월세"] +
        score_df["생활물가점수"] * weights["물가"] +
        score_df["교통점수"] * weights["교통"] +
        score_df["문화점수"] * weights["문화"] +
        score_df["공원점수"] * weights["공원"] +
        score_df["도서관점수"] * weights["도서관"]
    ) / total

    score_df["추천점수_100"] = (score_df["추천점수"] * 100).round(1)
    return score_df.sort_values("추천점수", ascending=False).reset_index(drop=True)

def district_reason(row):
    reasons = []
    if row["월세점수"] >= 0.65:
        reasons.append("월세 부담이 비교적 낮아요")
    if row["생활물가점수"] >= 0.65:
        reasons.append("생활물가가 상대적으로 안정적이에요")
    if row["교통점수"] >= 0.65:
        reasons.append("지하철 접근성이 좋아요")
    if row["문화점수"] >= 0.65:
        reasons.append("문화공간이 풍부해요")
    if row["공원점수"] >= 0.65:
        reasons.append("공원·녹지 접근성이 좋아요")
    if row["도서관점수"] >= 0.65:
        reasons.append("도서관 이용이 편리해요")
    return reasons[:3] if reasons else ["전체 지표가 고르게 무난해요"]

district_df, culture, library, subway, parks, prices, culture_type_counts, rent_city_avg, rent_source, park_district_col, city_price_avg = load_all_data()

# -----------------------------
# 헤더
# -----------------------------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="main-title">서울, 처음이니? : 어디서 자취할까?</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">월세, 교통, 문화생활, 공원, 도서관, 생활물가를 한 번에 비교해서 나에게 맞는 서울 자치구를 찾아보세요.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.header("우선순위 설정")
    st.markdown(
        '<div class="sidebar-guide">'
        '<b>중요도 가이드</b><br>'
        '0 = 거의 안 봄<br>'
        '1~2 = 조금 참고<br>'
        '3 = 보통 중요<br>'
        '4 = 꽤 중요<br>'
        '5 = 가장 중요'
        '</div>',
        unsafe_allow_html=True
    )
    w_rent = st.slider("월세", 0, 5, 5)
    w_price = st.slider("생활물가", 0, 5, 3)
    w_transport = st.slider("교통(지하철)", 0, 5, 4)
    w_culture = st.slider("문화생활", 0, 5, 3)
    w_park = st.slider("공원·녹지", 0, 5, 2)
    w_library = st.slider("도서관", 0, 5, 2)

    st.markdown("---")
    district_options = ["전체 보기"] + SEOUL_DISTRICTS
    selected_district = st.selectbox("자치구 상세 보기", district_options, index=0)

weights = {
    "월세": w_rent,
    "물가": w_price,
    "교통": w_transport,
    "문화": w_culture,
    "공원": w_park,
    "도서관": w_library,
}

score_df = make_score_frame(district_df, weights)

if selected_district == "전체 보기":
    detail_district = score_df.iloc[0]["자치구"]
else:
    detail_district = selected_district

detail_row = score_df[score_df["자치구"] == detail_district].iloc[0]

# -----------------------------
# 주요 지표
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">서울 전체 평균 월세</div>'
        f'<div class="metric-value">{rent_city_avg}만원</div>'
        f'<div class="metric-help">{"전월세 CSV 기준" if rent_source=="csv" else "보고서 요약값 기준"}</div></div>',
        unsafe_allow_html=True
    )
with c2:
    diff = detail_row["평균월세"] - rent_city_avg
    diff_txt = f"서울 평균보다 {abs(diff)}만원 {'비싸요' if diff > 0 else '저렴해요' if diff < 0 else '비슷해요'}"
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{detail_district} 평균 월세</div>'
        f'<div class="metric-value">{int(detail_row["평균월세"])}만원</div>'
        f'<div class="metric-help">{diff_txt}</div></div>',
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">서울 평균 생활물가</div>'
        f'<div class="metric-value">{city_price_avg:,}원</div>'
        f'<div class="metric-help">업로드한 생활물가 CSV 평균</div></div>',
        unsafe_allow_html=True
    )
with c4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{detail_district} 추천 점수</div>'
        f'<div class="metric-value">{detail_row["추천점수_100"]}점</div>'
        f'<div class="metric-help">현재 우선순위 기준</div></div>',
        unsafe_allow_html=True
    )

# -----------------------------
# 추천 / 지도 / 문화생활
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["추천 결과", "서울 지도", "지역 상세", "데이터 보기"])

with tab1:
    st.markdown('<div class="section-title">우선순위에 맞는 추천 지역 TOP 5</div>', unsafe_allow_html=True)
    top5 = score_df.head(5)
    cols = st.columns(3)
    for i, (_, row) in enumerate(top5.iloc[:3].iterrows()):
        with cols[i]:
            reasons = district_reason(row)
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-rank">TOP {i+1}</div>
                <div class="rec-name">{row['자치구']}</div>
                <div class="rec-score">{row['추천점수_100']}점</div>
                <div class="small-note" style="margin-top:0.3rem;">평균 월세 {int(row['평균월세'])}만원 · 생활물가 {int(row['생활물가평균']):,}원</div>
                <div style="margin-top:0.55rem;">{"".join([f'<span class="tag">{r}</span>' for r in reasons])}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">전체 순위</div>', unsafe_allow_html=True)
    rank_view = score_df[["자치구", "추천점수_100", "평균월세", "생활물가평균", "지하철역수", "문화공간수", "공원수", "도서관수", "주요호선"]].copy()
    rank_view.columns = ["자치구", "추천점수", "평균월세(만원)", "생활물가평균(원)", "지하철역수", "문화공간수", "공원수", "도서관수", "주요호선"]
    st.dataframe(rank_view, use_container_width=True, hide_index=True)

    chart_df = score_df.sort_values("추천점수_100", ascending=True)
    fig = px.bar(
        chart_df,
        x="추천점수_100",
        y="자치구",
        orientation="h",
        text="추천점수_100",
        color="추천점수_100",
        color_continuous_scale="Blues",
        labels={"추천점수_100": "추천 점수", "자치구": ""}
    )
    fig.update_layout(
        height=700,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<div class="section-title">클릭해서 보는 서울 자치구 지도</div>', unsafe_allow_html=True)
    st.caption("지도의 자치구를 클릭하면 해당 구의 핵심 정보가 팝업으로 표시됩니다. 상세 비교는 왼쪽 자치구 선택과 함께 보면 더 편합니다.")

    try:
        geojson = load_geojson()
        geo_df = score_df.copy()
        geo_df["id"] = geo_df["자치구"]

        score_map = {r["자치구"]: float(r["추천점수_100"]) for _, r in geo_df.iterrows()}
        rent_map = {r["자치구"]: int(r["평균월세"]) for _, r in geo_df.iterrows()}
        culture_map = {r["자치구"]: int(r["문화공간수"]) for _, r in geo_df.iterrows()}
        park_map = {r["자치구"]: int(r["공원수"]) for _, r in geo_df.iterrows()}
        subway_map = {r["자치구"]: int(r["지하철역수"]) for _, r in geo_df.iterrows()}

        for feature in geojson["features"]:
            name = feature["properties"].get("name")
            feature["properties"]["추천점수"] = score_map.get(name, 0)
            feature["properties"]["평균월세"] = rent_map.get(name, 0)
            feature["properties"]["문화공간수"] = culture_map.get(name, 0)
            feature["properties"]["공원수"] = park_map.get(name, 0)
            feature["properties"]["지하철역수"] = subway_map.get(name, 0)

        m = folium.Map(location=[37.56, 126.98], zoom_start=10.5, tiles="CartoDB positron")

        folium.Choropleth(
            geo_data=geojson,
            data=geo_df,
            columns=["자치구", "추천점수_100"],
            key_on="feature.properties.name",
            fill_color="PuBu",
            fill_opacity=0.78,
            line_opacity=0.9,
            line_color="#4b5563",
            legend_name="추천 점수",
            highlight=True
        ).add_to(m)

        popup = GeoJsonPopup(
            fields=["name", "추천점수", "평균월세", "문화공간수", "공원수", "지하철역수"],
            aliases=["자치구", "추천 점수", "평균 월세(만원)", "문화공간 수", "공원 수", "지하철역 수"],
            labels=True,
            localize=True,
        )
        tooltip = GeoJsonTooltip(
            fields=["name", "추천점수", "평균월세"],
            aliases=["자치구", "추천 점수", "평균 월세(만원)"],
            sticky=True,
        )

        gj = folium.GeoJson(
            geojson,
            name="자치구",
            style_function=lambda x: {
                "fillColor": "#ffffff00",
                "color": "#374151",
                "weight": 1.2,
            },
            highlight_function=lambda x: {
                "fillColor": "#93c5fd",
                "color": "#1d4ed8",
                "weight": 2.2,
                "fillOpacity": 0.25,
            },
            tooltip=tooltip,
            popup=popup,
        )
        gj.add_to(m)
        folium.LayerControl(collapsed=True).add_to(m)
        st_folium(m, width=None, height=720)
    except Exception:
        st.info("지도를 불러오지 못했어요. 인터넷 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요.")

with tab3:
    st.markdown(f'<div class="section-title">{detail_district} 상세 정보</div>', unsafe_allow_html=True)

    left, right = st.columns([1.08, 0.92])
    with left:
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown("#### 핵심 요약")
        reasons = district_reason(detail_row)
        st.markdown("".join([f'<span class="tag">{r}</span>' for r in reasons]), unsafe_allow_html=True)

        radar_df = pd.DataFrame({
            "항목": ["월세", "생활물가", "교통", "문화생활", "공원·녹지", "도서관"],
            "점수": [
                float(detail_row["월세점수"]),
                float(detail_row["생활물가점수"]),
                float(detail_row["교통점수"]),
                float(detail_row["문화점수"]),
                float(detail_row["공원점수"]),
                float(detail_row["도서관점수"]),
            ]
        })

        radar = px.line_polar(
            radar_df, r="점수", theta="항목", line_close=True, range_r=[0,1]
        )
        radar.update_traces(fill="toself")
        radar.update_layout(
            height=420,
            margin=dict(l=30, r=30, t=10, b=10),
            paper_bgcolor="white",
        )
        st.plotly_chart(radar, use_container_width=True)

        compare_df = pd.DataFrame({
            "항목": ["평균월세", "생활물가평균", "문화공간수", "공원수", "도서관수", "지하철역수"],
            detail_district: [
                int(detail_row["평균월세"]),
                int(detail_row["생활물가평균"]),
                int(detail_row["문화공간수"]),
                int(detail_row["공원수"]),
                int(detail_row["도서관수"]),
                int(detail_row["지하철역수"]),
            ],
            "서울평균": [
                int(round(district_df["평균월세"].mean())),
                int(round(district_df["생활물가평균"].mean())),
                int(round(district_df["문화공간수"].mean())),
                int(round(district_df["공원수"].mean())),
                int(round(district_df["도서관수"].mean())),
                int(round(district_df["지하철역수"].mean())),
            ]
        })
        bar = px.bar(compare_df, x="항목", y=[detail_district, "서울평균"], barmode="group")
        bar.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
        st.plotly_chart(bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="detail-card">', unsafe_allow_html=True)
        st.markdown("#### 문화생활은 무엇이 많은가?")
        district_culture_types = culture_type_counts[culture_type_counts["자치구"] == detail_district].head(8)
        if district_culture_types.empty:
            st.write("등록된 문화공간 정보가 없어요.")
        else:
            for _, r in district_culture_types.iterrows():
                st.markdown(f'<span class="tag">{r["문화카테고리"]} {int(r["개수"])}곳</span>', unsafe_allow_html=True)

        st.markdown("#### 대표 문화공간")
        district_culture = culture[culture["자치구"] == detail_district][["문화시설명", "주제분류", "주소"]].head(10)
        if len(district_culture):
            st.dataframe(district_culture, use_container_width=True, hide_index=True)
        else:
            st.write("표시할 문화공간 정보가 없어요.")

        st.markdown("#### 지하철")
        district_subway = subway[subway["자치구"] == detail_district]
        lines = sorted(district_subway["호선"].dropna().astype(str).unique().tolist())
        stations = district_subway["역명"].dropna().astype(str).unique().tolist()
        st.markdown("".join([f'<span class="tag">{line}</span>' for line in lines]) if lines else '<span class="small-note">호선 정보 없음</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="small-note">주요 역: {", ".join(stations[:12]) if stations else "없음"}</div>', unsafe_allow_html=True)

        st.markdown("#### 공원 & 도서관")
        district_parks = parks[parks[park_district_col] == detail_district]["공원명"].dropna().astype(str).tolist()
        district_libraries = library[library["구명"] == detail_district]["도서관명"].dropna().astype(str).tolist()
        st.markdown(f'<div class="small-note"><b>공원</b>: {", ".join(district_parks[:8]) if district_parks else "없음"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="small-note" style="margin-top:0.35rem;"><b>도서관</b>: {", ".join(district_libraries[:8]) if district_libraries else "없음"}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">생활물가 한눈에 보기</div>', unsafe_allow_html=True)
    district_prices = prices[prices["자치구 이름"] == detail_district].copy()
    if len(district_prices):
        top_items = (
            district_prices.groupby("품목 이름")["가격(원)"].mean()
            .sort_values(ascending=False)
            .head(12)
            .round().astype(int)
            .reset_index()
        )
        item_chart = px.bar(top_items.sort_values("가격(원)"), x="가격(원)", y="품목 이름", orientation="h")
        item_chart.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(item_chart, use_container_width=True)
    else:
        st.info("생활물가 데이터가 없어요.")

with tab4:
    st.markdown('<div class="section-title">원본 기반 요약 데이터</div>', unsafe_allow_html=True)
    st.caption("생활물가는 정수 단위로 반올림해 표시했습니다.")
    data_view = district_df.copy()
    data_view["생활물가평균"] = data_view["생활물가평균"].round().astype(int)
    st.dataframe(data_view, use_container_width=True, hide_index=True)
