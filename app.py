import json
import os
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="서울 자취맵",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# 기본 설정
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구",
]

FILE_MAP = {
    "subway": "서울교통공사_역주소 및 전화번호.csv",
    "parks": "서울시 주요 공원현황(2026 상반기).xlsx",
    "libraries": "서울시 공공도서관 현황정보.csv",
    "rent": "서울특별시_전월세가_2025.csv",
    "prices": "생필품 농수축산물 가격 정보(2024년).csv",
    "culture": "서울시 문화공간 정보.csv",
}

CATEGORY_META = {
    "공원": {"color": "#4CAF50", "icon": "🌳"},
    "도서관": {"color": "#1E88E5", "icon": "📚"},
    "문화공간": {"color": "#8E24AA", "icon": "🎭"},
}

BASKET_ITEMS = [
    "대파 1단",
    "감자 100g",
    "돼지고기 100g",
    "양파 1망",
    "라면 5개입 1봉",
    "우유 1L",
    "달걀 30개",
    " 쌀(이천쌀) 20kg 1포",
]

GEOJSON_URL = (
    "https://raw.githubusercontent.com/raqoon886/Local_HangJeongDong/master/"
    "hangjeongdong_%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C.geojson"
)


# ==============================
# 스타일
# ==============================
CUSTOM_CSS = """
<style>
.main > div {padding-top: 1rem;}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {
    padding: 1.25rem 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #f7faff 0%, #eef7ff 60%, #f6fff3 100%);
    border: 1px solid rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}
.hero h1 {font-size: 2rem; margin: 0 0 0.35rem 0;}
.hero p {margin: 0.1rem 0; color: #4b5563;}
.soft-card {
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 0.95rem 1rem;
    background: white;
}
.small-muted {font-size: 0.87rem; color: #6b7280;}
.section-title {margin-top: 0.25rem; margin-bottom: 0.5rem;}
.kpi-card {
    border-radius: 18px;
    padding: 0.9rem 1rem;
    color: #111827;
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.08);
    box-shadow: 0 4px 18px rgba(0,0,0,0.04);
}
.kpi-label {font-size: 0.9rem; color: #6b7280; margin-bottom: 0.2rem;}
.kpi-value {font-size: 1.6rem; font-weight: 700;}
.kpi-sub {font-size: 0.82rem; color: #6b7280;}
.tag {
    display: inline-block;
    padding: 0.18rem 0.55rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 0.25rem;
    margin-bottom: 0.25rem;
    background: #f3f4f6;
    color: #374151;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================
# 유틸리티 함수
# ==============================
def file_path(key: str) -> str:
    return os.path.join(BASE_DIR, FILE_MAP[key])


def safe_read_csv(path: str) -> pd.DataFrame:
    for encoding in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            continue
    return pd.read_csv(path)


def safe_read_excel(path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    if sheet_name is None:
        return pd.read_excel(path)
    return pd.read_excel(path, sheet_name=sheet_name)


def normalize_district(value: object) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    match = re.search(r"([가-힣]+구)", text)
    if not match:
        return None
    gu = match.group(1)
    return gu if gu in SEOUL_DISTRICTS else None


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def fmt_int(value: Optional[float], suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(value)):,}{suffix}"


def fmt_float(value: Optional[float], digits: int = 1, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:,.{digits}f}{suffix}"


def metric_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>
    """


@st.cache_data(show_spinner=False)
def load_geojson() -> Tuple[Optional[dict], Optional[pd.DataFrame]]:
    try:
        response = requests.get(GEOJSON_URL, timeout=12)
        response.raise_for_status()
        geojson = response.json()
        records = []
        for feature in geojson.get("features", []):
            adm_nm = feature.get("properties", {}).get("adm_nm")
            district = normalize_district(adm_nm)
            if district:
                records.append({"adm_nm": adm_nm, "district": district})
        geo_df = pd.DataFrame(records)
        return geojson, geo_df
    except Exception:
        return None, None


@st.cache_data(show_spinner=False)
def load_data() -> Dict[str, pd.DataFrame]:
    # 공원
    parks = safe_read_excel(file_path("parks"))
    parks = parks.rename(
        columns={
            "공원명": "name",
            "지역": "district",
            "공원주소": "address",
            "전화번호": "phone",
            "X좌표(WGS84)": "lon",
            "Y좌표(WGS84)": "lat",
            "바로가기": "url",
        }
    )
    parks["district"] = parks["district"].apply(normalize_district)
    parks["lat"] = pd.to_numeric(parks["lat"], errors="coerce")
    parks["lon"] = pd.to_numeric(parks["lon"], errors="coerce")
    parks["category"] = "공원"
    parks = parks[["name", "district", "address", "phone", "lat", "lon", "url", "category"]].dropna(subset=["district"])

    # 도서관
    libraries = safe_read_csv(file_path("libraries"))
    libraries = libraries.rename(
        columns={
            "도서관명": "name",
            "구명": "district",
            "주소": "address",
            "전화번호": "phone",
            "위도": "lat",
            "경도": "lon",
            "홈페이지 URL": "url",
            "운영시간": "hours",
            "정기 휴관일": "closed",
        }
    )
    libraries["district"] = libraries["district"].apply(normalize_district)
    libraries["lat"] = pd.to_numeric(libraries["lat"], errors="coerce")
    libraries["lon"] = pd.to_numeric(libraries["lon"], errors="coerce")
    libraries["category"] = "도서관"
    libraries = libraries[["name", "district", "address", "phone", "lat", "lon", "url", "hours", "closed", "category"]].dropna(subset=["district"])

    # 문화공간
    culture = safe_read_csv(file_path("culture"))
    culture = culture.rename(
        columns={
            "문화시설명": "name",
            "자치구": "district",
            "주소": "address",
            "전화번호": "phone",
            "위도": "lat",
            "경도": "lon",
            "홈페이지": "url",
            "관람시간": "hours",
            "관람료": "fee",
            "휴관일": "closed",
            "지하철": "subway_info",
        }
    )
    culture["district"] = culture["district"].apply(normalize_district)
    culture["lat"] = pd.to_numeric(culture["lat"], errors="coerce")
    culture["lon"] = pd.to_numeric(culture["lon"], errors="coerce")
    culture["category"] = "문화공간"
    culture = culture[["name", "district", "address", "phone", "lat", "lon", "url", "hours", "fee", "closed", "subway_info", "category"]].dropna(subset=["district"])

    # 지하철역
    subway = safe_read_csv(file_path("subway"))
    subway = subway.rename(
        columns={
            "호선": "line",
            "역명": "name",
            "도로명주소": "road_address",
            "구주소": "old_address",
            "전화번호": "phone",
        }
    )
    subway["district"] = subway["road_address"].apply(normalize_district)
    subway["district"] = subway["district"].fillna(subway["old_address"].apply(normalize_district))
    subway = subway.dropna(subset=["district"])

    # 전월세
    rent = safe_read_csv(file_path("rent"))
    rent = rent.rename(
        columns={
            "자치구명": "district",
            "법정동명": "dong",
            "전월세구분": "rent_type",
            "임대면적": "area_sqm",
            "보증금(만원)": "deposit_10k",
            "임대료(만원)": "monthly_10k",
            "건물명": "building_name",
            "건축년도": "built_year",
            "건물용도": "building_type",
            "계약일": "contract_date",
        }
    )
    rent["district"] = rent["district"].apply(normalize_district)
    rent["area_sqm"] = pd.to_numeric(rent["area_sqm"], errors="coerce")
    rent["deposit_10k"] = to_numeric(rent["deposit_10k"])
    rent["monthly_10k"] = to_numeric(rent["monthly_10k"])
    rent["built_year"] = pd.to_numeric(rent["built_year"], errors="coerce")
    rent["contract_date"] = pd.to_datetime(rent["contract_date"].astype(str), format="%Y%m%d", errors="coerce")
    rent = rent.dropna(subset=["district"])

    # 생필품 / 전통시장
    prices = safe_read_csv(file_path("prices"))
    prices = prices.rename(
        columns={
            "시장/마트 이름": "market_name",
            "품목 이름": "item_name",
            "가격(원)": "price_won",
            "자치구 이름": "district",
            "점검일자": "check_date",
            "시장유형 구분(시장/마트) 이름": "market_type",
        }
    )
    prices["district"] = prices["district"].apply(normalize_district)
    prices["price_won"] = to_numeric(prices["price_won"])
    prices["check_date"] = pd.to_datetime(prices["check_date"], errors="coerce")
    prices = prices[(prices["market_type"] == "전통시장") & prices["district"].notna()].copy()

    # 좌표가 있는 시설 데이터
    points = pd.concat([
        parks[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
        libraries[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
        culture[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
    ], ignore_index=True)
    points = points.dropna(subset=["lat", "lon", "district"])

    district_centers = (
        points.groupby("district", as_index=False)[["lat", "lon"]]
        .mean()
        .sort_values("district")
    )

    return {
        "parks": parks,
        "libraries": libraries,
        "culture": culture,
        "subway": subway,
        "rent": rent,
        "prices": prices,
        "points": points,
        "district_centers": district_centers,
    }


@st.cache_data(show_spinner=False)
def build_rent_summary(rent_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    monthly = rent_df[rent_df["rent_type"] == "월세"].copy()
    summary = (
        monthly.groupby("district", as_index=False)
        .agg(
            monthly_median=("monthly_10k", "median"),
            monthly_mean=("monthly_10k", "mean"),
            deposit_median=("deposit_10k", "median"),
            area_median=("area_sqm", "median"),
            listings=("monthly_10k", "count"),
            latest_contract=("contract_date", "max"),
        )
        .sort_values("monthly_median", ascending=False)
    )
    summary["latest_contract_str"] = summary["latest_contract"].dt.strftime("%Y-%m-%d")
    return monthly, summary


@st.cache_data(show_spinner=False)
def build_market_summary(prices_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # 시장 목록
    markets = (
        prices_df.groupby(["district", "market_name"], as_index=False)
        .agg(
            item_count=("item_name", "nunique"),
            latest_check=("check_date", "max"),
        )
        .sort_values(["district", "market_name"])
    )
    markets["latest_check_str"] = markets["latest_check"].dt.strftime("%Y-%m-%d")

    # 최근 시점 품목 가격
    latest_item_price = (
        prices_df.sort_values("check_date")
        .groupby(["district", "market_name", "item_name"], as_index=False)
        .tail(1)
    )

    basket = latest_item_price[latest_item_price["item_name"].isin(BASKET_ITEMS)].copy()
    basket_summary = (
        basket.groupby(["district", "item_name"], as_index=False)
        .agg(avg_price=("price_won", "mean"), markets=("market_name", "nunique"))
        .sort_values(["district", "item_name"])
    )

    basket_total = (
        basket_summary.groupby("district", as_index=False)
        .agg(
            basket_total=("avg_price", "sum"),
            basket_item_count=("item_name", "count"),
        )
        .sort_values("basket_total", ascending=False)
    )

    return markets, basket_summary, basket_total


# ==============================
# 데이터 로드
# ==============================
try:
    data = load_data()
    geojson, geo_df = load_geojson()
    monthly_rent, rent_summary = build_rent_summary(data["rent"])
    markets_df, basket_summary_df, basket_total_df = build_market_summary(data["prices"])
except FileNotFoundError as e:
    st.error(f"필수 데이터 파일을 찾지 못했습니다: {e}")
    st.stop()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

points = data["points"].copy()
subway = data["subway"].copy()
parks = data["parks"].copy()
libraries = data["libraries"].copy()
culture = data["culture"].copy()
centers = data["district_centers"].copy()

# ==============================
# 사이드바
# ==============================
st.sidebar.title("⚙️ 탐색 설정")
selected_district = st.sidebar.selectbox("자치구 선택", ["전체"] + SEOUL_DISTRICTS, index=0)
selected_categories = st.sidebar.multiselect(
    "지도에 표시할 시설",
    ["공원", "도서관", "문화공간"],
    default=["공원", "도서관", "문화공간"],
)
show_rent_layer = st.sidebar.toggle("월세 시세 레이어 표시", value=True)
show_labels = st.sidebar.toggle("지도 마커 이름 표시", value=False)

building_types = sorted([x for x in monthly_rent["building_type"].dropna().unique().tolist() if str(x).strip()])
selected_buildings = st.sidebar.multiselect(
    "월세 분석 건물용도",
    building_types,
    default=building_types,
)

st.sidebar.markdown("---")
st.sidebar.caption("지도 클릭 선택은 제외하고, 코딩 초보자도 안정적으로 배포 가능한 방식으로 구성했습니다.")
st.sidebar.caption("지하철역·전통시장은 업로드 파일에 좌표가 없어 목록 중심으로 제공합니다.")

# 필터링
filtered_monthly = monthly_rent.copy()
if selected_buildings:
    filtered_monthly = filtered_monthly[filtered_monthly["building_type"].isin(selected_buildings)]
if selected_district != "전체":
    filtered_monthly = filtered_monthly[filtered_monthly["district"] == selected_district]

current_rent_summary = (
    filtered_monthly.groupby("district", as_index=False)
    .agg(
        monthly_median=("monthly_10k", "median"),
        deposit_median=("deposit_10k", "median"),
        listings=("monthly_10k", "count"),
        area_median=("area_sqm", "median"),
        latest_contract=("contract_date", "max"),
    )
    .sort_values("monthly_median", ascending=False)
)
current_rent_summary["latest_contract_str"] = current_rent_summary["latest_contract"].dt.strftime("%Y-%m-%d")

if selected_district == "전체":
    active_points = points[points["category"].isin(selected_categories)].copy()
else:
    active_points = points[(points["district"] == selected_district) & (points["category"].isin(selected_categories))].copy()

selected_subway = subway if selected_district == "전체" else subway[subway["district"] == selected_district]
selected_markets = markets_df if selected_district == "전체" else markets_df[markets_df["district"] == selected_district]
selected_basket = basket_summary_df if selected_district == "전체" else basket_summary_df[basket_summary_df["district"] == selected_district]
selected_basket_total = basket_total_df if selected_district == "전체" else basket_total_df[basket_total_df["district"] == selected_district]

# ==============================
# 헤더
# ==============================
st.markdown(
    """
    <div class='hero'>
        <h1>🏠 서울 자취맵</h1>
        <p>서울 자취생을 위한 지역 탐색 플랫폼 — 공원, 도서관, 문화공간, 전통시장, 지하철역, 월세 시세를 한눈에 비교</p>
        <p class='small-muted'>기준: 업로드된 CSV/XLSX 파일 기반 · 월세 시세는 <b>서울특별시_전월세가_2025.csv</b>의 월세 계약 데이터 기준</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================
# 상단 KPI
# ==============================
all_market_count = selected_markets["market_name"].nunique() if not selected_markets.empty else 0
all_subway_count = selected_subway["name"].nunique() if not selected_subway.empty else 0
active_rent_row = None
if selected_district != "전체" and not current_rent_summary.empty:
    active_rent_row = current_rent_summary.iloc[0]

if selected_district == "전체":
    total_row = current_rent_summary.agg(
        {
            "monthly_median": "median",
            "deposit_median": "median",
            "listings": "sum",
            "area_median": "median",
        }
    )
    latest_contract = current_rent_summary["latest_contract"].max() if "latest_contract" in current_rent_summary else pd.NaT
    district_count = current_rent_summary["district"].nunique()
else:
    total_row = active_rent_row if active_rent_row is not None else pd.Series(dtype=float)
    latest_contract = active_rent_row["latest_contract"] if active_rent_row is not None else pd.NaT
    district_count = 1

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(metric_card("중앙 월세", fmt_int(total_row.get("monthly_median"), "만원"), f"분석 자치구 {district_count}곳"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("중앙 보증금", fmt_int(total_row.get("deposit_median"), "만원"), "월세 계약 기준"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("전통시장 수", fmt_int(all_market_count, "곳"), f"지하철역 {all_subway_count}개"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("계약 건수", fmt_int(total_row.get("listings"), "건"), f"최근 계약일 {latest_contract.strftime('%Y-%m-%d') if pd.notna(latest_contract) else '-'}"), unsafe_allow_html=True)

# ==============================
# 탭 구성
# ==============================
tab1, tab2, tab3, tab4 = st.tabs(["📍 지도/개요", "🏘️ 지역 상세", "🧺 장보기 물가", "ℹ️ 데이터 안내"])

with tab1:
    left, right = st.columns([1.65, 1])

    with left:
        st.subheader("서울 지도")
        map_note = "월세 중앙값 레이어 + 좌표가 있는 시설 마커"
        if not show_rent_layer:
            map_note = "좌표가 있는 시설 마커만 표시"
        st.caption(map_note)

        fig = go.Figure()

        # 1) 월세 choropleth
        if show_rent_layer and geojson is not None and geo_df is not None and not current_rent_summary.empty:
            merged = geo_df.merge(current_rent_summary[["district", "monthly_median"]], on="district", how="left")
            fig_choro = px.choropleth_mapbox(
                merged,
                geojson=geojson,
                locations="adm_nm",
                featureidkey="properties.adm_nm",
                color="monthly_median",
                color_continuous_scale="YlGnBu",
                opacity=0.38,
                mapbox_style="carto-positron",
                center={"lat": 37.5665, "lon": 126.9780},
                zoom=9.5 if selected_district == "전체" else 10.4,
                hover_data={"district": True, "adm_nm": False, "monthly_median": ":.0f"},
            )
            for tr in fig_choro.data:
                fig.add_trace(tr)

        # 2) 시설 포인트
        point_df = active_points.copy()
        if selected_district != "전체" and not centers[centers["district"] == selected_district].empty:
            center_row = centers[centers["district"] == selected_district].iloc[0]
            map_center = {"lat": float(center_row["lat"]), "lon": float(center_row["lon"])}
            map_zoom = 11.1
        else:
            map_center = {"lat": 37.5665, "lon": 126.9780}
            map_zoom = 9.4

        for category in selected_categories:
            cdf = point_df[point_df["category"] == category].copy()
            if cdf.empty:
                continue
            text = cdf["name"] if show_labels else None
            fig.add_trace(
                go.Scattermapbox(
                    lat=cdf["lat"],
                    lon=cdf["lon"],
                    mode="markers+text" if show_labels else "markers",
                    text=text,
                    textposition="top right",
                    marker=go.scattermapbox.Marker(size=10, color=CATEGORY_META[category]["color"]),
                    name=f"{CATEGORY_META[category]['icon']} {category}",
                    customdata=np.stack([
                        cdf["name"].fillna("-"),
                        cdf["district"].fillna("-"),
                        cdf["address"].fillna("-"),
                    ], axis=-1),
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "자치구: %{customdata[1]}<br>"
                        "주소: %{customdata[2]}<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_center=map_center,
            mapbox_zoom=map_zoom,
            height=680,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("전통시장·지하철역은 업로드 파일에 좌표가 없어 상세 목록으로 제공합니다.")

    with right:
        st.subheader("지역 비교")
        if current_rent_summary.empty:
            st.info("선택 조건에 맞는 월세 데이터가 없습니다.")
        else:
            compare_fig = px.bar(
                current_rent_summary.head(15).sort_values("monthly_median"),
                x="monthly_median",
                y="district",
                orientation="h",
                labels={"monthly_median": "중앙 월세(만원)", "district": "자치구"},
                text="monthly_median",
            )
            compare_fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
            compare_fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(compare_fig, use_container_width=True)

        st.markdown("### 선택 지역 한눈에 보기")
        if selected_district == "전체":
            rank_text = "전체 서울 비교"
            current_market_total = selected_markets["market_name"].nunique()
            current_subway_total = selected_subway["name"].nunique()
            current_point_total = active_points.shape[0]
            basket_value = selected_basket_total["basket_total"].median() if not selected_basket_total.empty else np.nan
        else:
            district_rank = current_rent_summary.reset_index(drop=True)
            district_rank["rank"] = district_rank.index + 1
            matched = district_rank[district_rank["district"] == selected_district]
            rank_text = f"월세 중앙값 순위 {int(matched['rank'].iloc[0])}위 / {len(district_rank)}개 구" if not matched.empty else "-"
            current_market_total = selected_markets["market_name"].nunique()
            current_subway_total = selected_subway["name"].nunique()
            current_point_total = active_points.shape[0]
            basket_value = selected_basket_total["basket_total"].iloc[0] if not selected_basket_total.empty else np.nan

        st.markdown(f"<span class='tag'>📊 {rank_text}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='tag'>🛒 전통시장 {current_market_total}곳</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='tag'>🚇 지하철역 {current_subway_total}개</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='tag'>📍 지도표시 시설 {current_point_total}개</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='tag'>🧺 장보기 바스켓 {fmt_int(basket_value, '원')}</span>", unsafe_allow_html=True)

        st.markdown("### 월세 해석 팁")
        st.info(
            "- 중앙값은 극단값 영향을 줄여 자취생 체감 시세를 보기 좋습니다.\n"
            "- 보증금과 월세를 함께 보세요. 월세만 낮고 보증금이 높을 수 있습니다.\n"
            "- 건물용도 필터를 바꾸면 지역 체감이 꽤 달라집니다."
        )

with tab2:
    st.subheader(f"{selected_district} 상세 정보" if selected_district != "전체" else "전체 지역 상세 정보")

    if selected_district != "전체" and not current_rent_summary.empty:
        row = current_rent_summary[current_rent_summary["district"] == selected_district]
        if not row.empty:
            row = row.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("중앙 월세", fmt_int(row["monthly_median"], "만원"))
            c2.metric("중앙 보증금", fmt_int(row["deposit_median"], "만원"))
            c3.metric("중앙 전용면적", fmt_float(row["area_median"], 1, "㎡"))
            c4.metric("월세 표본수", fmt_int(row["listings"], "건"))

    dcol1, dcol2 = st.columns([1.1, 1])
    with dcol1:
        st.markdown("### 월세 상위 표본")
        rent_preview = filtered_monthly.copy()
        rent_preview = rent_preview.sort_values(["monthly_10k", "deposit_10k"], ascending=[False, False])
        rent_preview = rent_preview[["district", "dong", "building_name", "building_type", "area_sqm", "deposit_10k", "monthly_10k", "contract_date"]].head(20)
        rent_preview = rent_preview.rename(
            columns={
                "district": "자치구",
                "dong": "법정동",
                "building_name": "건물명",
                "building_type": "건물용도",
                "area_sqm": "면적(㎡)",
                "deposit_10k": "보증금(만원)",
                "monthly_10k": "월세(만원)",
                "contract_date": "계약일",
            }
        )
        if not rent_preview.empty:
            st.dataframe(rent_preview, use_container_width=True, hide_index=True)
        else:
            st.info("조건에 맞는 월세 데이터가 없습니다.")

    with dcol2:
        st.markdown("### 지하철역 목록")
        subway_view = selected_subway[["district", "line", "name", "road_address", "phone"]].drop_duplicates().rename(
            columns={
                "district": "자치구",
                "line": "호선",
                "name": "역명",
                "road_address": "도로명주소",
                "phone": "전화번호",
            }
        )
        subway_view = subway_view.sort_values(["자치구", "호선", "역명"]).head(50)
        if not subway_view.empty:
            st.dataframe(subway_view, use_container_width=True, hide_index=True)
        else:
            st.info("해당 지역의 지하철역 데이터가 없습니다.")

    st.markdown("---")
    st.markdown("### 시설 목록")

    cat_tabs = st.tabs(["🌳 공원", "📚 도서관", "🎭 문화공간", "🛒 전통시장"])

    with cat_tabs[0]:
        view = parks if selected_district == "전체" else parks[parks["district"] == selected_district]
        view = view[["district", "name", "address", "phone", "url"]].rename(
            columns={"district": "자치구", "name": "공원명", "address": "주소", "phone": "전화번호", "url": "바로가기"}
        )
        st.dataframe(view.sort_values(["자치구", "공원명"]), use_container_width=True, hide_index=True)

    with cat_tabs[1]:
        view = libraries if selected_district == "전체" else libraries[libraries["district"] == selected_district]
        view = view[["district", "name", "address", "hours", "closed", "url"]].rename(
            columns={"district": "자치구", "name": "도서관명", "address": "주소", "hours": "운영시간", "closed": "휴관일", "url": "홈페이지"}
        )
        st.dataframe(view.sort_values(["자치구", "도서관명"]), use_container_width=True, hide_index=True)

    with cat_tabs[2]:
        view = culture if selected_district == "전체" else culture[culture["district"] == selected_district]
        view = view[["district", "name", "address", "fee", "hours", "url"]].rename(
            columns={"district": "자치구", "name": "시설명", "address": "주소", "fee": "관람료", "hours": "운영시간", "url": "홈페이지"}
        )
        st.dataframe(view.sort_values(["자치구", "시설명"]), use_container_width=True, hide_index=True)

    with cat_tabs[3]:
        view = selected_markets[["district", "market_name", "item_count", "latest_check_str"]].drop_duplicates().rename(
            columns={"district": "자치구", "market_name": "시장명", "item_count": "품목수", "latest_check_str": "최근 점검일"}
        )
        st.dataframe(view.sort_values(["자치구", "시장명"]), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("전통시장 장보기 물가")
    st.caption("업로드된 2024년 가격 파일에서 전통시장만 추출해 최근 점검 기준으로 묶었습니다.")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if selected_basket_total.empty:
            st.info("표시할 장보기 바스켓 데이터가 없습니다.")
        else:
            basket_rank = selected_basket_total.sort_values("basket_total", ascending=False)
            basket_fig = px.bar(
                basket_rank.head(15).sort_values("basket_total"),
                x="basket_total",
                y="district",
                orientation="h",
                labels={"basket_total": "바스켓 합계(원)", "district": "자치구"},
                text="basket_total",
            )
            basket_fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
            basket_fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(basket_fig, use_container_width=True)

    with col_b:
        st.markdown("### 바스켓 구성")
        st.write(
            ", ".join([item.strip() for item in BASKET_ITEMS])
        )
        st.markdown("### 선택 지역 품목 평균가")
        basket_view = selected_basket.copy().rename(
            columns={"district": "자치구", "item_name": "품목", "avg_price": "평균가격(원)", "markets": "반영시장수"}
        )
        if not basket_view.empty:
            st.dataframe(basket_view.sort_values(["자치구", "품목"]), use_container_width=True, hide_index=True)
        else:
            st.info("선택 지역의 바스켓 데이터가 없습니다.")

    st.markdown("### 전통시장별 최근 품목가")
    latest_price_table = (
        data["prices"].sort_values("check_date")
        .groupby(["district", "market_name", "item_name"], as_index=False)
        .tail(1)
    )
    if selected_district != "전체":
        latest_price_table = latest_price_table[latest_price_table["district"] == selected_district]
    latest_price_table = latest_price_table[["district", "market_name", "item_name", "price_won", "check_date"]].rename(
        columns={
            "district": "자치구",
            "market_name": "시장명",
            "item_name": "품목",
            "price_won": "가격(원)",
            "check_date": "점검일",
        }
    )
    st.dataframe(latest_price_table.head(150), use_container_width=True, hide_index=True)

with tab4:
    st.subheader("데이터 안내")

    info_rows = [
        {
            "데이터": "서울시 주요 공원현황",
            "파일": FILE_MAP["parks"],
            "활용": "공원 지도 마커 / 공원 목록",
            "기준": "파일명 기준 2026 상반기",
        },
        {
            "데이터": "서울교통공사 역주소 및 전화번호",
            "파일": FILE_MAP["subway"],
            "활용": "지하철역 목록 / 호선 정보",
            "기준": "업로드 파일 기준",
        },
        {
            "데이터": "서울시 공공도서관 현황정보",
            "파일": FILE_MAP["libraries"],
            "활용": "도서관 지도 마커 / 목록",
            "기준": "업로드 파일 기준",
        },
        {
            "데이터": "서울시 문화공간 정보",
            "파일": FILE_MAP["culture"],
            "활용": "문화공간 지도 마커 / 목록",
            "기준": "업로드 파일 기준",
        },
        {
            "데이터": "서울특별시 전월세가 2025",
            "파일": FILE_MAP["rent"],
            "활용": "자치구별 월세 중앙값/보증금 분석",
            "기준": f"파일 내 최근 계약일 {data['rent']['contract_date'].max().strftime('%Y-%m-%d') if data['rent']['contract_date'].notna().any() else '-'}",
        },
        {
            "데이터": "생필품 농수축산물 가격 정보(2024년)",
            "파일": FILE_MAP["prices"],
            "활용": "전통시장 목록 / 장보기 물가 비교",
            "기준": f"파일 내 최근 점검일 {data['prices']['check_date'].max().strftime('%Y-%m-%d') if data['prices']['check_date'].notna().any() else '-'}",
        },
    ]
    st.dataframe(pd.DataFrame(info_rows), use_container_width=True, hide_index=True)

    st.markdown("### 구현 특징")
    st.write(
        "1. 코딩 초보자 2명이 오늘 안에 완성할 수 있도록 Streamlit 단일 앱 구조로 작성했습니다.\n"
        "2. 지도는 월세 시세 레이어와 좌표가 있는 생활 인프라를 함께 보여줍니다.\n"
        "3. 전통시장과 지하철역은 좌표가 없는 파일이므로 목록형 정보로 우선 제공했습니다.\n"
        "4. 월세 시세는 평균보다 중앙값을 중심으로 보여 주어 극단값 영향을 줄였습니다.\n"
        "5. 장보기 바스켓을 추가해 자취생 생활비 관점까지 비교할 수 있게 했습니다."
    )

    st.markdown("### GitHub / Streamlit 배포 체크리스트")
    st.code(
        """# 1) GitHub 저장소에 아래 파일 업로드\n"
        "app.py\n"
        "requirements.txt\n"
        "서울교통공사_역주소 및 전화번호.csv\n"
        "서울시 주요 공원현황(2026 상반기).xlsx\n"
        "서울시 공공도서관 현황정보.csv\n"
        "서울특별시_전월세가_2025.csv\n"
        "생필품 농수축산물 가격 정보(2024년).csv\n"
        "서울시 문화공간 정보.csv\n\n"
        "# 2) 로컬 실행\n"
        "pip install -r requirements.txt\n"
        "streamlit run app.py\n\n"
        "# 3) Streamlit Community Cloud 배포 시\n"
        "Main file path: app.py\n""",
        language="bash",
    )
