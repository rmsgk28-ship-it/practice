
import json
import math
import os
import re
from io import BytesIO

import branca.colormap as cm
import folium
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
from streamlit_folium import st_folium

st.set_page_config(
    page_title="서울, 처음이니? : 어디서 자취할까?",
    page_icon="🏠",
    layout="wide",
)

# ------------------------------------------------------------
# 스타일
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1320px;}
    html, body, [class*="css"]  {font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Pretendard", sans-serif;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 45%, #10b981 100%);
        border-radius: 28px;
        padding: 28px 28px 24px 28px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
    }
    .hero-title {font-size: 2rem; font-weight: 800; margin-bottom: 8px;}
    .hero-sub {font-size: 1rem; color: rgba(255,255,255,0.92); line-height: 1.6;}
    .mini-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 6px 12px;
        margin-right: 6px;
        margin-top: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        background: rgba(255,255,255,0.16);
        color: white;
        border: 1px solid rgba(255,255,255,0.18);
    }
    .panel {
        background: #ffffff;
        border: 1px solid #e5edf7;
        border-radius: 22px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 10px 30px rgba(15,23,42,0.06);
    }
    .metric-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #dbe7f6;
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 6px 22px rgba(30,41,59,0.06);
        height: 100%;
    }
    .metric-label {font-size: 0.9rem; color: #667085; margin-bottom: 6px;}
    .metric-value {font-size: 1.9rem; line-height: 1.05; font-weight: 800; color: #111827;}
    .metric-desc {font-size: 0.88rem; color: #64748b; margin-top: 8px; line-height: 1.5;}
    .rank-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        border: 1px solid #d9eafe;
        border-radius: 22px;
        padding: 18px;
        min-height: 208px;
        box-shadow: 0 10px 26px rgba(37,99,235,0.08);
    }
    .rank-no {font-size: 0.92rem; color: #2563eb; font-weight: 800;}
    .rank-title {font-size: 1.42rem; font-weight: 900; color: #0f172a; margin: 4px 0 10px 0;}
    .rank-meta {font-size: 0.94rem; color: #334155; line-height: 1.7;}
    .chip {
        display: inline-block; border-radius: 999px; padding: 4px 10px; margin: 0 6px 6px 0;
        background: #eef4ff; color: #1d4ed8; font-size: 0.8rem; font-weight: 700;
    }
    .warn-box {
        background: #fff8eb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        border-radius: 16px;
        padding: 16px 18px;
        color: #92400e;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .success-box {
        background: #effcf6;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        border-radius: 16px;
        padding: 16px 18px;
        color: #166534;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .info-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-left: 5px solid #3b82f6;
        border-radius: 16px;
        padding: 16px 18px;
        color: #1d4ed8;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .subtle {color:#64748b; font-size:0.9rem;}
    .section-title {font-size:1.2rem; font-weight:800; color:#0f172a; margin-bottom:10px;}
    .small {font-size:0.84rem; color:#64748b;}
    .review-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 16px;
    }
    .footer-note {font-size: 0.82rem; color:#6b7280; line-height:1.6;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 999px;
        padding-left: 18px;
        padding-right: 18px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 상수 / 메타데이터
# ------------------------------------------------------------
DISTRICTS = [
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
    "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
    "용산구","은평구","종로구","중구","중랑구"
]

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
    "강남구":95,"강동구":72,"강북구":62,"강서구":68,"관악구":60,"광진구":78,"구로구":63,"금천구":58,"노원구":60,
    "도봉구":55,"동대문구":68,"동작구":75,"마포구":85,"서대문구":70,"서초구":92,"성동구":80,"성북구":65,"송파구":88,
    "양천구":70,"영등포구":75,"용산구":82,"은평구":63,"종로구":75,"중구":78,"중랑구":60
}

DISTRICT_REVIEWS = {
    "강남구": "직주근접은 최고지만 예산이 낮으면 선택지가 빠르게 줄어요. 역세권 신축은 편하지만 관리비까지 꼭 같이 보세요.",
    "강동구": "가족 단위 주거지 느낌이 강해서 조용한 편이에요. 다만 핵심 상권과 조금 떨어진 생활권은 밤에 빨리 한산해집니다.",
    "강북구": "비교적 예산 친화적이고 조용한 주거지가 많아요. 대신 언덕과 역세권 편차를 꼭 체크해야 해요.",
    "강서구": "마곡·발산 접근이 좋아 직장인 수요가 있어요. 공항철도/5호선 활용이 좋은 대신 지역에 따라 이동시간 차이가 큽니다.",
    "관악구": "가성비 자취의 대표 주자예요. 다만 경사, 노후 원룸, 골목 소음 여부는 직접 확인하고 들어가는 게 좋아요.",
    "광진구": "건대 생활권은 재미와 편의가 강점이지만 밤 상권이 활발해서 조용한 집을 원하면 골목 안쪽을 보세요.",
    "구로구": "구디 직장인에게는 현실적인 선택지예요. 주거지는 무난하지만 역과의 거리 차이가 만족도에 크게 작용합니다.",
    "금천구": "예산 대비 교통이 의외로 괜찮은 숨은 카드예요. 다만 생활권이 단조롭게 느껴질 수 있어 문화생활은 외부 의존도가 있어요.",
    "노원구": "대학가와 주거지가 섞여 있어 차분한 편이에요. 북서울권 생활에 익숙하면 만족도가 높고 도심 출퇴근은 다소 길 수 있어요.",
    "도봉구": "월세는 낮은 편이지만 강남·여의도 통근은 길게 느껴질 수 있어요. 조용함을 우선하면 장점이 큽니다.",
    "동대문구": "회기·청량리 쪽은 교통 허브라 편하지만 동네 분위기 차이가 큽니다. 밤길과 노후도를 꼭 확인하세요.",
    "동작구": "통학과 직주근접의 중간 해법으로 좋아요. 다만 흑석·사당·노량진은 지역마다 분위기가 꽤 달라 직접 비교가 중요합니다.",
    "마포구": "문화생활 만족도는 높지만 월세와 생활비가 같이 올라요. 놀기 좋은 동네와 살기 편한 골목을 구분해서 보세요.",
    "서대문구": "신촌권과 주거권의 성격 차이가 큽니다. 대학가를 누리면서도 조용한 곳을 찾으려면 연희·북가좌권도 같이 보세요.",
    "서초구": "교통과 생활 인프라는 훌륭하지만 예산 압박이 큽니다. 반포/서초/방배 생활권의 가격 차이도 큽니다.",
    "성동구": "성수 영향으로 트렌디하고 이동이 편해요. 대신 월세 상승이 빠른 편이라 가성비 매물은 속도가 중요해요.",
    "성북구": "대학가 특유의 공부 분위기와 차분함이 강점이에요. 오르막과 겨울 체감 이동시간을 미리 생각하면 좋아요.",
    "송파구": "생활 인프라와 공원이 좋고 안정감 있는 편이에요. 다만 잠실권은 예산이 높고, 외곽권은 체감 이동시간을 봐야 해요.",
    "양천구": "주거지는 안정적이고 깔끔하지만 문화 상권은 상대적으로 약할 수 있어요. 목동권과 신월/신정권 차이가 큽니다.",
    "영등포구": "여의도 접근성은 좋고 상권도 강합니다. 다만 유동인구가 많고 일부 지역은 밤 분위기 편차가 있어요.",
    "용산구": "서울 중심 접근성은 뛰어나지만 가격이 비쌉니다. 효창·숙대입구 쪽처럼 비교적 차분한 주거권도 함께 살펴보세요.",
    "은평구": "조용하고 주거 안정감이 있어요. 다만 도심권 직장이라면 경의중앙/3·6호선 환승 패턴을 꼭 확인하세요.",
    "종로구": "문화·행정 중심지라 입지는 좋지만 주택 노후도와 생활 소음을 같이 봐야 해요. 혼자 살기엔 취향 차가 큽니다.",
    "중구": "도심 접근성과 편의성은 매우 강하지만 생활비가 높고 주거 공급이 제한적일 수 있어요.",
    "중랑구": "상대적으로 예산 친화적이고 주거용 실거주 만족도가 무난해요. 다만 강남·여의도 접근은 노선 선택에 따라 편차가 큽니다.",
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
    "서울과학기술대학교": ["노원구","중랑구","도봉구"],
}

WORK_TO_DISTRICTS = {
    "선택 안 함": [],
    "강남역/테헤란로": ["강남구","서초구","송파구","동작구","광진구"],
    "여의도": ["영등포구","동작구","마포구","관악구","구로구"],
    "광화문/종로": ["종로구","중구","서대문구","용산구","성북구"],
    "성수/서울숲": ["성동구","광진구","송파구","동대문구"],
    "상암DMC": ["마포구","은평구","서대문구","강서구"],
    "구로디지털단지": ["구로구","금천구","관악구","영등포구"],
    "마곡": ["강서구","양천구","영등포구","구로구"],
    "판교/분당": ["서초구","강남구","송파구"],
    "수원/광교": ["금천구","구로구","강남구"],
}

LINE_PREFS = {
    "1호선","2호선","3호선","4호선","5호선","6호선","7호선","8호선","9호선",
    "경의중앙선","공항철도","경춘선","수인분당선","신분당선","우이신설선","신림선","GTX-A"
}

EXTENDED_LINES = {
    "강남구":["2호선","3호선","7호선","9호선","수인분당선","신분당선","GTX-A"],
    "강동구":["5호선","8호선","9호선"],
    "강북구":["4호선","우이신설선"],
    "강서구":["5호선","9호선","공항철도"],
    "관악구":["2호선","신림선"],
    "광진구":["2호선","5호선","7호선"],
    "구로구":["1호선","2호선","7호선"],
    "금천구":["1호선","7호선","신안산선 예정"],
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
    "영등포구":["1호선","2호선","5호선","7호선","9호선","GTX-A 연계"],
    "용산구":["1호선","4호선","6호선","경의중앙선","공항철도","GTX-A 연계"],
    "은평구":["3호선","6호선","경의중앙선","공항철도","GTX-A"],
    "종로구":["1호선","3호선","4호선","5호선","6호선","경의중앙선"],
    "중구":["1호선","2호선","3호선","4호선","5호선","6호선","공항철도"],
    "중랑구":["6호선","7호선","경춘선"],
}

LINE_CONGESTION = {
    "1호선":0.70, "2호선":0.95, "3호선":0.80, "4호선":0.82, "5호선":0.72, "6호선":0.60,
    "7호선":0.88, "8호선":0.62, "9호선":0.98, "경의중앙선":0.84, "공항철도":0.56,
    "경춘선":0.48, "수인분당선":0.86, "신분당선":0.78, "우이신설선":0.42, "신림선":0.83,
    "GTX-A":0.30, "GTX-A 연계":0.35, "신안산선 예정":0.28
}

LOW_BUDGET_WARNINGS = {
    "도봉구":"예산은 낮지만 강남·여의도 출퇴근이면 이동시간이 길 수 있어요. 통학/통근 우선이면 노선부터 체크하세요.",
    "금천구":"월세는 낮지만 문화 상권은 단조롭게 느껴질 수 있어요. 구디·가산 직장인이 아니면 생활권 취향을 봐야 해요.",
    "관악구":"가성비는 좋지만 경사와 노후 원룸 편차가 큽니다. 직접 밤 동선과 건물 상태를 확인하는 게 중요해요.",
    "중랑구":"주거비 부담은 낮지만 핵심 업무지구 접근은 노선 선택에 따라 차이가 큽니다. 환승 피로를 생각하세요.",
    "강북구":"예산 친화적이지만 언덕과 역세권 거리 편차가 큽니다. 도보 이동 부담을 체크하세요.",
}

CHECKLIST_ITEMS = [
    "등기부등본/전입 가능 여부 확인",
    "관리비 포함 항목 확인(수도/인터넷/공용전기)",
    "밤 10시 이후 골목 동선 직접 확인",
    "세탁기/냉장고/에어컨 옵션 실물 확인",
    "햇빛/환기/곰팡이/결로 여부 확인",
    "주변 편의점·약국·마트·버스정류장 위치 확인",
    "계약 전 인터넷 속도/휴대폰 수신 상태 확인",
    "도보 10분 내 지하철역·자전거 도로·공원 확인",
]

CULTURE_CATEGORY_LABELS = {
    "미술관/갤러리":"미술관·갤러리",
    "공연장":"공연장",
    "박물관/기념관":"박물관·기념관",
    "문화원":"문화원",
    "문화예술회관":"문화예술회관",
    "도서관":"도서관",
    "기타":"복합문화공간·기타",
}

# ------------------------------------------------------------
# 유틸
# ------------------------------------------------------------
def read_csv_safely(path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, engine="python", encoding_errors="ignore")

def format_lines(lines):
    uniq = []
    for line in lines:
        if line not in uniq:
            uniq.append(line)
    return ", ".join(uniq[:8]) if uniq else "-"

def extract_district(text):
    if pd.isna(text):
        return None
    m = re.search(r"([가-힣]+구)", str(text))
    return m.group(1) if m else None

def infer_culture_type(s: str) -> str:
    s = str(s).strip()
    return CULTURE_CATEGORY_LABELS.get(s, s if s else "기타")

def icon_chips(items):
    return "".join([f"<span class='chip'>{x}</span>" for x in items if x])

def commute_bucket(district, destination):
    gbd_fast = {"강남구","서초구","송파구","동작구","성동구","광진구","은평구"}
    ybd_fast = {"영등포구","동작구","마포구","강서구","구로구","관악구"}
    cbd_fast = {"종로구","중구","서대문구","용산구","성북구","동대문구"}
    if destination == "강남":
        return "15~25분" if district in gbd_fast else "30~45분"
    if destination == "여의도":
        return "10~20분" if district in ybd_fast else "30~45분"
    return "15~25분" if district in cbd_fast else "30~40분"

def realistic_tip(district):
    return DISTRICT_REVIEWS.get(district, "역세권 여부와 골목 체감이 만족도를 크게 좌우해요. 예산과 이동시간, 밤 동선을 함께 확인해 보세요.")

# ------------------------------------------------------------
# 데이터 로드
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_base_data():
    culture = read_csv_safely("서울시 문화공간 정보.csv")
    library = read_csv_safely("서울시 공공도서관 현황정보.csv")
    subway = read_csv_safely("서울교통공사_역주소 및 전화번호.csv")
    prices = read_csv_safely("생필품 농수축산물 가격 정보(2024년).csv")
    parks = pd.read_excel("서울시 주요 공원현황(2026 상반기).xlsx")

    # 정리
    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    culture = culture[culture["자치구"].isin(DISTRICTS)].copy()
    culture["문화유형"] = culture["주제분류"].apply(infer_culture_type)
    culture["위도"] = pd.to_numeric(culture["위도"], errors="coerce")
    culture["경도"] = pd.to_numeric(culture["경도"], errors="coerce")

    library["구명"] = library["구명"].astype(str).str.strip()
    library = library[library["구명"].isin(DISTRICTS)].copy()
    library["위도"] = pd.to_numeric(library["위도"], errors="coerce")
    library["경도"] = pd.to_numeric(library["경도"], errors="coerce")

    parks["지역"] = parks["지역"].astype(str).str.strip()
    parks = parks[parks["지역"].isin(DISTRICTS)].copy()
    parks["X좌표(WGS84)"] = pd.to_numeric(parks["X좌표(WGS84)"], errors="coerce")
    parks["Y좌표(WGS84)"] = pd.to_numeric(parks["Y좌표(WGS84)"], errors="coerce")

    prices["자치구 이름"] = prices["자치구 이름"].astype(str).str.strip()
    prices["가격(원)"] = pd.to_numeric(prices["가격(원)"], errors="coerce")
    prices = prices[prices["자치구 이름"].isin(DISTRICTS)].copy()
    price_month = pd.to_datetime(prices["년도-월"], format="%b-%y", errors="coerce")
    latest_month = price_month.max()
    if pd.notna(latest_month):
        prices = prices[price_month == latest_month].copy()

    subway["자치구"] = subway["도로명주소"].apply(extract_district).fillna(subway["구주소"].apply(extract_district))
    subway["자치구"] = subway["자치구"].astype(str).str.strip()
    subway = subway[subway["자치구"].isin(DISTRICTS)].copy()

    return culture, library, subway, prices, parks

@st.cache_data(show_spinner=False)
def load_rent_summary():
    use_csv = False
    seoul_avg = round(np.mean(list(EMBEDDED_RENT.values())), 1)
    rent_df = pd.DataFrame({"자치구": list(EMBEDDED_RENT.keys()), "월세": list(EMBEDDED_RENT.values())})
    if os.path.exists("서울특별시_전월세가_2025.csv"):
        try:
            raw = read_csv_safely("서울특별시_전월세가_2025.csv")
            raw["전월세구분"] = raw["전월세구분"].astype(str)
            raw = raw[raw["전월세구분"].str.contains("월세", na=False)].copy()
            raw["임대료(만원)"] = pd.to_numeric(raw["임대료(만원)"], errors="coerce")
            raw["자치구명"] = raw["자치구명"].astype(str).str.strip()
            raw = raw[raw["자치구명"].isin(DISTRICTS)]
            if not raw.empty:
                summary = raw.groupby("자치구명")["임대료(만원)"].median().reindex(DISTRICTS)
                summary = summary.fillna(pd.Series(EMBEDDED_RENT)).round(0)
                rent_df = pd.DataFrame({"자치구": summary.index, "월세": summary.values})
                seoul_avg = float(raw["임대료(만원)"].median())
                use_csv = True
        except Exception:
            pass
    return rent_df, seoul_avg, use_csv

@st.cache_data(show_spinner=False)
def build_district_dataframe():
    culture, library, subway, prices, parks = load_base_data()
    rent_df, seoul_rent_avg, using_rent_csv = load_rent_summary()

    base = pd.DataFrame(index=DISTRICTS)

    base["문화시설수"] = culture.groupby("자치구").size().reindex(DISTRICTS).fillna(0)
    base["도서관수"] = library.groupby("구명").size().reindex(DISTRICTS).fillna(0)
    base["공원수"] = parks.groupby("지역").size().reindex(DISTRICTS).fillna(0)
    base["지하철역수"] = subway.groupby("자치구").size().reindex(DISTRICTS).fillna(0)
    base["생활물가평균"] = prices.groupby("자치구 이름")["가격(원)"].mean().reindex(DISTRICTS).fillna(prices["가격(원)"].mean())
    base["월세"] = rent_df.set_index("자치구")["월세"].reindex(DISTRICTS).fillna(pd.Series(EMBEDDED_RENT))

    culture_type_top = (
        culture.groupby(["자치구", "문화유형"]).size().rename("개수").reset_index()
        .sort_values(["자치구", "개수"], ascending=[True, False])
    )

    district_lines = {}
    for d in DISTRICTS:
        lines = EXTENDED_LINES.get(d, []).copy()
        if d in subway["자치구"].values:
            lines += subway[subway["자치구"] == d]["호선"].astype(str).str.strip().tolist()
        # normalize
        clean = []
        for line in lines:
            line = str(line).strip()
            if line and line not in clean:
                clean.append(line)
        district_lines[d] = clean

    base["노선수"] = [len(district_lines[d]) for d in DISTRICTS]
    base["대표노선"] = [format_lines(district_lines[d]) for d in DISTRICTS]

    scaler = MinMaxScaler()
    norm_df = pd.DataFrame(
        scaler.fit_transform(base[["월세", "생활물가평균", "지하철역수", "노선수", "문화시설수", "공원수", "도서관수"]]),
        columns=["월세_norm", "생활물가_norm", "지하철역_norm", "노선_norm", "문화_norm", "공원_norm", "도서관_norm"],
        index=base.index,
    )

    base["월세점수"] = 1 - norm_df["월세_norm"]
    base["생활물가점수"] = 1 - norm_df["생활물가_norm"]
    base["교통점수_base"] = (norm_df["지하철역_norm"] * 0.55 + norm_df["노선_norm"] * 0.45).clip(0, 1)
    base["문화점수_base"] = (norm_df["문화_norm"] * 0.55 + norm_df["공원_norm"] * 0.2 + norm_df["도서관_norm"] * 0.25).clip(0, 1)

    # 강화 지표
    infra_avg = (base["교통점수_base"] + base["문화점수_base"]) / 2
    base["가성비지수"] = ((infra_avg * 0.7 + base["월세점수"] * 0.3) * 100).round(0)

    future_transit_focus = {"은평구", "강남구", "용산구", "영등포구", "금천구"}
    base["미래교통가치"] = [0.18 if d in future_transit_focus else 0.0 for d in base.index]
    base["교통점수_base"] = (base["교통점수_base"] + base["미래교통가치"]).clip(0, 1)
    base["안심점수"] = (
        base["도서관수"].rank(pct=True) * 0.5
        + base["공원수"].rank(pct=True) * 0.35
        + base["문화시설수"].rank(pct=True) * 0.15
    ).clip(0.32, 0.96)

    crowding = []
    for d in DISTRICTS:
        values = [LINE_CONGESTION.get(line, 0.55) for line in district_lines[d]]
        crowding.append(float(np.mean(values)) if values else 0.55)
    base["혼잡도"] = crowding
    base["혼잡도설명"] = base["혼잡도"].apply(lambda x: "높음" if x >= 0.8 else ("보통" if x >= 0.6 else "낮음"))

    base = base.reset_index().rename(columns={"index": "자치구"})
    return base, culture, library, subway, prices, parks, culture_type_top, district_lines, seoul_rent_avg, using_rent_csv

# ------------------------------------------------------------
# 추천 엔진
# ------------------------------------------------------------
PRIORITY_OPTIONS = ["월세", "생활물가", "교통", "문화생활"]

def priority_weights(order):
    points = [4, 3, 2, 1]
    raw = {"월세": 0, "생활물가": 0, "교통": 0, "문화생활": 0}
    for i, item in enumerate(order):
        raw[item] = points[i]
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}

def transport_match_score(district, selected_university, selected_work, selected_lines, district_lines):
    score = 0.0

    if selected_university != "선택 안 함":
        ranked = DEFAULT_UNI_TO_DISTRICTS.get(selected_university, [])
        if district in ranked:
            score += 0.55 - ranked.index(district) * 0.12

    if selected_work != "선택 안 함":
        ranked = WORK_TO_DISTRICTS.get(selected_work, [])
        if district in ranked:
            score += 0.45 - ranked.index(district) * 0.09

    lines = set(district_lines.get(district, []))
    if selected_lines:
        overlap = len(lines.intersection(selected_lines))
        score += min(overlap / max(len(selected_lines), 1), 1.0) * 0.55

    return min(score, 1.3)

def score_recommendations(df, selected_university, selected_work, selected_lines, order):
    weights = priority_weights(order)
    work = df.copy()

    transport_bonus = []
    for district in work["자치구"]:
        transport_bonus.append(transport_match_score(district, selected_university, selected_work, selected_lines, district_lines_map))
    work["교통보정"] = transport_bonus
    work["교통점수"] = (work["교통점수_base"] * 0.72 + work["교통보정"] * 0.28).clip(0, 1.15)

    work["추천점수"] = (
        work["월세점수"] * weights["월세"]
        + work["생활물가점수"] * weights["생활물가"]
        + work["교통점수"] * weights["교통"]
        + work["문화점수_base"] * weights["문화생활"]
    ) * 100

    # 안심/가성비는 설명용 보정
    work["총평점"] = (work["추천점수"] * 0.82 + work["가성비지수"] * 0.10 + work["안심점수"] * 100 * 0.08).round(1)
    return work.sort_values(["총평점", "추천점수"], ascending=False)

def build_reason(row, selected_university, selected_work, selected_lines):
    reasons = []
    if row["월세"] <= seoul_avg_rent:
        reasons.append(f"서울 평균 월세({round(seoul_avg_rent)}만 원)보다 저렴")
    if row["가성비지수"] >= 70:
        reasons.append("인프라 대비 가격 균형이 좋음")
    if row["안심점수"] >= 0.75:
        reasons.append("도서관·공원 기반 정주 안정감이 높음")
    if selected_university != "선택 안 함" and row["자치구"] in DEFAULT_UNI_TO_DISTRICTS.get(selected_university, []):
        reasons.append(f"{selected_university} 통학 관점에서 유리")
    if selected_work != "선택 안 함" and row["자치구"] in WORK_TO_DISTRICTS.get(selected_work, []):
        reasons.append(f"{selected_work} 출퇴근 관점에서 유리")
    overlap = set(district_lines_map.get(row["자치구"], [])).intersection(selected_lines)
    if overlap:
        reasons.append("희망 노선 " + ", ".join(sorted(overlap)[:3]) + " 이용 가능")
    if not reasons:
        reasons.append("월세·교통·문화생활의 균형이 무난함")
    return reasons[:3]

# ------------------------------------------------------------
# 화면 구성
# ------------------------------------------------------------
base_df, culture_df, library_df, subway_df, prices_df, parks_df, culture_type_top_df, district_lines_map, seoul_avg_rent, using_rent_csv = build_district_dataframe()

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">서울, 처음이니? : 어디서 자취할까?</div>
        <div class="hero-sub">
            처음 서울에서 자취를 시작하는 2030을 위해 만든 지역 추천 서비스예요.
            단순 통계가 아니라 <b>월세 · 생활비 · 교통 · 문화생활 · 밤길 체감</b>을 묶어서
            “내 하루가 실제로 어떻게 달라질지” 기준으로 비교해 볼 수 있어요.
        </div>
        <span class="mini-badge">가성비 지수</span>
        <span class="mini-badge">지옥철 혼잡도 반영</span>
        <span class="mini-badge">GTX-A 미래가치 반영</span>
        <span class="mini-badge">체크리스트 저장</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("우선순위 설정")
    st.caption("1순위일수록 추천 점수에 더 크게 반영돼요. 1순위=40%, 2순위=30%, 3순위=20%, 4순위=10%")

    p1 = st.selectbox("1순위", PRIORITY_OPTIONS, index=0)
    remaining = [x for x in PRIORITY_OPTIONS if x != p1]
    p2 = st.selectbox("2순위", remaining, index=0)
    remaining = [x for x in remaining if x != p2]
    p3 = st.selectbox("3순위", remaining, index=0)
    remaining = [x for x in remaining if x != p3]
    p4 = st.selectbox("4순위", remaining, index=0)

    order = [p1, p2, p3, p4]

    st.markdown("---")
    st.subheader("필수 조건")
    rent_band = st.selectbox(
        "희망 월세 가격대",
        ["상관없음", "50만원대 이하", "60만원대", "70만원대", "80만원대", "90만원대 이상"],
        index=2,
    )
    university = st.selectbox("재학 중인 대학교", list(DEFAULT_UNI_TO_DISTRICTS.keys()), index=0)
    work_place = st.selectbox("근무지 / 자주 가는 업무지구", list(WORK_TO_DISTRICTS.keys()), index=0)
    preferred_lines = st.multiselect("희망 지하철 노선(중복 선택 가능)", sorted(LINE_PREFS), default=["2호선"] if university == "서울대학교" else [])

    st.markdown("---")
    st.subheader("초보 자취 체크리스트")
    selected_checklist = []
    for item in CHECKLIST_ITEMS:
        if st.checkbox(item, value=item in CHECKLIST_ITEMS[:3]):
            selected_checklist.append(item)

weights = priority_weights(order)

work_df = score_recommendations(base_df, university, work_place, preferred_lines, order)

if rent_band != "상관없음":
    lo, hi = {
        "50만원대 이하": (0, 59),
        "60만원대": (60, 69),
        "70만원대": (70, 79),
        "80만원대": (80, 89),
        "90만원대 이상": (90, 999),
    }[rent_band]
    work_df = work_df[(work_df["월세"] >= lo) & (work_df["월세"] <= hi)].copy()

if work_df.empty:
    st.error("지금 설정한 조건을 동시에 만족하는 자치구가 없어요. 월세 가격대나 희망 노선을 조금 완화해 보세요.")
    st.stop()

# ------------------------------------------------------------
# 상단 핵심 카드
# ------------------------------------------------------------
top_pick = work_df.iloc[0]
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">서울 평균 월세</div>
            <div class="metric-value">{round(seoul_avg_rent)}만 원</div>
            <div class="metric-desc">{"로컬 전월세 CSV 기준" if using_rent_csv else "보고서 기반 요약값 기준"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">이번 조건의 1위 추천</div>
            <div class="metric-value">{top_pick['자치구']}</div>
            <div class="metric-desc">총평점 {top_pick['총평점']:.1f} / 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    market_avg = int(round(prices_df["가격(원)"].mean(), 0))
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">서울 생활물가 평균</div>
            <div class="metric-value">{market_avg:,}원</div>
            <div class="metric-desc">업로드한 생활물가 파일 기준 평균값</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">오늘의 포인트</div>
            <div class="metric-value">{work_df['가성비지수'].max():.0f}</div>
            <div class="metric-desc">이번 필터 내 최고 가성비 지수</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if rent_band in {"50만원대 이하", "60만원대"}:
    budget_hits = [d for d in work_df["자치구"].tolist()[:3] if d in LOW_BUDGET_WARNINGS]
    if budget_hits:
        msg = "<br>".join([f"• <b>{d}</b> — {LOW_BUDGET_WARNINGS[d]}" for d in budget_hits])
        st.markdown(f"<div class='warn-box'><b>저예산 자취 팁</b><br>{msg}</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["추천 결과", "지역 상세", "비교 분석", "체크리스트 저장"])

# ------------------------------------------------------------
# 탭1: 추천 결과
# ------------------------------------------------------------
with tab1:
    st.markdown("### 🔥 지금 조건에서 추천하는 자치구 TOP 5")
    st.caption("월세·생활물가·교통·문화생활을 1~4순위 가중치로 반영했고, 교통은 학교·근무지·희망 노선 선택을 추가 반영했어요.")

    top5 = work_df.head(5).copy()
    cols = st.columns(5)
    for i, (_, row) in enumerate(top5.iterrows()):
        reasons = build_reason(row, university, work_place, preferred_lines)
        delta = round(row["월세"] - seoul_avg_rent)
        rent_desc = f"서울 평균 대비 {'-' if delta < 0 else '+'}{abs(delta)}만 원"
        with cols[i]:
            st.markdown(
                f"""
                <div class="rank-card">
                    <div class="rank-no">TOP {i+1}</div>
                    <div class="rank-title">{row['자치구']}</div>
                    <div class="rank-meta">
                        <b>총평점</b> {row['총평점']:.1f}<br>
                        <b>월세</b> {int(round(row['월세']))}만 원 <span class="small">({rent_desc})</span><br>
                        <b>생활물가</b> {int(round(row['생활물가평균'])):,}원<br>
                        <b>대표 노선</b> {row['대표노선']}<br>
                        <b>문화생활</b> 문화시설 {int(row['문화시설수'])} · 공원 {int(row['공원수'])} · 도서관 {int(row['도서관수'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(icon_chips(reasons), unsafe_allow_html=True)

    st.markdown("### 📌 2030 상경러를 위한 테마별 추천")
    t1, t2, t3 = st.columns(3)
    best_vfm = work_df.sort_values("가성비지수", ascending=False).iloc[0]["자치구"]
    best_safety = work_df.sort_values("안심점수", ascending=False).iloc[0]["자치구"]
    best_future = work_df.sort_values("미래교통가치", ascending=False).iloc[0]["자치구"]
    with t1:
        st.markdown(f"<div class='success-box'><b>💰 가성비 끝판왕</b><br>{best_vfm} — 인프라 대비 월세 밸런스가 좋음</div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"<div class='success-box'><b>🛡️ 밤길 안심 1위</b><br>{best_safety} — 공원·도서관 기반 정주 안정감 우수</div>", unsafe_allow_html=True)
    with t3:
        st.markdown(f"<div class='info-box'><b>🚀 미래 교통 수혜지</b><br>{best_future} — GTX-A/광역망 관점에서 기대치가 큼</div>", unsafe_allow_html=True)

    st.markdown("### 🗺️ 서울 자치구 지도")
    st.caption("구역을 누르면 팝업에서 월세, 가성비, 노선, 문화생활 수를 볼 수 있어요.")

    map_center = [37.55, 126.98]
    fmap = folium.Map(location=map_center, zoom_start=11, tiles="cartodbpositron")

    try:
        geojson_url = "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json"
        geojson = requests.get(geojson_url, timeout=8).json()
        score_map = work_df.set_index("자치구")["총평점"].to_dict()
        colormap = cm.LinearColormap(colors=["#dbeafe", "#60a5fa", "#2563eb"], vmin=min(score_map.values()), vmax=max(score_map.values()))
        colormap.caption = "추천 점수"

        def style_fn(feature):
            name = feature["properties"].get("name")
            score = score_map.get(name, 0)
            return {
                "fillColor": colormap(score) if name in score_map else "#e5e7eb",
                "color": "#334155",
                "weight": 1.3,
                "fillOpacity": 0.75,
            }

        gj = folium.GeoJson(
            geojson,
            name="서울 자치구",
            style_function=style_fn,
            tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["자치구"], sticky=False),
        )
        gj.add_to(fmap)

        for _, row in work_df.iterrows():
            center = DISTRICT_CENTERS[row["자치구"]]
            popup_html = f"""
            <div style='min-width:220px'>
            <b>{row['자치구']}</b><br>
            월세: {int(round(row['월세']))}만 원<br>
            총평점: {row['총평점']:.1f}<br>
            가성비지수: {row['가성비지수']:.0f}<br>
            생활물가: {int(round(row['생활물가평균'])):,}원<br>
            혼잡도: {row['혼잡도설명']}<br>
            노선: {row['대표노선']}<br>
            문화시설: {int(row['문화시설수'])} / 공원: {int(row['공원수'])} / 도서관: {int(row['도서관수'])}
            </div>
            """
            folium.CircleMarker(
                location=center,
                radius=8,
                color="#1d4ed8",
                fill=True,
                fill_opacity=0.95,
                popup=folium.Popup(popup_html, max_width=280),
            ).add_to(fmap)

        colormap.add_to(fmap)
    except Exception:
        for _, row in work_df.iterrows():
            center = DISTRICT_CENTERS[row["자치구"]]
            folium.Marker(
                location=center,
                popup=f"{row['자치구']} | 총평점 {row['총평점']:.1f} | 월세 {int(round(row['월세']))}만 원",
            ).add_to(fmap)

    st_folium(fmap, width=None, height=620)

    chart_df = top5[["자치구", "총평점", "월세", "생활물가평균", "가성비지수"]].copy()
    chart_df["생활물가평균"] = chart_df["생활물가평균"].round(0)
    left, right = st.columns([1.15, 1])
    with left:
        fig = px.bar(
            chart_df,
            x="자치구",
            y="총평점",
            color="총평점",
            text="총평점",
            color_continuous_scale="Blues",
            title="TOP 5 추천 점수 비교",
        )
        fig.update_layout(coloraxis_showscale=False, height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        mix = px.scatter(
            chart_df,
            x="월세",
            y="생활물가평균",
            size="가성비지수",
            color="자치구",
            hover_name="자치구",
            title="월세와 생활물가의 균형",
        )
        mix.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(mix, use_container_width=True)

# ------------------------------------------------------------
# 탭2: 지역 상세
# ------------------------------------------------------------
with tab2:
    detail_district = st.selectbox("심층 분석할 자치구", work_df["자치구"].tolist(), index=0)
    row = base_df.set_index("자치구").loc[detail_district]

    st.markdown(f"### 📍 {detail_district} 심층 분석")
    a, b, c, d = st.columns(4)
    a.metric("예상 월세", f"{int(round(row['월세']))}만 원", f"서울 평균 대비 {int(round(row['월세'] - seoul_avg_rent)):+d}만 원")
    b.metric("생활물가 평균", f"{int(round(row['생활물가평균'])):,}원")
    c.metric("가성비 지수", f"{int(round(row['가성비지수']))}")
    d.metric("밤길 안심 점수", f"{int(round(row['안심점수']*100))}점")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("강남역(GBD)", commute_bucket(detail_district, "강남"))
    with c2:
        st.metric("여의도(YBD)", commute_bucket(detail_district, "여의도"))
    with c3:
        st.metric("시청/종로(CBD)", commute_bucket(detail_district, "종로"))

    st.markdown(f"<div class='review-box'><b>💬 자취생 한 줄 평</b><br>{realistic_tip(detail_district)}</div>", unsafe_allow_html=True)

    dcol1, dcol2 = st.columns([1, 1])
    with dcol1:
        st.markdown("#### 🚇 교통")
        st.markdown(icon_chips(district_lines_map.get(detail_district, [])), unsafe_allow_html=True)
        st.write(f"지하철역 수: **{int(row['지하철역수'])}개**")
        st.write(f"혼잡도: **{row['혼잡도설명']}** (통근 핵심 노선 위주 대리 지표)")
        if university != "선택 안 함":
            if detail_district in DEFAULT_UNI_TO_DISTRICTS.get(university, []):
                st.success(f"{university} 통학권 추천 자치구에 포함돼요.")
            else:
                st.info(f"{university} 기준으로는 1순위 통학권은 아니에요.")
        if work_place != "선택 안 함":
            if detail_district in WORK_TO_DISTRICTS.get(work_place, []):
                st.success(f"{work_place} 출퇴근 후보로 적합한 편이에요.")
            else:
                st.info(f"{work_place} 기준으로는 통근시간 비교가 필요해요.")

        stations = subway_df[subway_df["자치구"] == detail_district][["호선", "역명"]].drop_duplicates().sort_values(["호선", "역명"])
        if not stations.empty:
            st.markdown("**대표 역**")
            st.dataframe(stations.head(12), use_container_width=True, hide_index=True)

    with dcol2:
        st.markdown("#### 🎭 문화생활")
        district_culture_types = (
            culture_type_top_df[culture_type_top_df["자치구"] == detail_district][["문화유형", "개수"]]
            .head(6)
            .copy()
        )
        if not district_culture_types.empty:
            fig = px.bar(
                district_culture_types,
                x="문화유형",
                y="개수",
                color="개수",
                color_continuous_scale="Tealgrn",
                title="이 동네에 많은 문화생활 종류",
            )
            fig.update_layout(coloraxis_showscale=False, height=320, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)

        culture_examples = culture_df[culture_df["자치구"] == detail_district][["문화유형", "문화시설명", "주소"]].dropna().head(8)
        if not culture_examples.empty:
            st.markdown("**대표 시설과 위치**")
            st.dataframe(culture_examples, use_container_width=True, hide_index=True)

        parks_examples = parks_df[parks_df["지역"] == detail_district][["공원명", "공원주소"]].head(5)
        libs_examples = library_df[library_df["구명"] == detail_district][["도서관명", "주소"]].head(5)

        if not parks_examples.empty:
            st.markdown("**대표 공원**")
            st.dataframe(parks_examples, use_container_width=True, hide_index=True)
        if not libs_examples.empty:
            st.markdown("**대표 도서관 / 공부환경**")
            st.dataframe(libs_examples, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# 탭3: 비교 분석
# ------------------------------------------------------------
with tab3:
    st.markdown("### 🆚 자치구 비교 분석")
    st.caption("최대 3곳까지 비교할 수 있어요. 월세, 생활권, 문화생활, 교통, 학교·직장 접근성을 한 번에 비교합니다.")

    compare_choices = st.multiselect("비교할 자치구 선택 (최대 3개)", work_df["자치구"].tolist(), default=work_df["자치구"].tolist()[:2], max_selections=3)
    if compare_choices:
        comp = base_df[base_df["자치구"].isin(compare_choices)].copy()

        # 비교 테이블
        comp_table = comp[["자치구", "월세", "생활물가평균", "지하철역수", "문화시설수", "공원수", "도서관수", "가성비지수", "안심점수", "대표노선"]].copy()
        comp_table["생활물가평균"] = comp_table["생활물가평균"].round(0).astype(int)
        comp_table["안심점수"] = (comp_table["안심점수"] * 100).round(0).astype(int)
        comp_table = comp_table.rename(columns={"생활물가평균":"생활물가(원)", "월세":"예상월세(만 원)", "지하철역수":"역 수", "문화시설수":"문화시설", "공원수":"공원", "도서관수":"도서관", "가성비지수":"가성비", "안심점수":"안심점수"})
        st.dataframe(comp_table, use_container_width=True, hide_index=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            bar = px.bar(
                comp,
                x="자치구",
                y=["월세", "생활물가평균"],
                barmode="group",
                title="월세 / 생활물가 비교",
            )
            bar.update_layout(height=380)
            st.plotly_chart(bar, use_container_width=True)
        with cc2:
            infra = px.bar(
                comp,
                x="자치구",
                y=["문화시설수", "공원수", "도서관수", "지하철역수"],
                barmode="group",
                title="생활권 인프라 비교",
            )
            infra.update_layout(height=380)
            st.plotly_chart(infra, use_container_width=True)

        st.markdown("#### 🚇 교통·통학·통근 비교")
        commute_rows = []
        for d in compare_choices:
            uni_mark = "추천권" if university != "선택 안 함" and d in DEFAULT_UNI_TO_DISTRICTS.get(university, []) else "-"
            work_mark = "추천권" if work_place != "선택 안 함" and d in WORK_TO_DISTRICTS.get(work_place, []) else "-"
            line_overlap = ", ".join(sorted(set(district_lines_map.get(d, [])).intersection(preferred_lines))) if preferred_lines else "-"
            commute_rows.append({
                "자치구": d,
                "지하철 노선": format_lines(district_lines_map.get(d, [])),
                f"{university} 기준": uni_mark if university != "선택 안 함" else "-",
                f"{work_place} 기준": work_mark if work_place != "선택 안 함" else "-",
                "희망 노선 일치": line_overlap if line_overlap else "-",
                "현실 팁": realistic_tip(d),
            })
        st.dataframe(pd.DataFrame(commute_rows), use_container_width=True, hide_index=True)

        st.markdown("#### 📝 어디가 더 현실적으로 잘 맞을까?")
        best_compare = score_recommendations(comp, university, work_place, preferred_lines, order).iloc[0]["자치구"]
        st.markdown(
            f"<div class='info-box'><b>이번 조건에서 비교군 1위</b><br><b>{best_compare}</b>가 가장 균형이 좋아요. "
            f"월세·교통·생활권·문화생활의 합산 점수가 가장 높았고, "
            f"현재 설정한 {'학교' if university != '선택 안 함' else '생활조건'} 기준과도 가장 잘 맞아요.</div>",
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# 탭4: 체크리스트 저장
# ------------------------------------------------------------
with tab4:
    st.markdown("### ✅ 초보 자취생 체크리스트")
    st.caption("당장 방 보러 갈 때 필요한 항목을 저장해 두세요. 스트림릿 앱 안에서는 세션으로 유지되고, 파일로도 내려받을 수 있어요.")

    if selected_checklist:
        for item in selected_checklist:
            st.markdown(f"- {item}")
    else:
        st.info("왼쪽 사이드바에서 체크리스트를 선택해 보세요.")

    summary_payload = {
        "site": "서울, 처음이니? : 어디서 자취할까?",
        "priority_order": order,
        "rent_band": rent_band,
        "university": university,
        "work_place": work_place,
        "preferred_lines": preferred_lines,
        "top_recommendations": work_df["자치구"].head(5).tolist(),
        "selected_checklist": selected_checklist,
    }

    summary_text = (
        f"[서울, 처음이니? : 어디서 자취할까?]\n"
        f"- 우선순위: {' > '.join(order)}\n"
        f"- 희망 월세: {rent_band}\n"
        f"- 대학교: {university}\n"
        f"- 근무지: {work_place}\n"
        f"- 희망 노선: {', '.join(preferred_lines) if preferred_lines else '없음'}\n"
        f"- 추천 TOP5: {', '.join(work_df['자치구'].head(5).tolist())}\n"
        f"- 체크리스트:\n  • " + "\n  • ".join(selected_checklist if selected_checklist else ["선택 항목 없음"])
    )

    st.download_button(
        label="체크리스트 + 추천결과 TXT로 저장",
        data=summary_text,
        file_name="seoul_jachui_checklist.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.download_button(
        label="설정값 JSON으로 저장",
        data=json.dumps(summary_payload, ensure_ascii=False, indent=2),
        file_name="seoul_jachui_settings.json",
        mime="application/json",
        use_container_width=True,
    )

st.markdown(
    """
    <div class="footer-note">
    ※ 밤길 안심 점수는 실제 범죄 통계가 아니라 공원·도서관·정주 인프라 밀도를 활용한 대리지표예요.<br>
    ※ 지옥철 혼잡도와 GTX-A/광역망 가치는 실시간 교통량이 아니라 노선 특성과 향후 접근성 기대를 반영한 참고 지표예요.<br>
    ※ 전월세 CSV가 함께 있으면 그 값을 우선 사용하고, 없으면 업로드된 보고서 기반 월세 요약값으로 동작해요.
    </div>
    """,
    unsafe_allow_html=True,
)
