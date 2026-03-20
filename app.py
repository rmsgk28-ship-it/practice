import os
import re
from typing import Dict, Optional

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
    "prices": "생필품 농수축산물 가격 정보(2024년).csv",
    "culture": "서울시 문화공간 정보.csv",
    "rent_summary": "서울시_월세요약_2025.csv",
    "rent_building": "서울시_월세_건물유형요약_2025.csv",
    "rent_dong": "서울시_월세_동별요약_2025.csv",
    "rent_month": "서울시_월세_월별요약_2025.csv",
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
.small-muted {font-size: 0.87rem; color: #6b7280;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def file_path(key: str) -> str:
    return os.path.join(BASE_DIR, FILE_MAP[key])


def safe_read_csv(path: str) -> pd.DataFrame:
    for encoding in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            continue
    return pd.read_csv(path)


def safe_read_excel(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


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


def fmt_int(value, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{int(round(float(value))):,}{suffix}"


def metric_card(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>
    """


@st.cache_data(show_spinner=False)
def load_geojson():
    try:
        response = requests.get(GEOJSON_URL, timeout=12)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def load_data() -> Dict[str, pd.DataFrame]:
    parks = safe_read_excel(file_path("parks")).rename(
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

    libraries = safe_read_csv(file_path("libraries")).rename(
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

    culture = safe_read_csv(file_path("culture")).rename(
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

    subway = safe_read_csv(file_path("subway")).rename(
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

    prices = safe_read_csv(file_path("prices")).rename(
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

    rent_summary = safe_read_csv(file_path("rent_summary"))
    rent_building = safe_read_csv(file_path("rent_building"))
    rent_dong = safe_read_csv(file_path("rent_dong"))
    rent_month = safe_read_csv(file_path("rent_month"))

    for df in [rent_summary, rent_building, rent_dong, rent_month]:
        if "district" in df.columns:
            df["district"] = df["district"].apply(normalize_district)
        for col in ["monthly_median", "monthly_mean", "deposit_median", "area_median", "listings"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "latest_contract" in df.columns:
            df["latest_contract"] = pd.to_datetime(df["latest_contract"], errors="coerce")
    if "contract_month" in rent_month.columns:
        rent_month["contract_month"] = pd.to_datetime(rent_month["contract_month"], errors="coerce")

    points = pd.concat([
        parks[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
        libraries[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
        culture[["name", "district", "address", "phone", "lat", "lon", "url", "category"]],
    ], ignore_index=True).dropna(subset=["lat", "lon", "district"])

    district_centers = points.groupby("district", as_index=False)[["lat", "lon"]].mean()
    fallback = pd.DataFrame({
        "district": SEOUL_DISTRICTS,
        "lat": [37.5172, 37.5301, 37.6396, 37.5509, 37.4784, 37.5384, 37.4954, 37.4569, 37.6542, 37.6688,
                37.5744, 37.5124, 37.5663, 37.5794, 37.4837, 37.5635, 37.5894, 37.5145, 37.5170, 37.5264,
                37.5323, 37.6027, 37.5735, 37.5636, 37.6066],
        "lon": [127.0473, 127.1238, 127.0257, 126.8495, 126.9516, 127.0823, 126.8874, 126.8956, 127.0568, 127.0471,
                127.0397, 126.9393, 126.9019, 126.9368, 127.0324, 127.0369, 127.0167, 127.1059, 126.8665, 126.8962,
                126.9900, 126.9291, 126.9790, 126.9976, 127.0927],
    })
    district_centers = fallback.merge(district_centers, on="district", how="left", suffixes=("_base", ""))
    district_centers["lat"] = district_centers["lat"].fillna(district_centers["lat_base"])
    district_centers["lon"] = district_centers["lon"].fillna(district_centers["lon_base"])
    district_centers = district_centers[["district", "lat", "lon"]]

    return {
        "parks": parks,
        "libraries": libraries,
        "culture": culture,
        "subway": subway,
        "prices": prices,
        "points": points,
        "centers": district_centers,
        "rent_summary": rent_summary.dropna(subset=["district"]),
        "rent_building": rent_building.dropna(subset=["district"]),
        "rent_dong": rent_dong.dropna(subset=["district"]),
        "rent_month": rent_month.dropna(subset=["district"]),
    }


@st.cache_data(show_spinner=False)
def build_market_summary(prices_df: pd.DataFrame):
    markets = (
        prices_df.groupby(["district", "market_name"], as_index=False)
        .agg(item_count=("item_name", "nunique"), latest_check=("check_date", "max"))
        .sort_values(["district", "market_name"])
    )
    latest_item_price = prices_df.sort_values("check_date").groupby(["district", "market_name", "item_name"], as_index=False).tail(1)
    basket = latest_item_price[latest_item_price["item_name"].isin(BASKET_ITEMS)].copy()
    basket_summary = (
        basket.groupby(["district", "item_name"], as_index=False)
        .agg(avg_price=("price_won", "mean"), markets=("market_name", "nunique"))
        .sort_values(["district", "item_name"])
    )
    basket_total = (
        basket_summary.groupby("district", as_index=False)
        .agg(basket_total=("avg_price", "sum"), basket_item_count=("item_name", "count"))
        .sort_values("basket_total", ascending=False)
    )
    return markets, basket_summary, basket_total


try:
    data = load_data()
    geojson = load_geojson()
    markets_df, basket_summary_df, basket_total_df = build_market_summary(data["prices"])
except FileNotFoundError as e:
    st.error(f"필수 데이터 파일을 찾지 못했습니다: {e}")
    st.stop()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

points = data["points"].copy()
subway = data["subway"].copy()
rent_summary = data["rent_summary"].copy()
rent_building = data["rent_building"].copy()
rent_dong = data["rent_dong"].copy()
rent_month = data["rent_month"].copy()
centers = data["centers"].copy()

st.sidebar.title("⚙️ 탐색 설정")
selected_district = st.sidebar.selectbox("자치구 선택", ["전체"] + SEOUL_DISTRICTS, index=0)
selected_categories = st.sidebar.multiselect(
    "지도에 표시할 시설",
    ["공원", "도서관", "문화공간"],
    default=["공원", "도서관", "문화공간"],
)
selected_building_type = st.sidebar.selectbox(
    "월세 건물유형",
    ["전체"] + sorted(rent_building["building_type"].dropna().astype(str).unique().tolist()),
)
show_rent_layer = st.sidebar.toggle("월세 레이어 표시", value=True)
show_labels = st.sidebar.toggle("시설명 표시", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("대용량 전월세 원본 CSV 없이도 실행되도록 월세 요약 파일 4개만 사용합니다.")
st.sidebar.caption("지하철역·전통시장은 업로드 파일에 좌표가 없어 목록 중심으로 제공합니다.")

if selected_district == "전체":
    active_points = points[points["category"].isin(selected_categories)].copy()
    active_subway = subway.copy()
    active_markets = markets_df.copy()
    active_basket = basket_summary_df.copy()
    active_basket_total = basket_total_df.copy()
    active_rent = rent_summary.copy()
    active_dong = rent_dong.copy()
    active_month = rent_month.copy()
    if selected_building_type == "전체":
        rent_for_kpi = rent_summary.copy()
    else:
        rent_for_kpi = rent_building[rent_building["building_type"] == selected_building_type].copy()
else:
    active_points = points[(points["district"] == selected_district) & (points["category"].isin(selected_categories))].copy()
    active_subway = subway[subway["district"] == selected_district].copy()
    active_markets = markets_df[markets_df["district"] == selected_district].copy()
    active_basket = basket_summary_df[basket_summary_df["district"] == selected_district].copy()
    active_basket_total = basket_total_df[basket_total_df["district"] == selected_district].copy()
    active_rent = rent_summary[rent_summary["district"] == selected_district].copy()
    active_dong = rent_dong[rent_dong["district"] == selected_district].copy()
    active_month = rent_month[rent_month["district"] == selected_district].copy()
    if selected_building_type == "전체":
        rent_for_kpi = active_rent.copy()
    else:
        rent_for_kpi = rent_building[(rent_building["district"] == selected_district) & (rent_building["building_type"] == selected_building_type)].copy()

if selected_building_type != "전체" and selected_district == "전체":
    map_rent = rent_building[rent_building["building_type"] == selected_building_type].copy()
else:
    map_rent = active_rent.copy() if selected_building_type == "전체" else rent_for_kpi.copy()

st.markdown(
    """
    <div class='hero'>
        <h1>🏠 서울 자취맵</h1>
        <p>서울 자취생을 위한 지역 탐색 플랫폼 — 월세 시세, 공원, 도서관, 문화공간, 전통시장, 지하철역을 한 화면에서 비교</p>
        <p class='small-muted'>월세는 원본 대용량 파일 대신 요약 파일 4개를 사용합니다. 따라서 사이트는 빠르게 실행되고 GitHub 업로드 제한에도 대응됩니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

latest_contract = rent_for_kpi["latest_contract"].max() if "latest_contract" in rent_for_kpi.columns and not rent_for_kpi.empty else pd.NaT
median_monthly = rent_for_kpi["monthly_median"].median() if "monthly_median" in rent_for_kpi.columns and not rent_for_kpi.empty else None
median_deposit = rent_for_kpi["deposit_median"].median() if "deposit_median" in rent_for_kpi.columns and not rent_for_kpi.empty else None
median_area = rent_for_kpi["area_median"].median() if "area_median" in rent_for_kpi.columns and not rent_for_kpi.empty else None
listing_count = rent_for_kpi["listings"].sum() if "listings" in rent_for_kpi.columns and not rent_for_kpi.empty else None

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(metric_card("중앙 월세", fmt_int(median_monthly, "만원"), f"건물유형: {selected_building_type}"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("중앙 보증금", fmt_int(median_deposit, "만원"), "월세 요약 기준"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("중앙 면적", fmt_int(median_area, "㎡"), f"전통시장 {active_markets['market_name'].nunique() if not active_markets.empty else 0}곳"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("계약 건수", fmt_int(listing_count, "건"), f"최근 계약일 {latest_contract.strftime('%Y-%m-%d') if pd.notna(latest_contract) else '-'}"), unsafe_allow_html=True)

left, right = st.columns([1.7, 1])

with left:
    st.subheader("🗺️ 서울 지도")
    fig = go.Figure()

    if show_rent_layer and not map_rent.empty:
        map_df = centers.merge(map_rent[[c for c in map_rent.columns if c in ["district", "monthly_median", "deposit_median", "listings", "area_median", "building_type"]]], on="district", how="left")
        hover = []
        for _, row in map_df.iterrows():
            hover.append(
                f"<b>{row['district']}</b><br>중앙 월세: {fmt_int(row.get('monthly_median'), '만원')}<br>중앙 보증금: {fmt_int(row.get('deposit_median'), '만원')}<br>계약 건수: {fmt_int(row.get('listings'), '건')}"
            )
        fig.add_trace(
            go.Scattermapbox(
                lat=map_df["lat"],
                lon=map_df["lon"],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=map_df["monthly_median"].fillna(0).clip(lower=20).div(2).clip(12, 32),
                    color=map_df["monthly_median"],
                    colorscale="YlOrRd",
                    showscale=True,
                    colorbar=dict(title="중앙 월세(만원)"),
                    opacity=0.55,
                ),
                text=map_df["district"] if show_labels else None,
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover,
                name="월세 요약",
            )
        )

    for category in selected_categories:
        category_df = active_points[active_points["category"] == category].copy()
        if category_df.empty:
            continue
        fig.add_trace(
            go.Scattermapbox(
                lat=category_df["lat"],
                lon=category_df["lon"],
                mode="markers+text" if show_labels else "markers",
                text=category_df["name"] if show_labels else None,
                textposition="top right",
                marker=go.scattermapbox.Marker(size=9, color=CATEGORY_META[category]["color"], opacity=0.88),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>구: %{customdata[1]}<br>주소: %{customdata[2]}<extra></extra>"
                ),
                customdata=category_df[["name", "district", "address"]].fillna("-").values,
                name=category,
            )
        )

    center_lat = active_points["lat"].mean() if not active_points.empty else 37.5665
    center_lon = active_points["lon"].mean() if not active_points.empty else 126.9780
    if selected_district != "전체":
        district_center = centers[centers["district"] == selected_district]
        if not district_center.empty:
            center_lat = district_center.iloc[0]["lat"]
            center_lon = district_center.iloc[0]["lon"]

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=10.0 if selected_district == "전체" else 12.1,
        mapbox_center={"lat": center_lat, "lon": center_lon},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📌 선택 지역 요약")
    summary_df = pd.DataFrame([
        {"항목": "공원", "개수": int((active_points["category"] == "공원").sum())},
        {"항목": "도서관", "개수": int((active_points["category"] == "도서관").sum())},
        {"항목": "문화공간", "개수": int((active_points["category"] == "문화공간").sum())},
        {"항목": "전통시장", "개수": int(active_markets["market_name"].nunique()) if not active_markets.empty else 0},
        {"항목": "지하철역", "개수": int(active_subway["name"].nunique()) if not active_subway.empty else 0},
    ])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("### 🛒 장보기 물가 바스켓")
    if active_basket_total.empty:
        st.info("선택 조건에 해당하는 전통시장 물가 데이터가 없습니다.")
    else:
        basket_rank = active_basket_total.sort_values("basket_total")
        st.dataframe(
            basket_rank.rename(columns={"district": "자치구", "basket_total": "바스켓 총액(원)", "basket_item_count": "품목수"}),
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("💸 자치구별 월세 비교")
    rank_df = map_rent.sort_values("monthly_median", ascending=False).copy()
    if rank_df.empty:
        st.info("표시할 월세 데이터가 없습니다.")
    else:
        rank_fig = px.bar(
            rank_df,
            x="district",
            y="monthly_median",
            hover_data={"deposit_median": True, "area_median": True, "listings": True},
            labels={"district": "자치구", "monthly_median": "중앙 월세(만원)"},
        )
        rank_fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(rank_fig, use_container_width=True)

with chart_col2:
    st.subheader("📈 월세 추이")
    trend_df = active_month.sort_values("contract_month").copy()
    if selected_building_type != "전체" and selected_district != "전체":
        st.caption("월별 요약은 자치구 기준으로 제공됩니다. 건물유형별 월 추이는 현재 미지원입니다.")
    if trend_df.empty:
        st.info("표시할 월별 데이터가 없습니다.")
    else:
        trend_fig = px.line(
            trend_df,
            x="contract_month",
            y="monthly_median",
            color="district" if selected_district == "전체" else None,
            markers=True,
            labels={"contract_month": "계약월", "monthly_median": "중앙 월세(만원)", "district": "자치구"},
        )
        trend_fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(trend_fig, use_container_width=True)

bottom1, bottom2 = st.columns(2)
with bottom1:
    st.subheader("🏘️ 동별 월세 상위 지역")
    if active_dong.empty:
        st.info("표시할 동별 데이터가 없습니다.")
    else:
        st.dataframe(
            active_dong.sort_values("monthly_median", ascending=False)
            .head(15)
            .rename(columns={
                "district": "자치구",
                "dong": "법정동",
                "monthly_median": "중앙 월세(만원)",
                "deposit_median": "중앙 보증금(만원)",
                "area_median": "중앙 면적(㎡)",
                "listings": "계약 건수",
                "latest_contract": "최근 계약일",
            }),
            use_container_width=True,
            hide_index=True,
        )

with bottom2:
    st.subheader("🏢 건물유형별 월세")
    building_view = rent_building.copy() if selected_district == "전체" else rent_building[rent_building["district"] == selected_district].copy()
    if building_view.empty:
        st.info("표시할 건물유형 데이터가 없습니다.")
    else:
        st.dataframe(
            building_view.sort_values(["district", "monthly_median"], ascending=[True, False]).rename(columns={
                "district": "자치구",
                "building_type": "건물유형",
                "monthly_median": "중앙 월세(만원)",
                "deposit_median": "중앙 보증금(만원)",
                "area_median": "중앙 면적(㎡)",
                "listings": "계약 건수",
                "latest_contract": "최근 계약일",
            }),
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")
list_col1, list_col2 = st.columns(2)

with list_col1:
    st.subheader("🚇 인근 지하철역")
    if active_subway.empty:
        st.info("해당 조건에 맞는 지하철역 정보가 없습니다.")
    else:
        subway_view = active_subway[["district", "line", "name", "road_address", "phone"]].copy()
        subway_view.columns = ["자치구", "호선", "역명", "주소", "전화번호"]
        st.dataframe(subway_view.sort_values(["자치구", "호선", "역명"]), use_container_width=True, hide_index=True, height=420)

with list_col2:
    st.subheader("🛍️ 전통시장")
    if active_markets.empty:
        st.info("해당 조건에 맞는 전통시장 정보가 없습니다.")
    else:
        market_view = active_markets.copy()
        market_view["latest_check"] = market_view["latest_check"].dt.strftime("%Y-%m-%d")
        market_view.columns = ["자치구", "시장명", "품목수", "최근 점검일"]
        st.dataframe(market_view.sort_values(["자치구", "시장명"]), use_container_width=True, hide_index=True, height=420)

st.subheader("🧺 품목별 평균 가격")
if active_basket.empty:
    st.info("품목별 평균 가격 데이터가 없습니다.")
else:
    basket_table = active_basket.copy().rename(columns={
        "district": "자치구",
        "item_name": "품목",
        "avg_price": "평균 가격(원)",
        "markets": "반영 시장 수",
    })
    st.dataframe(basket_table.sort_values(["자치구", "품목"]), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "데이터 출처: 업로드된 서울시 공공데이터 파일. 월세는 대용량 원본 CSV를 직접 올리지 않고, 미리 생성한 요약 파일(자치구/건물유형/동별/월별)로 제공됩니다."
)
