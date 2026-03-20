
import re
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울 자취 추천 플랫폼",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

RENT_BY_DISTRICT = {
    "강남구": 95, "강동구": 72, "강북구": 62, "강서구": 68, "관악구": 60,
    "광진구": 78, "구로구": 63, "금천구": 58, "노원구": 60, "도봉구": 55,
    "동대문구": 68, "동작구": 75, "마포구": 85, "서대문구": 70, "서초구": 92,
    "성동구": 80, "성북구": 65, "송파구": 88, "양천구": 70, "영등포구": 75,
    "용산구": 82, "은평구": 63, "종로구": 75, "중구": 78, "중랑구": 60,
}

DISTRICT_COORDS = {
    "강남구": [37.5172, 127.0473], "강동구": [37.5301, 127.1238], "강북구": [37.6397, 127.0257],
    "강서구": [37.5509, 126.8495], "관악구": [37.4784, 126.9516], "광진구": [37.5385, 127.0822],
    "구로구": [37.4954, 126.8874], "금천구": [37.4602, 126.9006], "노원구": [37.6542, 127.0568],
    "도봉구": [37.6688, 127.0471], "동대문구": [37.5744, 127.0395], "동작구": [37.5124, 126.9393],
    "마포구": [37.5663, 126.9014], "서대문구": [37.5791, 126.9368], "서초구": [37.4837, 127.0324],
    "성동구": [37.5634, 127.0366], "성북구": [37.5894, 127.0167], "송파구": [37.5145, 127.1059],
    "양천구": [37.5169, 126.8664], "영등포구": [37.5264, 126.8962], "용산구": [37.5326, 126.9900],
    "은평구": [37.6027, 126.9291], "종로구": [37.5735, 126.9788], "중구": [37.5640, 126.9970],
    "중랑구": [37.6063, 127.0927],
}

CATEGORY_COLORS = {
    "문화공간": "#7C3AED",
    "도서관": "#2563EB",
    "공원": "#16A34A",
}

DATA_FILES = {
    "culture": "서울시 문화공간 정보.csv",
    "library": "서울시 공공도서관 현황정보.csv",
    "subway": "서울교통공사_역주소 및 전화번호.csv",
    "parks": "서울시 주요 공원현황(2026 상반기).xlsx",
    "price": "생필품 농수축산물 가격 정보(2024년).csv",
}


def apply_style():
    st.markdown(
        """
        <style>
        .stApp {background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 35%, #F8FAFC 100%);}
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px;}
        .hero {
            background: linear-gradient(135deg, #111827 0%, #1D4ED8 55%, #06B6D4 100%);
            padding: 28px 30px;
            border-radius: 24px;
            color: white;
            box-shadow: 0 10px 30px rgba(29,78,216,.18);
            margin-bottom: 18px;
        }
        .hero h1 {font-size: 2.1rem; margin: 0 0 8px 0; line-height: 1.2;}
        .hero p {margin: 0; opacity: 0.92; font-size: 1.02rem;}
        .section-title {
            font-weight: 800; font-size: 1.28rem; margin: 8px 0 12px 0; color: #111827;
        }
        .soft-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 22px;
            padding: 18px 18px 14px 18px;
            box-shadow: 0 8px 24px rgba(15,23,42,.05);
        }
        .rank-card {
            background: #fff;
            border: 1px solid #E5E7EB;
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 8px 24px rgba(15,23,42,.05);
            min-height: 190px;
        }
        .badge {
            display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 0.8rem;
            font-weight: 700; background: #EEF2FF; color: #4338CA; margin-bottom: 10px;
        }
        .mini-kpi {
            background:#F8FAFC; border:1px solid #E5E7EB; border-radius:16px; padding:12px;
            text-align:center; min-height:88px;
        }
        .mini-kpi .label {font-size:0.83rem; color:#64748B;}
        .mini-kpi .value {font-size:1.35rem; font-weight:800; color:#0F172A; margin-top:4px;}
        .reason-box {
            background:#F8FAFC; border-radius:16px; padding:12px 14px; border:1px solid #E5E7EB;
            margin-top: 10px; color:#334155;
        }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            padding: 10px 14px;
            box-shadow: 0 8px 20px rgba(15,23,42,.04);
        }
        .source-note {
            font-size: 0.86rem; color: #475569; line-height: 1.6;
            background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 18px; padding: 14px 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_csv_flexible(path: str) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=enc, engine="python", on_bad_lines="skip")
        except Exception as e:
            last_error = e
    raise last_error


@st.cache_data(show_spinner=False)
def load_data():
    base = Path(".")
    missing = [name for name in DATA_FILES.values() if not (base / name).exists()]
    if missing:
        st.error("다음 파일이 폴더에 없습니다: " + ", ".join(missing))
        st.stop()

    culture = load_csv_flexible(DATA_FILES["culture"])
    library = load_csv_flexible(DATA_FILES["library"])
    subway = load_csv_flexible(DATA_FILES["subway"])
    price = load_csv_flexible(DATA_FILES["price"])
    parks = pd.read_excel(DATA_FILES["parks"])

    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    library["구명"] = library["구명"].astype(str).str.strip()
    parks["지역"] = parks["지역"].astype(str).str.strip()
    price["자치구 이름"] = price["자치구 이름"].astype(str).str.strip()

    def extract_gu(text):
        if pd.isna(text):
            return None
        m = re.search(r"서울특별시\s+([가-힣]+구)", str(text))
        return m.group(1) if m else None

    subway["자치구"] = subway["도로명주소"].apply(extract_gu).fillna(
        subway["구주소"].apply(extract_gu)
    )
    subway["호선"] = subway["호선"].astype(str).str.strip()
    subway = subway[subway["자치구"].isin(RENT_BY_DISTRICT.keys())].copy()

    # Culture
    culture["무료여부_bool"] = culture["무료구분"].astype(str).str.contains("무료", na=False)
    culture_by_gu = culture.groupby("자치구").agg(
        문화공간_수=("문화시설명", "count"),
        문화카테고리_수=("주제분류", "nunique"),
        무료문화비율=("무료여부_bool", "mean"),
    )

    culture_category_counts = (
        culture.groupby(["자치구", "주제분류"]).size().reset_index(name="개수")
    )

    # Libraries
    library_by_gu = library.groupby("구명").agg(
        도서관_수=("도서관명", "count"),
        운영유형_수=("도서관 구분명", "nunique"),
    )

    # Parks
    parks_by_gu = parks.groupby("지역").agg(
        공원_수=("공원명", "count")
    )

    # Subway
    subway_by_gu = subway.groupby("자치구").agg(
        지하철역_수=("역명", "nunique"),
        호선_수=("호선", "nunique"),
    )
    subway_lines_by_gu = (
        subway.groupby("자치구")["호선"]
        .apply(lambda s: ", ".join(sorted(pd.unique(s), key=lambda x: (len(x), x))))
        .to_dict()
    )

    # Price
    price_by_gu = price.groupby("자치구 이름").agg(
        생활물가_평균=("가격(원)", "mean"),
        시장_마트_수=("시장/마트 이름", "nunique"),
        품목_수=("품목 이름", "nunique"),
    )
    price_item_by_gu = (
        price.groupby(["자치구 이름", "품목 이름"])["가격(원)"]
        .mean().reset_index()
    )

    # Master table
    base_df = pd.DataFrame({"자치구": list(RENT_BY_DISTRICT.keys())})
    base_df["예상월세_만원"] = base_df["자치구"].map(RENT_BY_DISTRICT)
    base_df["위도"] = base_df["자치구"].map(lambda x: DISTRICT_COORDS[x][0])
    base_df["경도"] = base_df["자치구"].map(lambda x: DISTRICT_COORDS[x][1])

    master = (
        base_df.merge(culture_by_gu, how="left", left_on="자치구", right_index=True)
        .merge(library_by_gu, how="left", left_on="자치구", right_index=True)
        .merge(parks_by_gu, how="left", left_on="자치구", right_index=True)
        .merge(subway_by_gu, how="left", left_on="자치구", right_index=True)
        .merge(price_by_gu, how="left", left_on="자치구", right_index=True)
    )

    fill_zero_cols = [
        "문화공간_수", "문화카테고리_수", "도서관_수", "운영유형_수",
        "공원_수", "지하철역_수", "호선_수", "시장_마트_수", "품목_수"
    ]
    for col in fill_zero_cols:
        master[col] = master[col].fillna(0).astype(int)

    master["무료문화비율"] = master["무료문화비율"].fillna(0.0)
    master["생활물가_평균"] = master["생활물가_평균"].fillna(price["가격(원)"].mean())

    return {
        "master": master,
        "culture": culture,
        "library": library,
        "subway": subway,
        "parks": parks,
        "price": price,
        "culture_category_counts": culture_category_counts,
        "subway_lines_by_gu": subway_lines_by_gu,
        "price_item_by_gu": price_item_by_gu,
    }


def minmax(series: pd.Series, inverse: bool = False) -> pd.Series:
    s = series.astype(float)
    min_v, max_v = s.min(), s.max()
    if max_v == min_v:
        out = pd.Series(np.ones(len(s)), index=s.index)
    else:
        out = (s - min_v) / (max_v - min_v)
    return 1 - out if inverse else out


def format_manwon(x):
    return f"{x:.0f}만원"


def recommend_reason(row, weight_order):
    phrases = {
        "월세점수": f"예상 월세가 {row['예상월세_만원']:.0f}만원대로 비교적 부담이 적어요.",
        "물가점수": f"생활물가 평균이 약 {row['생활물가_평균']:.0f}원 수준으로 안정적이에요.",
        "문화점수": f"문화공간 {int(row['문화공간_수'])}곳, 카테고리 {int(row['문화카테고리_수'])}종으로 문화생활 선택지가 넓어요.",
        "공원점수": f"공원 {int(row['공원_수'])}곳으로 휴식·산책 인프라가 좋아요.",
        "교통점수": f"지하철역 {int(row['지하철역_수'])}개, {row['주요호선']} 중심으로 이동이 편해요.",
        "도서관점수": f"도서관 {int(row['도서관_수'])}곳으로 공부·작업 환경이 좋아요.",
    }
    picked = []
    for col in weight_order:
        if col in phrases and len(picked) < 3:
            picked.append("• " + phrases[col])
    return "<br>".join(picked)


def score_data(master: pd.DataFrame, weights: dict) -> pd.DataFrame:
    df = master.copy()
    df["월세점수"] = minmax(df["예상월세_만원"], inverse=True)
    df["물가점수"] = minmax(df["생활물가_평균"], inverse=True)
    df["문화점수"] = 0.75 * minmax(df["문화공간_수"]) + 0.25 * minmax(df["문화카테고리_수"])
    df["공원점수"] = minmax(df["공원_수"])
    df["교통점수"] = 0.7 * minmax(df["지하철역_수"]) + 0.3 * minmax(df["호선_수"])
    df["도서관점수"] = minmax(df["도서관_수"])

    active = {k: v for k, v in weights.items() if v > 0}
    total_weight = sum(active.values()) if active else 1.0
    df["추천점수"] = 0.0
    for col, w in weights.items():
        df["추천점수"] += df[col] * w
    df["추천점수"] = (df["추천점수"] / total_weight * 100).round(1)

    score_cols = ["월세점수", "물가점수", "문화점수", "공원점수", "교통점수", "도서관점수"]
    df["강점"] = df[score_cols].idxmax(axis=1)
    return df.sort_values(["추천점수", "월세점수"], ascending=[False, False]).reset_index(drop=True)


def safe_select(df, cols):
    return df[[c for c in cols if c in df.columns]].copy()


apply_style()
data = load_data()
master = data["master"]
culture = data["culture"]
library = data["library"]
subway = data["subway"]
parks = data["parks"]
price = data["price"]
culture_category_counts = data["culture_category_counts"]
subway_lines_by_gu = data["subway_lines_by_gu"]
price_item_by_gu = data["price_item_by_gu"]

# Sidebar
with st.sidebar:
    st.markdown("## 우선순위 설정")
    st.caption("중요한 항목에 더 높은 점수를 주세요. 추천점수는 선택한 가중치 기준으로 계산됩니다.")

    max_rent = st.slider("허용 가능한 최대 월세", 55, 100, 75, 1, format="%d만원")

    selected_lines = st.multiselect(
        "꼭 있었으면 하는 지하철 호선",
        options=sorted(subway["호선"].dropna().unique().tolist()),
    )

    w_rent = st.slider("월세 중요도", 0, 5, 5)
    w_price = st.slider("생활물가 중요도", 0, 5, 3)
    w_transit = st.slider("교통(지하철) 중요도", 0, 5, 4)
    w_culture = st.slider("문화생활 중요도", 0, 5, 3)
    w_green = st.slider("공원/녹지 중요도", 0, 5, 2)
    w_library = st.slider("도서관/공부환경 중요도", 0, 5, 2)

    st.markdown("---")
    district_focus = st.selectbox("상세 탐색할 자치구", master["자치구"].tolist(), index=4)

weights = {
    "월세점수": w_rent,
    "물가점수": w_price,
    "교통점수": w_transit,
    "문화점수": w_culture,
    "공원점수": w_green,
    "도서관점수": w_library,
}

scored = score_data(master, weights)
scored["주요호선"] = scored["자치구"].map(subway_lines_by_gu).fillna("-")

filtered = scored[scored["예상월세_만원"] <= max_rent].copy()
if selected_lines:
    for line in selected_lines:
        filtered = filtered[filtered["주요호선"].str.contains(re.escape(line), na=False)]

if filtered.empty:
    filtered = scored.nsmallest(10, "예상월세_만원").copy()
    st.warning("선택한 조건에 정확히 맞는 자치구가 없어, 월세가 낮은 지역 중심으로 대체 추천을 표시합니다.")

top5 = filtered.head(5)
focus_row = scored[scored["자치구"] == district_focus].iloc[0]

st.markdown(
    """
    <div class="hero">
      <h1>서울 자취 추천 플랫폼</h1>
      <p>월세, 생활물가, 지하철, 공원, 도서관, 문화공간 데이터를 합쳐서
      우선순위 기반으로 자취하기 좋은 자치구를 추천합니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("추천 1위", top5.iloc[0]["자치구"], f"점수 {top5.iloc[0]['추천점수']}")
m2.metric("1위 지역 월세", format_manwon(top5.iloc[0]["예상월세_만원"]))
m3.metric("조건 충족 자치구 수", f"{len(filtered)}곳")
m4.metric("분석 문화공간 수", f"{len(culture):,}곳")

tab1, tab2, tab3, tab4 = st.tabs(["추천 결과", "지도 탐색", "지역 상세", "데이터 보기"])

with tab1:
    st.markdown('<div class="section-title">당신의 우선순위 기준 추천 TOP 5</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    weight_order = [k for k, v in sorted(weights.items(), key=lambda x: x[1], reverse=True) if v > 0]

    medals = ["🥇", "🥈", "🥉", "4위", "5위"]
    for idx, (_, row) in enumerate(top5.iterrows()):
        with cols[idx]:
            st.markdown(
                f"""
                <div class="rank-card">
                    <div class="badge">{medals[idx]}</div>
                    <h3 style="margin:0 0 6px 0;">{row['자치구']}</h3>
                    <div style="font-size:1.95rem;font-weight:800;color:#0F172A;line-height:1.1;">{row['추천점수']}</div>
                    <div style="font-size:0.9rem;color:#64748B;margin-bottom:12px;">추천점수 / 100</div>
                    <div class="mini-kpi"><div class="label">예상 월세</div><div class="value">{row['예상월세_만원']:.0f}만원</div></div>
                    <div style="height:8px"></div>
                    <div class="mini-kpi"><div class="label">주요 호선</div><div class="value" style="font-size:1rem;">{row['주요호선']}</div></div>
                    <div class="reason-box">{recommend_reason(row, weight_order)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">추천 순위 전체 보기</div>', unsafe_allow_html=True)
    rank_table = safe_select(
        filtered,
        ["자치구", "추천점수", "예상월세_만원", "생활물가_평균", "문화공간_수", "문화카테고리_수",
         "도서관_수", "공원_수", "지하철역_수", "주요호선"]
    )
    rank_table.columns = ["자치구", "추천점수", "예상 월세(만원)", "생활물가 평균(원)", "문화공간 수", "문화 카테고리 수",
                          "도서관 수", "공원 수", "지하철역 수", "주요 호선"]
    st.dataframe(rank_table, use_container_width=True, hide_index=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig_rank = px.bar(
            filtered.head(10),
            x="자치구",
            y="추천점수",
            color="추천점수",
            color_continuous_scale="Blues",
            text="추천점수",
        )
        fig_rank.update_layout(
            height=430, margin=dict(l=10, r=10, t=20, b=20),
            coloraxis_showscale=False, xaxis_title=None, yaxis_title="추천점수",
        )
        fig_rank.update_traces(textposition="outside")
        st.plotly_chart(fig_rank, use_container_width=True)
    with c2:
        radar_cols = ["월세점수", "물가점수", "문화점수", "공원점수", "교통점수", "도서관점수"]
        radar_labels = ["월세", "물가", "문화", "공원", "교통", "도서관"]
        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[focus_row[c] * 100 for c in radar_cols],
                theta=radar_labels,
                fill="toself",
                name=focus_row["자치구"],
            )
        )
        fig_radar.update_layout(
            height=430,
            margin=dict(l=20, r=20, t=20, b=20),
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

with tab2:
    st.markdown('<div class="section-title">시설 분포 지도</div>', unsafe_allow_html=True)
    cat1, cat2 = st.columns([1, 2])
    with cat1:
        map_scope = st.radio("지도 범위", ["선택한 자치구만", "서울 전체"], horizontal=True)
        show_culture = st.checkbox("문화공간", True)
        show_library = st.checkbox("도서관", True)
        show_parks = st.checkbox("공원", True)
        st.caption("지하철 파일에는 좌표가 없어 지도에는 문화공간·도서관·공원만 표시합니다.")

        district_culture = culture[culture["자치구"] == district_focus].copy()
        district_library = library[library["구명"] == district_focus].copy()
        district_parks = parks[parks["지역"] == district_focus].copy()

        st.markdown(
            f"""
            <div class="soft-card">
              <b>{district_focus}</b><br>
              문화공간 {len(district_culture)}곳 · 도서관 {len(district_library)}곳 · 공원 {len(district_parks)}곳<br>
              지하철역 {int(focus_row['지하철역_수'])}개 · 주요호선 {focus_row['주요호선']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cat2:
        center = DISTRICT_COORDS[district_focus] if map_scope == "선택한 자치구만" else [37.55, 126.98]
        zoom = 12 if map_scope == "선택한 자치구만" else 11
        m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

        # district centers
        if map_scope == "서울 전체":
            for _, row in filtered.head(10).iterrows():
                folium.CircleMarker(
                    location=[row["위도"], row["경도"]],
                    radius=7 + row["추천점수"] / 25,
                    tooltip=f"{row['자치구']} · 추천점수 {row['추천점수']}",
                    popup=folium.Popup(
                        f"<b>{row['자치구']}</b><br>추천점수 {row['추천점수']}<br>"
                        f"예상 월세 {row['예상월세_만원']}만원<br>문화공간 {row['문화공간_수']}곳<br>"
                        f"도서관 {row['도서관_수']}곳<br>공원 {row['공원_수']}곳",
                        max_width=280,
                    ),
                    color="#1D4ED8",
                    fill=True,
                    fill_opacity=0.8,
                ).add_to(m)

        if show_culture:
            cluster = MarkerCluster(name="문화공간").add_to(m)
            target = culture if map_scope == "서울 전체" else district_culture
            target = target.dropna(subset=["위도", "경도"])
            for _, row in target.head(400).iterrows():
                folium.CircleMarker(
                    location=[row["위도"], row["경도"]],
                    radius=4,
                    color=CATEGORY_COLORS["문화공간"],
                    fill=True,
                    fill_opacity=0.75,
                    popup=folium.Popup(
                        f"<b>{row['문화시설명']}</b><br>{row['주제분류']}<br>{row['주소']}",
                        max_width=280,
                    ),
                ).add_to(cluster)

        if show_library:
            cluster = MarkerCluster(name="도서관").add_to(m)
            target = library if map_scope == "서울 전체" else district_library
            target = target.dropna(subset=["위도", "경도"])
            for _, row in target.iterrows():
                folium.CircleMarker(
                    location=[row["위도"], row["경도"]],
                    radius=4,
                    color=CATEGORY_COLORS["도서관"],
                    fill=True,
                    fill_opacity=0.75,
                    popup=folium.Popup(
                        f"<b>{row['도서관명']}</b><br>{row['주소']}", max_width=260
                    ),
                ).add_to(cluster)

        if show_parks:
            cluster = MarkerCluster(name="공원").add_to(m)
            target = parks if map_scope == "서울 전체" else district_parks
            target = target.dropna(subset=["Y좌표(WGS84)", "X좌표(WGS84)"])
            for _, row in target.iterrows():
                folium.CircleMarker(
                    location=[row["Y좌표(WGS84)"], row["X좌표(WGS84)"]],
                    radius=4,
                    color=CATEGORY_COLORS["공원"],
                    fill=True,
                    fill_opacity=0.75,
                    popup=folium.Popup(
                        f"<b>{row['공원명']}</b><br>{row['공원주소']}", max_width=280
                    ),
                ).add_to(cluster)

        folium.LayerControl(collapsed=False).add_to(m)
        st_folium(m, width=None, height=620, returned_objects=[])

with tab3:
    st.markdown(f'<div class="section-title">{district_focus} 상세 분석</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("예상 월세", f"{focus_row['예상월세_만원']:.0f}만원")
    k2.metric("생활물가 평균", f"{focus_row['생활물가_평균']:.0f}원")
    k3.metric("문화공간", f"{int(focus_row['문화공간_수'])}곳")
    k4.metric("도서관 / 공원", f"{int(focus_row['도서관_수'])} / {int(focus_row['공원_수'])}")
    k5.metric("지하철역", f"{int(focus_row['지하철역_수'])}개")

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("#### 이 지역을 추천하는 이유")
        st.markdown(
            f"""
            <div class="soft-card">
            {recommend_reason(focus_row, weight_order)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 문화공간은 무엇이 있나요?")
        district_culture = culture[culture["자치구"] == district_focus].copy()
        district_categories = (
            district_culture["주제분류"].value_counts().rename_axis("문화공간 분류").reset_index(name="개수")
        )
        if not district_categories.empty:
            fig_cat = px.bar(
                district_categories,
                x="문화공간 분류",
                y="개수",
                color="개수",
                color_continuous_scale="Purples",
            )
            fig_cat.update_layout(
                height=320, margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False, xaxis_title=None, yaxis_title=None
            )
            st.plotly_chart(fig_cat, use_container_width=True)

            top_names = (
                district_culture[["주제분류", "문화시설명", "주소"]]
                .sort_values(["주제분류", "문화시설명"])
                .head(18)
            )
            st.dataframe(top_names, use_container_width=True, hide_index=True)
        else:
            st.info("이 자치구의 문화공간 데이터가 없습니다.")

    with right:
        st.markdown("#### 지하철역 / 주요 호선")
        district_subway = subway[subway["자치구"] == district_focus].copy()
        if district_subway.empty:
            st.info("지하철역 정보가 없습니다.")
        else:
            st.markdown(
                f"""
                <div class="soft-card">
                  <b>주요 호선</b><br>{focus_row['주요호선']}<br><br>
                  <b>대표 역</b><br>{", ".join(district_subway['역명'].dropna().unique()[:12])}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.dataframe(
                safe_select(district_subway, ["호선", "역명", "도로명주소", "전화번호"]).rename(
                    columns={"호선": "호선", "역명": "역명", "도로명주소": "주소", "전화번호": "전화번호"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("#### 장보기 물가 예시")
        district_price = price_item_by_gu[price_item_by_gu["자치구 이름"] == district_focus].copy()
        if not district_price.empty:
            district_price = district_price.sort_values("가격(원)").head(12)
            st.dataframe(
                district_price.rename(columns={"자치구 이름": "자치구", "품목 이름": "품목", "가격(원)": "평균가격(원)"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("생활물가 상세 데이터가 없습니다.")

with tab4:
    st.markdown('<div class="section-title">비교 차트와 원본 데이터</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fig_rent = px.scatter(
            scored,
            x="예상월세_만원",
            y="생활물가_평균",
            size="지하철역_수",
            color="추천점수",
            hover_name="자치구",
            color_continuous_scale="Tealgrn",
        )
        fig_rent.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=20),
                               xaxis_title="예상 월세(만원)", yaxis_title="생활물가 평균(원)")
        st.plotly_chart(fig_rent, use_container_width=True)
    with c2:
        fig_fac = px.scatter(
            scored,
            x="문화공간_수",
            y="공원_수",
            size="도서관_수",
            color="추천점수",
            hover_name="자치구",
            color_continuous_scale="Plasma",
        )
        fig_fac.update_layout(height=420, margin=dict(l=10, r=10, t=20, b=20),
                              xaxis_title="문화공간 수", yaxis_title="공원 수")
        st.plotly_chart(fig_fac, use_container_width=True)

    st.markdown("#### 자치구별 종합 데이터")
    view_df = safe_select(
        scored,
        [
            "자치구", "추천점수", "예상월세_만원", "생활물가_평균", "문화공간_수",
            "문화카테고리_수", "도서관_수", "공원_수", "지하철역_수", "호선_수", "주요호선"
        ],
    )
    view_df.columns = [
        "자치구", "추천점수", "예상 월세(만원)", "생활물가 평균(원)", "문화공간 수",
        "문화 카테고리 수", "도서관 수", "공원 수", "지하철역 수", "호선 수", "주요 호선"
    ]
    st.dataframe(view_df, use_container_width=True, hide_index=True)

    st.markdown(
        """
        <div class="source-note">
        <b>데이터 사용 방식</b><br>
        • 예상 월세는 업로드된 자치구 정주여건 보고서의 자치구별 요약값을 사용했습니다.<br>
        • 문화공간/도서관/공원/지하철/생활물가 지표는 업로드한 CSV·XLSX 파일에서 직접 집계했습니다.<br>
        • 문화공간 상세는 ‘주제분류 + 문화시설명 + 주소’까지 보여주도록 구성했습니다.<br>
        • 대용량 전월세 원본 파일은 사용하지 않아도 앱이 동작합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )
