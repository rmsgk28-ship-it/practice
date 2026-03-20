
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import re
from io import BytesIO

st.set_page_config(page_title="서울, 처음이니? : 어디서 자취할까?", page_icon="🏠", layout="wide")

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
h1, h2, h3 {letter-spacing: -0.02em;}
.small-help {color:#5f6368; font-size:0.92rem;}
.metric-card{
    background:#ffffff;
    border:1px solid #e8eef5;
    border-radius:18px;
    padding:18px 18px 14px 18px;
    box-shadow:0 4px 18px rgba(15,23,42,0.06);
    height:100%;
}
.metric-label{font-size:0.9rem; color:#667085; margin-bottom:6px;}
.metric-value{font-size:1.8rem; font-weight:800; color:#111827; line-height:1.1;}
.metric-sub{font-size:0.85rem; color:#6b7280; margin-top:6px;}
.reco-card{
    background:linear-gradient(180deg,#ffffff 0%, #f8fbff 100%);
    border:1px solid #dbe8ff;
    border-radius:20px;
    padding:18px;
    box-shadow:0 8px 28px rgba(37,99,235,0.08);
    margin-bottom:12px;
}
.reco-rank{font-size:0.92rem; color:#2563eb; font-weight:700;}
.reco-title{font-size:1.4rem; font-weight:800; color:#111827; margin:4px 0 8px 0;}
.reco-meta{font-size:0.92rem; color:#374151; line-height:1.7;}
.badge{
    display:inline-block; padding:4px 10px; border-radius:999px;
    background:#eef4ff; color:#1d4ed8; font-size:0.8rem; font-weight:700; margin-right:6px; margin-top:4px;
}
.tip-box{
    background:#fffaf0; border:1px solid #fde68a; color:#92400e;
    border-radius:14px; padding:14px 16px; font-size:0.95rem;
}
.section-card{
    background:#ffffff;
    border:1px solid #eceff3;
    border-radius:20px;
    padding:18px;
}
.table-note{font-size:0.84rem; color:#6b7280;}
</style>
""", unsafe_allow_html=True)

DISTRICTS = ["강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
             "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
             "용산구","은평구","종로구","중구","중랑구"]

DISTRICT_CENTERS = {
"강남구":[37.5172,127.0473],"강동구":[37.5301,127.1238],"강북구":[37.6397,127.0257],"강서구":[37.5509,126.8495],
"관악구":[37.4784,126.9516],"광진구":[37.5385,127.0822],"구로구":[37.4954,126.8874],"금천구":[37.4602,126.9006],
"노원구":[37.6542,127.0568],"도봉구":[37.6688,127.0471],"동대문구":[37.5744,127.0395],"동작구":[37.5124,126.9393],
"마포구":[37.5663,126.9014],"서대문구":[37.5791,126.9368],"서초구":[37.4837,127.0324],"성동구":[37.5634,127.0366],
"성북구":[37.5894,127.0167],"송파구":[37.5145,127.1059],"양천구":[37.5169,126.8664],"영등포구":[37.5264,126.8962],
"용산구":[37.5326,126.9900],"은평구":[37.6027,126.9291],"종로구":[37.5735,126.9788],"중구":[37.5640,126.9970],
"중랑구":[37.6063,127.0927]
}

EMBEDDED_RENT = {
"강남구":95,"강동구":72,"강북구":62,"강서구":68,"관악구":60,"광진구":78,"구로구":63,"금천구":58,"노원구":60,"도봉구":55,
"동대문구":68,"동작구":75,"마포구":85,"서대문구":70,"서초구":92,"성동구":80,"성북구":65,"송파구":88,"양천구":70,"영등포구":75,
"용산구":82,"은평구":63,"종로구":75,"중구":78,"중랑구":60
}

EMBEDDED_DISTRICT_INFO = {
"강남구":{"subway":["2호선","3호선","7호선","9호선","수인분당선","신분당선"],
          "summary":"직주근접, 보안, 편의시설은 매우 뛰어나지만 월세와 관리비 부담이 크고 생활 전반의 비용이 높습니다.",
          "pros":["업무지구 접근성 우수","생활 인프라와 브랜드 상권 밀집","늦은 귀가 동선이 비교적 안정적"],
          "cons":["월세 외 관리비 체감 부담 큼","외곽 원룸 골목은 경사·노후 건물 이슈","예산이 낮으면 선택지가 급격히 줄어듦"]},
"관악구":{"subway":["2호선","신림선"],
          "summary":"가성비와 청년 친화성이 강점인 대표 자취권입니다. 다만 골목 경사와 밀집 주거 특성은 체크가 필요합니다.",
          "pros":["월세 접근성이 좋음","서울대·신림·강남/여의도 통근 밸런스","청년 대상 식당/생활 서비스 풍부"],
          "cons":["봉천·고시촌 일부는 경사와 노후도 높음","원룸 밀집 지역 소음 편차 큼","배달 오토바이 통행이 잦은 골목 존재"]},
"마포구":{"subway":["2호선","5호선","6호선","경의중앙선","공항철도"],
          "summary":"홍대·합정·공덕 생활권의 문화 밀도는 매우 높지만 월세와 생활물가가 빠르게 올라 예산 관리가 중요합니다.",
          "pros":["문화공간·카페·야간 상권 강함","연세·이화·서강 및 DMC 접근성 우수","평지 동선이 상대적으로 많은 편"],
          "cons":["상권 인접 골목은 소음·관광객 유입 부담","월세 외 식비·카페비 지출 증가","핫플 주변은 주거 안정감 편차 큼"]},
"광진구":{"subway":["2호선","5호선","7호선"],
          "summary":"건대입구·자양·구의 생활권은 대학가와 업무권의 중간지점으로 밸런스가 좋지만 핫플화로 가격이 상승 중입니다.",
          "pros":["건국대·세종대 접근성 우수","2·7호선 더블 역세권 장점","성수/강남 이동이 편리"],
          "cons":["상권 주변 야간 소음이 큼","골목 주차난·체증 체감 가능","성수 인접 지역은 월세 상승 압력 존재"]},
"동대문구":{"subway":["1호선","2호선","5호선","경의중앙선","경춘선","수인분당선"],
          "summary":"회기·이문·장안 일대는 대학 접근성이 좋고 상대적으로 예산 친화적이지만 노후 인프라가 섞여 있습니다.",
          "pros":["경희대·시립대·외대 접근성 장점","예산 대비 면적 선택지 존재","청량리·회기 교통 허브 활용 가능"],
          "cons":["지역별 노후 원룸 편차 큼","일부 골목은 밤 분위기 확인 필요","대형 상권은 외부 이동 의존"]},
"성북구":{"subway":["4호선","6호선","우이신설선"],
          "summary":"안암·성신여대·정릉 생활권은 대학가 중심이라 공부와 생활 균형이 좋고 비교적 차분합니다.",
          "pros":["고려대·성신여대 접근성 우수","대학가 식당/카페 가격이 무난","조용한 골목 선택지가 있음"],
          "cons":["언덕·오르막 체감 지역 존재","노후 주택 비중 확인 필요","관광·업무 중심 상권은 상대적으로 약함"]},
"동작구":{"subway":["1호선","2호선","4호선","7호선","9호선","신림선"],
          "summary":"노량진·흑석·사당 쪽은 통학과 직주근접의 중간 해법이지만 역세권 여부에 따라 만족도가 크게 달라집니다.",
          "pros":["중앙대·숭실대·여의도/강남 접근성 우수","노선 선택 폭이 넓음","생활권이 다양해 취향별 선택 가능"],
          "cons":["역세권과 비역세권 체감 차이 큼","언덕·대단지 인접 주거 혼재","신축/신규 오피스텔은 예산 상승"]},
"성동구":{"subway":["2호선","3호선","5호선","수인분당선","경의중앙선"],
          "summary":"왕십리·성수 영향권으로 교통과 트렌드가 강점인 지역이지만 최근 월세 상승 폭이 큰 편입니다.",
          "pros":["한양대·성수·강남·종로 접근성 좋음","복합 환승 장점","문화/상권 선택지 풍부"],
          "cons":["성수 인접 지역은 예산 상승","상업지역 인접 주거지 소음 가능","가성비 매물 탐색 난도 높음"]},
"서대문구":{"subway":["2호선","3호선","5호선","경의중앙선"],
          "summary":"신촌·이대·홍제 등 생활권 차이가 커서 대학가 중심으로 고르면 만족도가 높고, 주거지는 차분한 편을 고를 수 있습니다.",
          "pros":["연세·이화·서강 통학 강점","신촌권 문화 접근성 우수","주거·상권 분리 선택 가능"],
          "cons":["신촌권은 월세/소음 부담","홍제 등 일부는 언덕 존재","역과 거리 차이가 만족도에 영향"]},
"용산구":{"subway":["1호선","4호선","6호선","경의중앙선","공항철도"],
          "summary":"서울 중심 업무권 접근성과 교통이 뛰어나지만 예산 부담이 크고 생활비도 높은 편입니다.",
          "pros":["서울 전역 이동 편리","환승 노선 다양","상권·공원·업무권 밸런스"],
          "cons":["월세가 높음","주거 면적 대비 비용 부담","핫플 인접 지역은 관광객 유입 존재"]},
}

DEFAULT_UNI_TO_DISTRICTS = {
"선택 안 함": [],
"서울대학교": ["관악구","동작구","금천구"],
"연세대학교": ["서대문구","마포구","은평구"],
"이화여자대학교": ["서대문구","마포구","은평구"],
"서강대학교": ["마포구","서대문구","영등포구"],
"홍익대학교": ["마포구","서대문구","영등포구"],
"건국대학교": ["광진구","성동구","송파구"],
"세종대학교": ["광진구","성동구","중랑구"],
"경희대학교": ["동대문구","성북구","중랑구"],
"한국외국어대학교": ["동대문구","성북구","중랑구"],
"서울시립대학교": ["동대문구","성동구","중랑구"],
"고려대학교": ["성북구","동대문구","종로구"],
"성신여자대학교": ["성북구","강북구","종로구"],
"한양대학교": ["성동구","동대문구","광진구"],
"중앙대학교": ["동작구","관악구","영등포구"],
"숭실대학교": ["동작구","관악구","영등포구"],
"숙명여자대학교": ["용산구","마포구","중구"],
"성균관대학교(인문)": ["종로구","성북구","중구"],
"국민대학교": ["성북구","강북구","종로구"],
"덕성여자대학교": ["강북구","노원구","성북구"],
"서울과학기술대학교": ["노원구","중랑구","도봉구"]
}

WORK_TO_DISTRICTS = {
"선택 안 함": [],
"강남역/테헤란로": ["강남구","서초구","송파구","동작구","광진구"],
"여의도": ["영등포구","동작구","관악구","마포구","구로구"],
"광화문/종로": ["종로구","중구","서대문구","성북구","용산구"],
"성수/서울숲": ["성동구","광진구","동대문구","송파구"],
"상암DMC": ["마포구","은평구","서대문구","강서구"],
"구로디지털단지": ["구로구","금천구","관악구","영등포구"],
"삼성역/잠실": ["강남구","송파구","성동구","광진구"],
"판교/분당": ["서초구","강남구","송파구","성남권 통근 가능"],
"마곡": ["강서구","양천구","구로구","영등포구"]
}

COMMUTE_NOTES = {
"서울대학교":"서울대입구역에서 서울대학교까지 셔틀·시내버스로 약 12분 수준으로 통학 동선이 일반적입니다.",
"연세대학교":"신촌역·이대역 생활권은 연세대 접근성이 좋고 도보/마을버스 활용도가 높습니다.",
"건국대학교":"건대입구역 생활권은 도보 통학이 가능해 자전거·도보 만족도가 높은 편입니다.",
"경희대학교":"회기역에서 마을버스/도보를 조합하는 통학 패턴이 일반적이며 정문 오르막을 감안해야 합니다.",
"고려대학교":"안암역 생활권은 도보 통학이 가능해 캠퍼스 근접성이 매우 높습니다."
}

RENT_BANDS = {
"상관없음": (0, 999),
"50만원대 이하": (0, 59),
"60만원대": (60, 69),
"70만원대": (70, 79),
"80만원대": (80, 89),
"90만원대 이상": (90, 999)
}

EXTENDED_LINES = {
"강남구":["2호선","3호선","7호선","9호선","수인분당선","신분당선"],
"강동구":["5호선","8호선","9호선"],
"강북구":["4호선","우이신설선"],
"강서구":["5호선","9호선","공항철도"],
"관악구":["2호선","신림선"],
"광진구":["2호선","5호선","7호선"],
"구로구":["1호선","2호선","7호선"],
"금천구":["1호선","7호선"],
"노원구":["4호선","6호선","7호선","경춘선"],
"도봉구":["1호선","4호선","7호선"],
"동대문구":["1호선","2호선","5호선","경의중앙선","경춘선","수인분당선"],
"동작구":["1호선","2호선","4호선","7호선","9호선","신림선"],
"마포구":["2호선","5호선","6호선","경의중앙선","공항철도"],
"서대문구":["2호선","3호선","5호선","경의중앙선"],
"서초구":["2호선","3호선","4호선","7호선","9호선","신분당선"],
"성동구":["2호선","3호선","5호선","수인분당선","경의중앙선"],
"성북구":["4호선","6호선","우이신설선"],
"송파구":["2호선","3호선","5호선","8호선","9호선","수인분당선"],
"양천구":["2호선","5호선"],
"영등포구":["1호선","2호선","5호선","7호선","9호선"],
"용산구":["1호선","4호선","6호선","경의중앙선","공항철도"],
"은평구":["3호선","6호선","경의중앙선","공항철도"],
"종로구":["1호선","3호선","4호선","5호선","6호선","경의중앙선"],
"중구":["1호선","2호선","3호선","4호선","5호선","6호선","공항철도"],
"중랑구":["6호선","7호선","경춘선"]
}

def icon_badges(tags):
    return " ".join([f"<span class='badge'>{t}</span>" for t in tags])

# -----------------------------
# 로더
# -----------------------------
def read_csv_safely(path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, engine="python", encoding_errors="ignore")

@st.cache_data(show_spinner=False)
def load_base_data():
    culture = read_csv_safely("서울시 문화공간 정보.csv")
    library = read_csv_safely("서울시 공공도서관 현황정보.csv")
    subway = read_csv_safely("서울교통공사_역주소 및 전화번호.csv")
    prices = read_csv_safely("생필품 농수축산물 가격 정보(2024년).csv")
    parks = pd.read_excel("서울시 주요 공원현황(2026 상반기).xlsx")

    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    library["구명"] = library["구명"].astype(str).str.strip()
    parks["지역"] = parks["지역"].astype(str).str.strip()
    prices["자치구 이름"] = prices["자치구 이름"].astype(str).str.strip()

    def extract_district(text):
        if pd.isna(text):
            return None
        m = re.search(r"([가-힣]+구)", str(text))
        return m.group(1) if m else None

    subway["자치구"] = subway["도로명주소"].apply(extract_district).fillna(subway["구주소"].apply(extract_district))
    subway["호선"] = subway["호선"].astype(str).str.strip()
    subway["역명"] = subway["역명"].astype(str).str.strip()

    return culture, library, subway, prices, parks

@st.cache_data(show_spinner=False)
def optional_rent_summary():
    try:
        rent = read_csv_safely("서울특별시_전월세가_2025.csv")
        rent = rent.copy()
        # 월세 계약만
        if "전월세구분" in rent.columns:
            rent = rent[rent["전월세구분"].astype(str).str.contains("월세")]
        if "임대료(만원)" in rent.columns and "자치구명" in rent.columns:
            rent["임대료(만원)"] = pd.to_numeric(rent["임대료(만원)"], errors="coerce")
            rent = rent[rent["임대료(만원)"] > 0]
            by_dist = rent.groupby("자치구명")["임대료(만원)"].mean().reindex(DISTRICTS)
            overall = float(rent["임대료(만원)"].mean())
            return by_dist.fillna(pd.Series(EMBEDDED_RENT)), overall, True
    except Exception:
        pass
    by_dist = pd.Series(EMBEDDED_RENT).reindex(DISTRICTS)
    overall = float(by_dist.mean())
    return by_dist, overall, False

@st.cache_data(show_spinner=False)
def build_district_dataframe():
    culture, library, subway, prices, parks = load_base_data()
    rent_by_dist, seoul_rent_avg, using_rent_csv = optional_rent_summary()

    df = pd.DataFrame(index=DISTRICTS)
    df["월세"] = rent_by_dist
    df["문화공간수"] = culture.groupby("자치구").size().reindex(DISTRICTS).fillna(0)
    df["도서관수"] = library.groupby("구명").size().reindex(DISTRICTS).fillna(0)
    df["공원수"] = parks[parks["지역"].isin(DISTRICTS)].groupby("지역").size().reindex(DISTRICTS).fillna(0)
    df["지하철역수"] = subway.groupby("자치구").size().reindex(DISTRICTS).fillna(0)
    df["생활물가"] = prices.groupby("자치구 이름")["가격(원)"].mean().reindex(DISTRICTS).fillna(prices["가격(원)"].mean()).round()
    df["문화생활지수_raw"] = df["문화공간수"] + df["도서관수"] + df["공원수"]
    df["지하철노선"] = pd.Series({d:", ".join(EXTENDED_LINES.get(d, [])) for d in DISTRICTS})
    df["노선다양성"] = pd.Series({d:len(EXTENDED_LINES.get(d, [])) for d in DISTRICTS})
    df["생활물가"] = df["생활물가"].astype(int)

    # 정규화
    def minmax(s, higher_better=True):
        s = s.astype(float)
        if s.max() == s.min():
            out = pd.Series(0.5, index=s.index)
        else:
            out = (s - s.min()) / (s.max() - s.min())
        return out if higher_better else 1 - out

    df["월세점수"] = minmax(df["월세"], higher_better=False)
    df["물가점수"] = minmax(df["생활물가"], higher_better=False)
    transit_raw = df["지하철역수"] * 0.6 + df["노선다양성"] * 0.4
    df["교통점수_base"] = minmax(transit_raw, higher_better=True)
    culture_raw = df["문화공간수"] * 0.45 + df["도서관수"] * 0.25 + df["공원수"] * 0.30
    df["문화점수_base"] = minmax(culture_raw, higher_better=True)

    return df, culture, library, subway, prices, parks, seoul_rent_avg, using_rent_csv

def compute_priority_weights(rank_map):
    rank_weight = {"1순위":0.4, "2순위":0.3, "3순위":0.2, "4순위":0.1}
    weights = {"월세":0, "생활물가":0, "교통":0, "문화생활":0}
    for rank, item in rank_map.items():
        weights[item] += rank_weight.get(rank, 0)
    return weights

def apply_preference_scoring(df, university, workplace, selected_lines, rent_band, rank_map):
    scored = df.copy()
    weights = compute_priority_weights(rank_map)

    # 교통 가중 보정
    scored["교통매칭"] = 0.0
    pref_districts = set(DEFAULT_UNI_TO_DISTRICTS.get(university, [])) | set(WORK_TO_DISTRICTS.get(workplace, []))
    if pref_districts:
        scored.loc[scored.index.isin(pref_districts), "교통매칭"] += 0.55

    if selected_lines:
        selected_lines = set(selected_lines)
        line_match = []
        for d in scored.index:
            lines = set(EXTENDED_LINES.get(d, []))
            denom = max(len(selected_lines), 1)
            line_match.append(len(lines.intersection(selected_lines)) / denom)
        scored["교통매칭"] += pd.Series(line_match, index=scored.index) * 0.45

    scored["교통점수"] = (scored["교통점수_base"] * 0.65 + scored["교통매칭"] * 0.35).clip(0, 1)
    scored["문화점수"] = scored["문화점수_base"]

    low, high = RENT_BANDS[rent_band]
    rent_fit = scored["월세"].between(low, high) if rent_band != "상관없음" else pd.Series(True, index=scored.index)
    # 밴드 바깥이면 감점만, 완전 제외는 하지 않음
    distance = np.where(rent_fit, 0, np.minimum(abs(scored["월세"]-low), abs(scored["월세"]-high)))
    if distance.max() == distance.min():
        penalty = pd.Series(1.0, index=scored.index)
    else:
        penalty = 1 - (pd.Series(distance, index=scored.index) / max(distance.max(), 1))
    scored["월세적합도"] = penalty

    scored["추천점수"] = (
        scored["월세점수"] * weights["월세"] * 0.75 + scored["월세적합도"] * weights["월세"] * 0.25 +
        scored["물가점수"] * weights["생활물가"] +
        scored["교통점수"] * weights["교통"] +
        scored["문화점수"] * weights["문화생활"]
    )

    return scored.sort_values("추천점수", ascending=False), weights

def culture_summary_for_district(culture_df, district):
    c = culture_df[culture_df["자치구"] == district].copy()
    if c.empty:
        return {}, pd.DataFrame(columns=["주제분류", "문화시설명", "주소"])
    type_counts = c["주제분류"].fillna("기타").value_counts().to_dict()
    top_examples = c[["주제분류", "문화시설명", "주소"]].fillna("").head(8)
    return type_counts, top_examples

def top_facility_examples(culture_df, district):
    c = culture_df[culture_df["자치구"] == district].copy()
    if c.empty:
        return []
    grouped = c.groupby("주제분류")["문화시설명"].apply(lambda s: ", ".join(s.head(2).tolist())).to_dict()
    return grouped

def district_story(district, row):
    if district in EMBEDDED_DISTRICT_INFO:
        return EMBEDDED_DISTRICT_INFO[district]
    # generic fallback
    story = {"subway":EXTENDED_LINES.get(district, []), "summary":"생활 인프라와 예산 밸런스를 함께 살펴봐야 하는 지역입니다.", "pros":[], "cons":[]}
    if row["월세"] <= 65:
        story["pros"].append("서울 평균 대비 월세 접근성이 좋은 편")
    else:
        story["cons"].append("서울 평균보다 월세가 높은 편")
    if row["문화생활지수_raw"] >= 80:
        story["pros"].append("문화/공원/도서관 등 여가 인프라가 풍부")
    else:
        story["pros"].append("조용하고 생활형 주거지를 찾기 쉬운 편")
    if row["노선다양성"] >= 5:
        story["pros"].append("환승 가능한 노선이 다양해 이동성이 좋음")
    else:
        story["cons"].append("주요 상권/업무지 이동 시 환승이 필요할 수 있음")
    return story

def low_budget_warning(rent_band, seoul_avg):
    if rent_band in ["50만원대 이하", "60만원대"] and RENT_BANDS[rent_band][1] < seoul_avg:
        return True
    return False

def render_metric_card(label, value, sub=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def build_geojson_map(scored_df, seoul_rent_avg, selected_district=None):
    m = folium.Map(location=[37.56, 126.98], zoom_start=10.6, tiles="CartoDB positron")
    try:
        url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"
        gj = requests.get(url, timeout=10).json()
        score_map = scored_df["추천점수"].to_dict()
        rent_map = scored_df["월세"].to_dict()
        price_map = scored_df["생활물가"].to_dict()

        for feat in gj["features"]:
            name = feat["properties"].get("name")
            feat["properties"]["추천점수"] = round(float(score_map.get(name, 0)), 3)
            feat["properties"]["월세"] = int(round(float(rent_map.get(name, seoul_rent_avg))))
            feat["properties"]["생활물가"] = int(round(float(price_map.get(name, 0))))

        folium.Choropleth(
            geo_data=gj,
            data=scored_df.reset_index(),
            columns=["index", "추천점수"],
            key_on="feature.properties.name",
            fill_color="Blues",
            fill_opacity=0.75,
            line_opacity=0.6,
            legend_name="추천 점수"
        ).add_to(m)

        highlight = {"weight": 3, "color": "#1d4ed8", "fillOpacity": 0.85}
        default_style = lambda feature: {
            "fillColor": "#dbeafe" if feature["properties"]["name"] == selected_district else "#f8fafc",
            "color": "#94a3b8",
            "weight": 1.2,
            "fillOpacity": 0.18 if feature["properties"]["name"] != selected_district else 0.35
        }
        popup_fields = ["name", "추천점수", "월세", "생활물가"]
        popup_aliases = ["자치구", "추천점수", "평균 월세(만원)", "생활물가 평균(원)"]
        folium.GeoJson(
            gj,
            style_function=default_style,
            highlight_function=lambda x: highlight,
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "추천점수", "월세"],
                aliases=["자치구", "추천점수", "월세(만원)"],
                sticky=True
            ),
            popup=folium.GeoJsonPopup(fields=popup_fields, aliases=popup_aliases, labels=True)
        ).add_to(m)
    except Exception:
        for d, (lat, lon) in DISTRICT_CENTERS.items():
            val = scored_df.loc[d, "추천점수"] if d in scored_df.index else 0
            folium.CircleMarker(
                [lat, lon], radius=8, color="#2563eb", fill=True, fill_opacity=0.85,
                popup=f"{d}<br>추천점수: {val:.2f}<br>월세: {int(scored_df.loc[d, '월세'])}만원"
            ).add_to(m)
    return m

def compare_commute_message(district, university, workplace, selected_lines):
    msgs = []
    if university != "선택 안 함":
        preferred = DEFAULT_UNI_TO_DISTRICTS.get(university, [])
        if district in preferred:
            msgs.append(f"{university} 기준 통학 후보권에 포함됩니다.")
        if university in COMMUTE_NOTES:
            msgs.append(COMMUTE_NOTES[university])
    if workplace != "선택 안 함":
        preferred = WORK_TO_DISTRICTS.get(workplace, [])
        if district in preferred:
            msgs.append(f"{workplace} 기준 출근 밸런스가 좋은 후보입니다.")
    if selected_lines:
        matched = sorted(set(EXTENDED_LINES.get(district, [])).intersection(selected_lines))
        if matched:
            msgs.append(f"선택한 노선과 겹치는 노선: {', '.join(matched)}")
        else:
            msgs.append("선택한 노선과 직접 겹치지 않아 환승 가능성을 확인해야 합니다.")
    return " ".join(msgs)

def rent_comparison_text(rent, seoul_avg):
    diff = rent - seoul_avg
    if diff <= -8:
        return f"서울 평균보다 약 {abs(diff):.0f}만원 저렴해 예산상 장점이 큽니다."
    elif diff < 0:
        return f"서울 평균보다 약 {abs(diff):.0f}만원 저렴한 편입니다."
    elif diff <= 8:
        return f"서울 평균보다 약 {diff:.0f}만원 높은 편입니다."
    return f"서울 평균보다 약 {diff:.0f}만원 높아 예산 여유가 있으면 적합합니다."

def 생활팁(district):
    tips = {
        "관악구":"봉천·신림은 경사와 골목 밀도를 반드시 현장 확인하세요. 역에서 도보 10분 이내인지가 만족도를 크게 좌우합니다.",
        "마포구":"상권 바로 뒤 원룸은 늦은 밤 소음 편차가 큽니다. 주말 체류 인구를 직접 체감해 보고 계약하는 편이 안전합니다.",
        "광진구":"건대입구 상권 인접지는 밤 소음 체크가 필수입니다. 세종대·건대 통학이면 골목 안쪽 평지 라인을 우선 보세요.",
        "동대문구":"회기·이문은 학교 접근성이 좋지만 건물 노후도 차이가 큽니다. 보일러/단열/엘리베이터 유무를 꼭 확인하세요.",
        "성북구":"안암·성신여대권은 언덕 차이가 큽니다. 야간 귀가 동선과 오르막 체감이 중요한 기준입니다.",
        "강남구":"월세뿐 아니라 관리비·식비·카페비까지 합친 총 생활비를 따져야 실제 체감 예산이 맞습니다."
    }
    return tips.get(district, "역세권 여부, 언덕, 밤길 분위기, 관리비를 함께 확인하면 실패 확률이 줄어듭니다.")

# -----------------------------
# 데이터 준비
# -----------------------------
df, culture, library, subway, prices, parks, seoul_rent_avg, using_rent_csv = build_district_dataframe()
seoul_price_avg = int(round(df["생활물가"].mean()))

# -----------------------------
# 헤더
# -----------------------------
st.title("서울, 처음이니? : 어디서 자취할까?")
st.markdown('<div class="small-help">월세 · 생활물가 · 교통 · 문화생활을 조합해 서울 자취 지역을 추천합니다. 교통 우선일 경우 재학 중인 대학교 / 근무지 / 희망 노선을 함께 반영하세요.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("우선순위 설정")
    st.caption("1순위일수록 추천 점수에 더 크게 반영됩니다. (1순위 40%, 2순위 30%, 3순위 20%, 4순위 10%)")
    options = ["월세", "생활물가", "교통", "문화생활"]
    p1 = st.selectbox("1순위", options, index=0)
    p2 = st.selectbox("2순위", options, index=2)
    p3 = st.selectbox("3순위", options, index=3)
    p4 = st.selectbox("4순위", options, index=1)
    if len({p1,p2,p3,p4}) < 4:
        st.warning("1~4순위는 서로 다른 항목으로 선택해 주세요.")
    rank_map = {"1순위":p1, "2순위":p2, "3순위":p3, "4순위":p4}

    st.divider()
    rent_band = st.selectbox("희망 월세 가격대", list(RENT_BANDS.keys()), index=2)
    university = st.selectbox("재학 중인 대학교", list(DEFAULT_UNI_TO_DISTRICTS.keys()))
    workplace = st.selectbox("근무지", list(WORK_TO_DISTRICTS.keys()))
    all_lines = sorted({line for lines in EXTENDED_LINES.values() for line in lines})
    selected_lines = st.multiselect("희망 지하철 노선(복수 선택 가능)", all_lines, placeholder="예: 2호선, 경의중앙선")

    st.divider()
    st.markdown("**우선순위 기준 간단 안내**")
    st.markdown("""
    - **월세**: 월 고정비 부담을 가장 중요하게 볼 때  
    - **생활물가**: 장보기/식비/기본 생필품 지출을 아끼고 싶을 때  
    - **교통**: 통학·출근 시간과 노선 환승 편의를 중시할 때  
    - **문화생활**: 공원·산책·도서관·전시/공연 같은 여가와 공부환경을 중시할 때
    """)

scored_df, weights = apply_preference_scoring(df, university, workplace, selected_lines, rent_band, rank_map)
top5 = scored_df.head(5)

# -----------------------------
# 상단 요약 카드
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("서울 평균 월세", f"{int(round(seoul_rent_avg))}만원",
                       "전월세 CSV가 있으면 실거래 월세 평균, 없으면 보고서 기반 요약값 사용")
with c2:
    render_metric_card("서울 생활물가 평균", f"{seoul_price_avg:,}원", "정수 반올림 기준")
with c3:
    top1 = top5.index[0]
    render_metric_card("현재 추천 1위", top1, rent_comparison_text(top5.iloc[0]["월세"], seoul_rent_avg))
with c4:
    render_metric_card("교통 반영", "대학교·근무지·노선",
                       "교통을 우선순위로 둘수록 해당 조건이 점수에 크게 반영됩니다.")

if low_budget_warning(rent_band, seoul_rent_avg):
    st.markdown("""
    <div class="tip-box">
    <b>저예산 안내</b><br>
    서울 평균 월세보다 낮은 가격대를 선택했어요. 예산상 장점은 크지만, 실제로는 역과 거리, 언덕/골목, 건물 노후도, 관리비, 밤길 분위기 차이가 매우 크게 나타날 수 있어요.
    계약 전에는 <b>관리비·반지층 여부·엘리베이터·채광·골목 소음</b>까지 꼭 확인하세요.
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# 메인 탭
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["추천 결과", "비교분석", "지역 상세", "첫 자취 팁"])

with tab1:
    left, right = st.columns([1.1, 1.3], gap="large")
    with left:
        st.subheader("우선순위 기반 추천 지역 TOP 5")
        for idx, (district, row) in enumerate(top5.iterrows(), start=1):
            story = district_story(district, row)
            tags = []
            if row["월세"] <= seoul_rent_avg:
                tags.append("서울 평균보다 저렴")
            if district in DEFAULT_UNI_TO_DISTRICTS.get(university, []):
                tags.append("대학교 접근 후보")
            if district in WORK_TO_DISTRICTS.get(workplace, []):
                tags.append("출근 밸런스")
            if selected_lines and set(selected_lines).intersection(set(EXTENDED_LINES.get(district, []))):
                tags.append("희망 노선 일치")
            if not tags:
                tags = ["균형형 추천"]

            st.markdown(f"""
            <div class="reco-card">
                <div class="reco-rank">TOP {idx}</div>
                <div class="reco-title">{district}</div>
                <div>{icon_badges(tags)}</div>
                <div class="reco-meta">
                    월세 <b>{int(round(row['월세']))}만원</b> · 생활물가 <b>{int(round(row['생활물가'])):,}원</b><br>
                    교통 노선: {", ".join(EXTENDED_LINES.get(district, []))}<br>
                    {story["summary"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.subheader("서울 자치구 지도")
        selected_district = st.selectbox("지도와 함께 볼 지역 선택", DISTRICTS, index=DISTRICTS.index(top1))
        fmap = build_geojson_map(scored_df, seoul_rent_avg, selected_district=selected_district)
        st_folium(fmap, width=None, height=620)

        row = scored_df.loc[selected_district]
        story = district_story(selected_district, row)
        st.markdown(f"""
        <div class="section-card">
            <h4 style="margin-top:0;">{selected_district} 한눈에 보기</h4>
            <div class="reco-meta">
                월세 {int(round(row['월세']))}만원 · 서울 평균 대비 {row['월세']-seoul_rent_avg:+.0f}만원<br>
                생활물가 {int(round(row['생활물가'])):,}원 · 문화생활지수 {int(row['문화생활지수_raw'])} · 지하철역 {int(row['지하철역수'])}개
            </div>
            <div class="small-help" style="margin-top:8px;">{compare_commute_message(selected_district, university, workplace, selected_lines)}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("지역 비교분석")
    compare_choices = st.multiselect("비교할 자치구 선택 (최대 3곳)", DISTRICTS, default=list(top5.index[:3]))
    compare_choices = compare_choices[:3]
    if compare_choices:
        comp = scored_df.loc[compare_choices, ["월세","생활물가","문화공간수","도서관수","공원수","지하철역수","추천점수"]].copy()
        comp["월세_vs_서울평균"] = comp["월세"].apply(lambda x: f"{x-seoul_rent_avg:+.0f}만원")
        comp["생활물가_vs_서울평균"] = comp["생활물가"].apply(lambda x: f"{x-seoul_price_avg:+,}원")
        st.dataframe(comp, use_container_width=True)

        chart_df = comp.reset_index().rename(columns={"index":"자치구"})
        fig = px.bar(chart_df, x="자치구", y=["월세","생활물가","지하철역수","문화공간수"], barmode="group",
                     title="선택 지역 핵심 지표 비교")
        st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(len(compare_choices))
        for c, district in zip(cols, compare_choices):
            with c:
                row = scored_df.loc[district]
                story = district_story(district, row)
                st.markdown(f"""
                <div class="section-card">
                    <h4 style="margin-top:0;">{district}</h4>
                    <div class="small-help">{rent_comparison_text(row['월세'], seoul_rent_avg)}</div>
                    <p style="margin:8px 0 6px 0;"><b>지하철 노선</b><br>{", ".join(EXTENDED_LINES.get(district, []))}</p>
                    <p style="margin:8px 0 6px 0;"><b>대학교/근무지 관점</b><br>{compare_commute_message(district, university, workplace, selected_lines)}</p>
                    <p style="margin:8px 0 6px 0;"><b>현실 자취 포인트</b><br>{story["summary"]}</p>
                    <p style="margin:8px 0 0 0;"><b>생활 팁</b><br>{생활팁(district)}</p>
                </div>
                """, unsafe_allow_html=True)

        if len(compare_choices) >= 2:
            best_rent = comp["월세"].idxmin()
            best_price = comp["생활물가"].idxmin()
            best_transit = comp["지하철역수"].idxmax()
            best_culture = (comp["문화공간수"] + comp["도서관수"] + comp["공원수"]).idxmax()
            st.markdown(f"""
            <div class="section-card">
                <h4 style="margin-top:0;">한 줄 정리</h4>
                <div class="reco-meta">
                    월세는 <b>{best_rent}</b>가 가장 부담이 적고, 생활물가는 <b>{best_price}</b>가 가장 낮습니다.  
                    교통은 <b>{best_transit}</b>가 가장 유리하고, 문화생활은 <b>{best_culture}</b>가 가장 풍부합니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("비교할 자치구를 1~3개 선택해 주세요.")

with tab3:
    st.subheader("지역 상세")
    detail_district = st.selectbox("상세하게 볼 자치구", DISTRICTS, index=DISTRICTS.index(top1), key="detail_select")
    row = scored_df.loc[detail_district]
    story = district_story(detail_district, row)
    type_counts, examples = culture_summary_for_district(culture, detail_district)
    top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    library_subset = library[library["구명"] == detail_district][["도서관명","주소"]].head(5)
    park_subset = parks[parks["지역"] == detail_district][["공원명","공원주소"]].head(5)
    subway_subset = subway[subway["자치구"] == detail_district][["호선","역명","도로명주소"]].drop_duplicates().head(12)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        render_metric_card(f"{detail_district} 평균 월세", f"{int(round(row['월세']))}만원", rent_comparison_text(row["월세"], seoul_rent_avg))
    with d2:
        render_metric_card("생활물가 평균", f"{int(round(row['생활물가'])):,}원", f"서울 평균 대비 {int(round(row['생활물가'] - seoul_price_avg)):+,}원")
    with d3:
        render_metric_card("지하철/문화", f"{int(row['지하철역수'])}역 · {int(row['문화공간수'])}곳", "도서관과 공원은 아래에서 함께 확인")
    with d4:
        render_metric_card("교통/통학 메모", "체크", compare_commute_message(detail_district, university, workplace, selected_lines))

    s1, s2 = st.columns([1.1, 0.9], gap="large")
    with s1:
        st.markdown(f"""
        <div class="section-card">
            <h4 style="margin-top:0;">현실 자취생 관점 요약</h4>
            <p>{story["summary"]}</p>
            <p><b>장점</b></p>
            <ul>{"".join([f"<li>{x}</li>" for x in story["pros"]])}</ul>
            <p><b>주의할 점</b></p>
            <ul>{"".join([f"<li>{x}</li>" for x in story["cons"]])}</ul>
            <p><b>생활 팁</b><br>{생활팁(detail_district)}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="table-note">교통 참고: {compare_commute_message(detail_district, university, workplace, selected_lines)}</div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 문화생활 종류")
        if top_types:
            for t, cnt in top_types:
                st.markdown(f"- **{t}**: {cnt}곳")
        else:
            st.write("등록된 문화공간 데이터가 적습니다.")
        st.markdown("#### 대표 문화시설")
        if not examples.empty:
            st.dataframe(examples.rename(columns={"주제분류":"종류","문화시설명":"시설명","주소":"위치"}), use_container_width=True, height=280)
        st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 지하철 노선 & 역")
        st.write(", ".join(EXTENDED_LINES.get(detail_district, [])))
        if not subway_subset.empty:
            st.dataframe(subway_subset.rename(columns={"호선":"노선","역명":"역명","도로명주소":"위치"}), use_container_width=True, height=260)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 도서관 / 공부환경")
        if not library_subset.empty:
            st.dataframe(library_subset.rename(columns={"도서관명":"도서관","주소":"위치"}), use_container_width=True, height=260)
        else:
            st.write("도서관 정보가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### 공원 / 산책 포인트")
        if not park_subset.empty:
            st.dataframe(park_subset.rename(columns={"공원명":"공원","공원주소":"위치"}), use_container_width=True, height=260)
        else:
            st.write("공원 정보가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.subheader("2030 자취생·상경 대학생을 위한 실전 팁")
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("""
        <div class="section-card">
            <h4 style="margin-top:0;">방 보러 갈 때 꼭 체크할 것</h4>
            <ul>
                <li>월세뿐 아니라 <b>관리비</b>, 전기/가스, 인터넷 포함 여부를 함께 확인</li>
                <li><b>역에서 집까지 밤길</b>, 언덕, 골목 폭, 가로등 밝기 직접 확인</li>
                <li><b>반지층·옥탑·필로티</b> 여부와 단열/소음/채광 체크</li>
                <li>옵션보다도 <b>보일러, 배수, 창문, 방음</b> 상태가 실거주 만족도를 좌우</li>
                <li>하루 두 번 이상 지나보며 <b>출근/등교 시간 체감</b> 확인</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class="section-card">
            <h4 style="margin-top:0;">동네 선택 팁</h4>
            <ul>
                <li><b>가성비형</b>: 관악·금천·도봉·중랑처럼 월세 부담이 상대적으로 낮은 지역부터 탐색</li>
                <li><b>통학형</b>: 학교 근처 역 + 마을버스/도보 동선까지 같이 보아야 실패가 적음</li>
                <li><b>문화생활형</b>: 마포·종로·중구·성동은 문화 밀도가 높지만 체감 지출도 커질 수 있음</li>
                <li><b>직주근접형</b>: 강남·서초·영등포·성동은 시간 절약 장점이 크지만 예산 관리가 중요</li>
                <li>처음 서울 자취라면 <b>역세권 10분 이내 + 대로변 접근</b>을 우선 고려하면 안정감이 높음</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 지금 설정한 조건에서 추천 이유 요약")
    st.write(f"- 우선순위: 1순위 {p1} / 2순위 {p2} / 3순위 {p3} / 4순위 {p4}")
    st.write(f"- 희망 월세: {rent_band}")
    if university != "선택 안 함":
        st.write(f"- 재학 중인 대학교: {university}")
    if workplace != "선택 안 함":
        st.write(f"- 근무지: {workplace}")
    if selected_lines:
        st.write(f"- 희망 노선: {', '.join(selected_lines)}")
    st.write(f"- 현재 조건에서 가장 추천되는 지역은 **{top1}** 입니다.")
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("데이터 사용 범위: 서울시 문화공간 정보, 서울시 공공도서관 현황정보, 서울교통공사 역주소/전화번호, 서울시 주요 공원현황, 생필품 농수축산물 가격 정보, 그리고 업로드된 전략/현황 보고서의 월세·생활권 요약값을 함께 사용했습니다.")
