
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
import re
from branca.colormap import linear

st.set_page_config(
    page_title="서울, 처음이니? : 어디서 자취할까?",
    page_icon="🏠",
    layout="wide"
)

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}
html, body, [class*="css"]  {
    font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}
.main-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
    color: #111827;
}
.sub-title {
    font-size: 1rem;
    color: #4b5563;
    margin-bottom: 1rem;
}
.hero {
    background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
    border: 1px solid #e5eefb;
    border-radius: 22px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
}
.metric-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1rem 1rem;
    box-shadow: 0 8px 24px rgba(15,23,42,0.04);
}
.metric-label {
    color: #6b7280;
    font-size: 0.88rem;
    margin-bottom: 0.2rem;
}
.metric-value {
    color: #111827;
    font-size: 1.55rem;
    font-weight: 800;
}
.metric-desc {
    color: #6b7280;
    font-size: 0.84rem;
}
.rec-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 20px;
    padding: 1rem 1rem;
    min-height: 205px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.04);
}
.rec-rank {
    display:inline-block;
    background:#111827;
    color:white;
    border-radius:999px;
    padding:0.2rem 0.55rem;
    font-size:0.82rem;
    font-weight:700;
}
.rec-title {
    margin-top:0.7rem;
    color:#111827 !important;
    font-size:1.35rem;
    font-weight:800;
}
.rec-sub {
    color:#4b5563;
    font-size:0.92rem;
    margin-top:0.15rem;
    line-height:1.45;
}
.badge {
    display:inline-block;
    border-radius:999px;
    padding:0.22rem 0.55rem;
    margin:0.15rem 0.2rem 0 0;
    font-size:0.78rem;
    font-weight:700;
    background:#f3f4f6;
    color:#374151;
}
.section-title {
    font-size:1.25rem;
    font-weight:800;
    color:#111827;
    margin-top:0.2rem;
    margin-bottom:0.8rem;
}
.tip-box {
    background:#f9fafb;
    border:1px solid #e5e7eb;
    border-left:5px solid #3b82f6;
    padding:0.9rem 1rem;
    border-radius:16px;
    color:#374151;
}
.warn-box {
    background:#fff7ed;
    border:1px solid #fed7aa;
    border-left:5px solid #f97316;
    padding:0.9rem 1rem;
    border-radius:16px;
    color:#7c2d12;
}
.good-box {
    background:#ecfdf5;
    border:1px solid #a7f3d0;
    border-left:5px solid #10b981;
    padding:0.9rem 1rem;
    border-radius:16px;
    color:#065f46;
}
.small-note {
    color:#6b7280;
    font-size:0.85rem;
}
[data-testid="stMetricValue"] {
    color: #111827 !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 기본 상수
# -----------------------------
DISTRICT_COORDS = {
    "강남구":[37.5172,127.0473],"강동구":[37.5301,127.1238],"강북구":[37.6397,127.0257],
    "강서구":[37.5509,126.8495],"관악구":[37.4784,126.9516],"광진구":[37.5385,127.0822],
    "구로구":[37.4954,126.8874],"금천구":[37.4602,126.9006],"노원구":[37.6542,127.0568],
    "도봉구":[37.6688,127.0471],"동대문구":[37.5744,127.0395],"동작구":[37.5124,126.9393],
    "마포구":[37.5663,126.9014],"서대문구":[37.5791,126.9368],"서초구":[37.4837,127.0324],
    "성동구":[37.5634,127.0366],"성북구":[37.5894,127.0167],"송파구":[37.5145,127.1059],
    "양천구":[37.5169,126.8664],"영등포구":[37.5264,126.8962],"용산구":[37.5326,126.9900],
    "은평구":[37.6027,126.9291],"종로구":[37.5735,126.9788],"중구":[37.5640,126.9970],
    "중랑구":[37.6063,127.0927]
}

EMBEDDED_RENT_SUMMARY = {
  "강남구": {
    "median": 74.0,
    "mean": 81.6,
    "count": 21729
  },
  "강동구": {
    "median": 50.0,
    "mean": 51.2,
    "count": 20999
  },
  "강북구": {
    "median": 45.0,
    "mean": 49.4,
    "count": 10968
  },
  "강서구": {
    "median": 53.0,
    "mean": 51.9,
    "count": 33594
  },
  "관악구": {
    "median": 50.0,
    "mean": 50.8,
    "count": 40736
  },
  "광진구": {
    "median": 55.0,
    "mean": 56.7,
    "count": 30308
  },
  "구로구": {
    "median": 48.0,
    "mean": 50.1,
    "count": 15849
  },
  "금천구": {
    "median": 47.0,
    "mean": 49.3,
    "count": 14692
  },
  "노원구": {
    "median": 43.0,
    "mean": 44.4,
    "count": 8296
  },
  "도봉구": {
    "median": 45.0,
    "mean": 48.6,
    "count": 7719
  },
  "동대문구": {
    "median": 55.0,
    "mean": 59.6,
    "count": 21058
  },
  "동작구": {
    "median": 50.0,
    "mean": 51.1,
    "count": 23048
  },
  "마포구": {
    "median": 65.0,
    "mean": 67.6,
    "count": 25327
  },
  "서대문구": {
    "median": 55.0,
    "mean": 60.0,
    "count": 18091
  },
  "서초구": {
    "median": 66.0,
    "mean": 78.9,
    "count": 16246
  },
  "성동구": {
    "median": 55.0,
    "mean": 59.5,
    "count": 11900
  },
  "성북구": {
    "median": 50.0,
    "mean": 55.0,
    "count": 14202
  },
  "송파구": {
    "median": 54.0,
    "mean": 57.8,
    "count": 37660
  },
  "양천구": {
    "median": 50.0,
    "mean": 53.7,
    "count": 10486
  },
  "영등포구": {
    "median": 50.0,
    "mean": 54.5,
    "count": 25500
  },
  "용산구": {
    "median": 67.0,
    "mean": 90.6,
    "count": 8828
  },
  "은평구": {
    "median": 50.0,
    "mean": 48.7,
    "count": 16981
  },
  "종로구": {
    "median": 60.0,
    "mean": 68.2,
    "count": 9370
  },
  "중구": {
    "median": 65.0,
    "mean": 70.4,
    "count": 6785
  },
  "중랑구": {
    "median": 45.0,
    "mean": 48.6,
    "count": 15836
  }
}
RENT_META = {"overall_mean": 57.5, "overall_median": 52.0, "count": 466208}

DISTRICT_STORIES = {
    "관악구": {
        "summary": "서울대입구·신림을 중심으로 1인 가구 친화 상권이 발달한 대표 가성비 자취권역.",
        "pros": ["월세 방어력이 좋고 식당·편의점 밀도가 높음", "신림선으로 여의도 접근이 개선", "초기 자취 입문자에게 선택지가 많음"],
        "cons": ["언덕과 노후 원룸 비중이 높아 실제 컨디션 편차가 큼", "밀집 주거지 특성상 소음·환기 이슈 체크 필요", "저가 방은 반지하/분리형 여부를 꼭 확인"],
        "one_line": "가성비는 강하지만, 매물 상태와 언덕/소음 체크는 필수."
    },
    "마포구": {
        "summary": "신촌·홍대·공덕 생활권을 끼고 있어 문화·상권·직주근접이 강한 프리미엄 자취권역.",
        "pros": ["문화공간과 카페, 공연·전시 접근성이 매우 좋음", "2·5·6호선과 공항철도 등 환승 체감이 좋음", "프리랜서·콘텐츠/미디어 직군 선호"],
        "cons": ["핫플 상권 인접 지역은 소음과 관광객 유동이 큼", "비슷한 컨디션 대비 월세가 빠르게 높아짐", "생활비까지 합치면 체감 부담이 큰 편"],
        "one_line": "분위기와 문화생활은 최고권, 대신 월세와 생활비는 확실히 비싼 편."
    },
    "서대문구": {
        "summary": "신촌·이대·연희권을 묶는 대학가 자취권역으로 통학 편의와 생활 인프라가 균형적.",
        "pros": ["연세대·이화여대·서강대 접근이 좋음", "마포보다는 살짝 덜 붐비는 대학가 생활권", "마을버스·도보 통학 동선이 강점"],
        "cons": ["신촌 생활권 인접지는 월세 상승 압력이 큼", "노후 원룸 매물이 많아 관리 상태 확인 필요", "언덕과 골목형 주거지 비중이 있음"],
        "one_line": "대학생에게 실용적이지만, 대학가 프리미엄은 분명히 존재."
    },
    "광진구": {
        "summary": "건대입구·자양·구의를 중심으로 대학가와 상권, 2·7호선 접근이 모두 강한 권역.",
        "pros": ["건국대·세종대 통학 및 2·7호선 출퇴근이 편함", "상권이 활발해 늦은 시간 귀가 불안감이 덜한 편", "성수 생활권을 함께 누리기 쉬움"],
        "cons": ["핫플 상권과 붙은 지역은 소음 민감도가 높음", "힙한 생활권 프리미엄이 월세에 반영", "골목형 주차난과 유동인구 혼잡이 있음"],
        "one_line": "생활은 재밌고 편리하지만, 그만큼 시세와 소음도 함께 온다."
    },
    "성동구": {
        "summary": "성수·왕십리 생활권을 아우르며 문화 감도와 직주근접성이 강한 실속형 프리미엄 지역.",
        "pros": ["성수 문화권과 IT/스타트업 접근성이 좋음", "왕십리 환승축으로 이동 효율이 높음", "한강·서울숲 접근성까지 챙기기 쉬움"],
        "cons": ["성수 인접 매물은 체감 월세가 빠르게 높아짐", "신축·리모델링 매물 프리미엄이 큼", "골목형 빌라권은 주차·동선 확인 필요"],
        "one_line": "출퇴근과 문화생활을 동시에 잡기 좋은 대신, 입지값을 치르는 지역."
    },
    "동대문구": {
        "summary": "회기·이문·장안을 중심으로 대학가 실수요가 많고, 상대적으로 현실적인 선택지가 남아 있는 곳.",
        "pros": ["경희대·외대·시립대 생활권과 맞닿음", "대학생 자취 수요를 반영한 식당/생활업종이 많음", "중심권 대비 비교적 현실적인 예산대가 존재"],
        "cons": ["노후 건물 비중이 높아 보일러·단열 상태 확인 필요", "회기권은 오르막과 오래된 골목 매물이 섞여 있음", "핫플형 문화생활을 원하면 외부 이동이 필요"],
        "one_line": "대학생의 지갑 사정을 잘 이해하는 지역이지만, 인프라와 건물 상태 편차가 크다."
    },
    "성북구": {
        "summary": "안암·보문·정릉 생활권을 중심으로 대학가 수요와 주거 안정성을 함께 보는 지역.",
        "pros": ["고려대 통학에 유리하고 동대문권 접근이 편함", "대학가 대비 상대적으로 조용한 주거지 선택 가능", "월세와 생활물가 균형이 무난한 편"],
        "cons": ["안암 인접지는 언덕과 계단 동선이 체감 큼", "노후 원룸은 수납·단열에서 아쉬울 수 있음", "문화핫플 밀도는 마포·성동보다 약함"],
        "one_line": "통학 안정감은 좋지만, 언덕과 매물 노후도는 꼭 체크해야 한다."
    },
    "강남구": {
        "summary": "역삼·논현·삼성을 중심으로 직주근접과 생활 편의는 최상위지만 비용도 최상위권.",
        "pros": ["업무지구 접근성과 생활 편의가 매우 강함", "편의시설·병원·헬스장·상권 밀도가 높음", "야간 이동과 택시 접근성이 편리"],
        "cons": ["오피스텔 관리비와 생활비까지 합치면 체감 부담이 큼", "비슷한 예산이면 타 지역보다 면적·채광이 작을 수 있음", "혼자 사는 고립감이 크게 느껴질 수 있음"],
        "one_line": "완성형 인프라를 누리지만, 비용 부담을 감수해야 하는 지역."
    },
    "동작구": {
        "summary": "노량진·상도·흑석 권역을 아우르며 관악과 여의도·강남 사이를 잇는 실용형 선택지.",
        "pros": ["9호선·7호선·신림선 연계 체감이 좋음", "흑석·노량진은 직주근접과 학주근접을 동시에 보기 좋음", "관악보다 상권은 덜 과밀하면서 예산대는 비슷한 매물이 있음"],
        "cons": ["언덕과 오래된 빌라권이 적지 않음", "노량진권은 수험생·학원가 특유의 분위기가 있음", "신축 매물은 가성비가 급격히 떨어질 수 있음"],
        "one_line": "교통이 강점인 실용형 지역, 다만 언덕과 동네 결은 직접 확인이 좋다."
    },
}

UNIVERSITY_MAP = {
    "해당 없음": {"districts": [], "tip": "대학 통학 가중치 없이 추천합니다."},
    "서울대학교": {"districts": ["관악구", "동작구"], "tip": "서울대입구역·신림권, 상도·흑석권이 현실적인 통학 축입니다."},
    "연세대학교": {"districts": ["서대문구", "마포구"], "tip": "신촌역·이대역 생활권이 가깝고 도보/마을버스 통학 동선이 좋습니다."},
    "이화여자대학교": {"districts": ["서대문구", "마포구"], "tip": "신촌·이대 생활권이 강하고, 조용함을 원하면 연희/북아현까지 같이 봅니다."},
    "서강대학교": {"districts": ["마포구", "서대문구"], "tip": "공덕·대흥·신촌을 함께 보면 통학과 알바 접근을 같이 챙기기 좋습니다."},
    "건국대학교": {"districts": ["광진구", "성동구"], "tip": "건대입구 도보권이 가장 강하고, 성수/왕십리권은 생활감도까지 좋습니다."},
    "세종대학교": {"districts": ["광진구"], "tip": "군자동·화양동·자양동 생활권이 기본 선택지입니다."},
    "경희대학교": {"districts": ["동대문구", "성북구"], "tip": "회기역 축과 이문·청량리권을 먼저 보세요."},
    "고려대학교": {"districts": ["성북구", "동대문구"], "tip": "안암역 도보권이 가장 편하고, 보문/제기동권까지 확장하면 선택지가 늘어납니다."},
    "한양대학교": {"districts": ["성동구", "동대문구"], "tip": "왕십리·행당·마장 생활권이 통학 효율이 좋습니다."},
    "중앙대학교": {"districts": ["동작구", "관악구"], "tip": "흑석·상도는 직접 접근, 신림은 예산 절감형 대안입니다."},
    "숭실대학교": {"districts": ["동작구", "관악구"], "tip": "상도·노량진·신대방 생활권이 무난합니다."},
    "홍익대학교": {"districts": ["마포구", "서대문구"], "tip": "홍대입구·합정·신촌 생활권이 강하고, 예산이 낮으면 서교 외곽까지 보세요."},
}

BEGINNER_LEVEL_BONUS = {
    "Lv.1 비기너": {"bonus_districts": ["강남구", "서초구", "송파구", "성동구"], "tip": "관리비가 조금 더 들더라도 보안과 관리 상태가 안정적인 지역에 가산점을 줍니다."},
    "Lv.2 프로 자취러": {"bonus_districts": ["관악구", "동작구", "동대문구", "성북구", "구로구", "금천구"], "tip": "가성비와 실제 생활 편의에 가산점을 줍니다."},
    "Lv.3 동네 정착러": {"bonus_districts": ["마포구", "성동구", "광진구", "종로구"], "tip": "로컬 상권과 문화생활이 풍부한 지역에 가산점을 줍니다."},
}

LOW_BUDGET_WARNINGS = [
    "서울 평균보다 낮은 예산대에서는 반지하·언덕·노후 원룸이 섞일 가능성이 높습니다.",
    "월세만 보지 말고 관리비, 채광, 수납, 보일러·곰팡이 상태를 함께 확인하세요.",
    "가성비 지역일수록 소음·오토바이 통행·귀가 동선 체감 차이가 큽니다."
]

# -----------------------------
# 데이터 로딩
# -----------------------------
@st.cache_data(show_spinner=False)
def read_csv_flexible(path):
    last_error = None
    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_error = e
    raise last_error

@st.cache_data(show_spinner=False)
def load_base_data():
    culture = read_csv_flexible("서울시 문화공간 정보.csv")
    library = read_csv_flexible("서울시 공공도서관 현황정보.csv")
    subway = read_csv_flexible("서울교통공사_역주소 및 전화번호.csv")
    prices = read_csv_flexible("생필품 농수축산물 가격 정보(2024년).csv")
    parks = pd.read_excel("서울시 주요 공원현황(2026 상반기).xlsx")
    return culture, library, subway, prices, parks

def extract_gu(text):
    if pd.isna(text):
        return None
    m = re.search(r'([가-힣]+구)', str(text))
    return m.group(1) if m else None

@st.cache_data(show_spinner=False)
def prepare_data():
    culture, library, subway, prices, parks = load_base_data()

    culture["자치구"] = culture["자치구"].astype(str).str.strip()
    culture["주제분류"] = culture["주제분류"].fillna("기타").astype(str)
    culture["문화시설명"] = culture["문화시설명"].fillna("이름 미상")
    culture["위도"] = pd.to_numeric(culture["위도"], errors="coerce")
    culture["경도"] = pd.to_numeric(culture["경도"], errors="coerce")

    library["구명"] = library["구명"].astype(str).str.strip()
    library["위도"] = pd.to_numeric(library["위도"], errors="coerce")
    library["경도"] = pd.to_numeric(library["경도"], errors="coerce")

    parks["지역"] = parks["지역"].astype(str).str.strip()
    parks["X좌표(WGS84)"] = pd.to_numeric(parks["X좌표(WGS84)"], errors="coerce")
    parks["Y좌표(WGS84)"] = pd.to_numeric(parks["Y좌표(WGS84)"], errors="coerce")

    prices["자치구 이름"] = prices["자치구 이름"].astype(str).str.strip()
    prices["가격(원)"] = pd.to_numeric(prices["가격(원)"], errors="coerce")

    subway["자치구"] = subway["도로명주소"].apply(extract_gu)
    subway["자치구"] = subway["자치구"].fillna(subway["구주소"].apply(extract_gu))

    districts = sorted(DISTRICT_COORDS.keys())

    culture_count = culture.groupby("자치구").size().reindex(districts, fill_value=0)
    library_count = library.groupby("구명").size().reindex(districts, fill_value=0)
    park_count = parks.groupby("지역").size().reindex(districts, fill_value=0)
    subway_count = subway.groupby("자치구").size().reindex(districts, fill_value=0)
    avg_price = prices.groupby("자치구 이름")["가격(원)"].mean().round().reindex(districts, fill_value=np.nan)

    culture_theme_top = (
        culture.groupby(["자치구","주제분류"]).size()
        .reset_index(name="count")
        .sort_values(["자치구","count"], ascending=[True, False])
    )

    line_map = (
        subway.dropna(subset=["자치구"])
        .groupby("자치구")["호선"]
        .apply(lambda x: sorted(set(x.astype(str))))
        .reindex(districts, fill_value=[])
    )

    station_map = (
        subway.dropna(subset=["자치구"])
        .groupby("자치구")["역명"]
        .apply(lambda x: sorted(set(x.astype(str))))
        .reindex(districts, fill_value=[])
    )

    rows = []
    for gu in districts:
        rs = EMBEDDED_RENT_SUMMARY.get(gu, {"median": np.nan, "mean": np.nan, "count": 0})
        rows.append({
            "자치구": gu,
            "대표월세": rs["median"],
            "평균월세": rs["mean"],
            "월세표본수": rs["count"],
            "생활물가평균": int(avg_price.get(gu)) if pd.notna(avg_price.get(gu)) else np.nan,
            "문화공간수": int(culture_count.get(gu, 0)),
            "공공도서관수": int(library_count.get(gu, 0)),
            "공원수": int(park_count.get(gu, 0)),
            "지하철역수": int(subway_count.get(gu, 0)),
            "지하철노선": ", ".join(line_map.get(gu, [])) if isinstance(line_map.get(gu, []), list) else "",
            "주요역": ", ".join(station_map.get(gu, [])[:8]) if isinstance(station_map.get(gu, []), list) else "",
        })
    summary = pd.DataFrame(rows)

    # 점수용 정규화
    def minmax(series, reverse=False):
        s = series.astype(float)
        if s.max() == s.min():
            out = pd.Series([0.5]*len(s), index=s.index)
        else:
            out = (s - s.min()) / (s.max() - s.min())
        return 1 - out if reverse else out

    summary["월세점수"] = minmax(summary["대표월세"], reverse=True)
    summary["물가점수"] = minmax(summary["생활물가평균"], reverse=True)
    summary["문화점수"] = minmax(summary["문화공간수"])
    summary["공원점수"] = minmax(summary["공원수"])
    summary["도서관점수"] = minmax(summary["공공도서관수"])
    summary["교통점수"] = minmax(summary["지하철역수"])

    return summary, culture, library, subway, prices, parks, culture_theme_top, line_map, station_map

summary, culture, library, subway, prices, parks, culture_theme_top, line_map, station_map = prepare_data()

# -----------------------------
# GeoJSON 로딩
# -----------------------------
@st.cache_data(show_spinner=False)
def load_geojson():
    urls = [
        "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json",
        "https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo.json"
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=12)
            if r.ok:
                return r.json()
        except Exception:
            continue
    return None

geojson_data = load_geojson()

# -----------------------------
# 추천 로직
# -----------------------------
def apply_budget_filter(df, budget_band):
    if budget_band == "상관없음":
        return df.copy()
    if budget_band == "50만원 이하":
        return df[df["대표월세"] <= 50]
    if budget_band == "50만원대":
        return df[(df["대표월세"] >= 50) & (df["대표월세"] < 60)]
    if budget_band == "60만원대":
        return df[(df["대표월세"] >= 60) & (df["대표월세"] < 70)]
    if budget_band == "70만원대":
        return df[(df["대표월세"] >= 70) & (df["대표월세"] < 80)]
    if budget_band == "80만원대":
        return df[(df["대표월세"] >= 80) & (df["대표월세"] < 90)]
    if budget_band == "90만원 이상":
        return df[df["대표월세"] >= 90]
    return df.copy()

def score_recommendations(df, weights, budget_band, university, selected_lines, level):
    rec = df.copy()
    total = sum(weights.values()) or 1
    norm = {k: v/total for k,v in weights.items()}

    rec["추천점수"] = (
        rec["월세점수"] * norm["월세"] +
        rec["물가점수"] * norm["물가"] +
        rec["교통점수"] * norm["교통"] +
        rec["문화점수"] * norm["문화"] +
        rec["공원점수"] * norm["공원"] +
        rec["도서관점수"] * norm["도서관"]
    )

    # 대학 보너스
    uni_info = UNIVERSITY_MAP.get(university, {"districts":[]})
    for gu in uni_info.get("districts", []):
        rec.loc[rec["자치구"] == gu, "추천점수"] += 0.08

    # 자취 레벨 보너스
    lv = BEGINNER_LEVEL_BONUS.get(level, {"bonus_districts":[]})
    for gu in lv.get("bonus_districts", []):
        rec.loc[rec["자치구"] == gu, "추천점수"] += 0.05

    # 호선 보너스
    if selected_lines:
        def line_bonus(lines):
            lines = lines or ""
            matched = sum(1 for x in selected_lines if x in lines)
            return matched * 0.04
        rec["추천점수"] += rec["지하철노선"].apply(line_bonus)

    rec = apply_budget_filter(rec, budget_band)

    # 필터로 아무 지역도 안 남으면 원본에서 재계산 없이 메시지용으로 반환
    return rec.sort_values(["추천점수", "문화공간수", "교통점수"], ascending=False)

def budget_is_low(budget_band):
    return budget_band in ["50만원 이하", "50만원대"]

def get_budget_text(budget_band):
    if budget_band == "상관없음":
        return "예산 제한 없음"
    return budget_band

def district_culture_details(gu):
    sub = culture[culture["자치구"] == gu].copy()
    if sub.empty:
        return [], pd.DataFrame(columns=["주제분류","count"]), pd.DataFrame(columns=["문화시설명","주제분류","주소"])
    top_types = (
        sub.groupby("주제분류").size().reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    top_fac = sub[["문화시설명","주제분류","주소"]].drop_duplicates().head(10)
    return sub["주제분류"].unique().tolist(), top_types, top_fac

def district_story(gu):
    if gu in DISTRICT_STORIES:
        return DISTRICT_STORIES[gu]
    row = summary[summary["자치구"] == gu].iloc[0]
    pros = []
    cons = []
    if row["대표월세"] <= RENT_META["overall_mean"]:
        pros.append("서울 평균 대비 월세 부담이 비교적 낮은 편")
    else:
        cons.append("서울 평균보다 월세 부담이 높은 편")
    if row["지하철역수"] >= summary["지하철역수"].median():
        pros.append("대중교통 선택지가 무난한 편")
    else:
        cons.append("생활 동선에 따라 환승 체감이 있을 수 있음")
    if row["문화공간수"] >= summary["문화공간수"].median():
        pros.append("전시·공연·문화공간 접근이 무난함")
    else:
        cons.append("문화생활은 다른 생활권으로 이동하는 경우가 있음")
    if row["공원수"] >= summary["공원수"].median():
        pros.append("산책·휴식 가능한 녹지 접근성이 괜찮은 편")
    return {
        "summary": f"{gu}은(는) 월세·생활 인프라·교통의 균형을 보고 접근하기 좋은 생활권입니다.",
        "pros": pros or ["기본적인 생활 인프라는 무난한 편"],
        "cons": cons or ["매물 상태와 실제 귀가 동선은 꼭 현장 확인 권장"],
        "one_line": "데이터상 균형은 괜찮지만, 최종 선택은 매물 컨디션과 동선 확인이 중요합니다."
    }

# -----------------------------
# 헤더
# -----------------------------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="main-title">서울, 처음이니? : 어디서 자취할까?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">서울 2030 자취가구와 상경 대학생을 위한 지역 큐레이션 서비스 · 월세, 물가, 교통, 문화생활, 공원, 도서관을 함께 비교해 추천해요.</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.header("추천 조건")
    budget_band = st.selectbox(
        "희망 월세 가격대",
        ["상관없음","50만원 이하","50만원대","60만원대","70만원대","80만원대","90만원 이상"],
        index=2
    )

    university = st.selectbox("재학 중인 대학교", list(UNIVERSITY_MAP.keys()), index=0)

    all_lines = sorted(subway["호선"].dropna().astype(str).unique().tolist())
    selected_lines = st.multiselect("원하는 지하철 노선", all_lines, default=[])

    level = st.selectbox("자취 레벨", list(BEGINNER_LEVEL_BONUS.keys()), index=0)

    st.markdown("### 중요도 설정")
    with st.expander("중요도 기준 안내", expanded=True):
        st.markdown(
            """
            - **0점**: 거의 안 봐도 됨  
            - **1~2점**: 있으면 좋음  
            - **3점**: 적당히 중요  
            - **4점**: 꽤 중요  
            - **5점**: 최우선  
            """
        )
    w_rent = st.slider("월세", 0, 5, 5)
    w_price = st.slider("생활물가", 0, 5, 3)
    w_transit = st.slider("교통", 0, 5, 4)
    w_culture = st.slider("문화생활", 0, 5, 3)
    w_park = st.slider("공원/산책", 0, 5, 2)
    w_library = st.slider("도서관/공부환경", 0, 5, 2)

weights = {
    "월세": w_rent,
    "물가": w_price,
    "교통": w_transit,
    "문화": w_culture,
    "공원": w_park,
    "도서관": w_library
}

recommend_df = score_recommendations(summary, weights, budget_band, university, selected_lines, level)

# 상세 지역 선택은 추천 결과 최상단 기본
default_district = recommend_df["자치구"].iloc[0] if not recommend_df.empty else "관악구"

# -----------------------------
# 상단 핵심 지표
# -----------------------------
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">서울 평균 월세</div><div class="metric-value">{RENT_META["overall_mean"]:.0f}만원</div><div class="metric-desc">1인 가구 적합 주택군 기준 평균</div></div>',
        unsafe_allow_html=True
    )
with m2:
    avg_price_all = int(round(prices["가격(원)"].mean()))
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">서울 생활물가 평균</div><div class="metric-value">{avg_price_all:,}원</div><div class="metric-desc">업로드된 생필품 가격 데이터 평균</div></div>',
        unsafe_allow_html=True
    )
with m3:
    top_area = default_district
    top_row = recommend_df.iloc[0] if not recommend_df.empty else summary[summary["자치구"]=="관악구"].iloc[0]
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">현재 추천 1위</div><div class="metric-value">{top_area}</div><div class="metric-desc">대표 월세 {int(top_row["대표월세"])}만원 · 추천점수 {top_row["추천점수"]:.2f}</div></div>',
        unsafe_allow_html=True
    )
with m4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">예산 조건</div><div class="metric-value">{get_budget_text(budget_band)}</div><div class="metric-desc">선택한 조건으로 추천 중</div></div>',
        unsafe_allow_html=True
    )

if budget_is_low(budget_band):
    st.markdown(
        '<div class="warn-box"><b>저예산 선택 안내</b><br>' +
        " ".join([f"• {x}" for x in LOW_BUDGET_WARNINGS]) +
        '</div>',
        unsafe_allow_html=True
    )

uni_tip = UNIVERSITY_MAP.get(university, UNIVERSITY_MAP["해당 없음"])["tip"]
lv_tip = BEGINNER_LEVEL_BONUS[level]["tip"]
st.markdown(
    f'<div class="tip-box"><b>현재 추천 로직 설명</b><br>대학 통학: {uni_tip}<br>자취 레벨: {lv_tip}<br>선택한 지하철 노선: ' +
    (", ".join(selected_lines) if selected_lines else "미선택") +
    '</div>',
    unsafe_allow_html=True
)

# -----------------------------
# 탭
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["🏆 추천 결과", "🗺️ 지도 & 지역 상세", "📊 비교 분석", "🎒 자취 가이드"])

with tab1:
    st.markdown('<div class="section-title">우선순위에 맞는 추천 지역 TOP 5</div>', unsafe_allow_html=True)
    if recommend_df.empty:
        st.warning("선택한 월세 가격대와 조건에 맞는 구가 없습니다. 월세 조건을 조금 넓혀 보세요.")
    else:
        top5 = recommend_df.head(5).reset_index(drop=True)
        cols = st.columns(5)
        for i, (_, row) in enumerate(top5.iterrows()):
            score = row["추천점수"]
            delta = row["평균월세"] - RENT_META["overall_mean"]
            score_reason = []
            if row["대표월세"] <= RENT_META["overall_mean"]:
                score_reason.append("월세 부담 낮음")
            if row["지하철역수"] >= summary["지하철역수"].median():
                score_reason.append("교통 편의")
            if row["문화공간수"] >= summary["문화공간수"].median():
                score_reason.append("문화생활 강점")
            if row["공원수"] >= summary["공원수"].median():
                score_reason.append("산책/녹지 무난")
            if row["공공도서관수"] >= summary["공공도서관수"].median():
                score_reason.append("공부환경 괜찮음")
            badges = "".join([f'<span class="badge">{x}</span>' for x in score_reason[:4]])
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="rec-card">
                        <span class="rec-rank">TOP {i+1}</span>
                        <div class="rec-title">{row['자치구']}</div>
                        <div class="rec-sub">
                            대표 월세 <b>{int(row['대표월세'])}만원</b><br>
                            서울 평균 대비 <b>{delta:+.1f}만원</b><br>
                            추천점수 <b>{score:.2f}</b>
                        </div>
                        <div style="margin-top:0.6rem;">{badges}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("#### 추천 결과 표")
        show_cols = ["자치구","대표월세","평균월세","생활물가평균","지하철역수","문화공간수","공원수","공공도서관수","추천점수"]
        st.dataframe(
            top5[show_cols].rename(columns={"대표월세":"대표월세(만원)","평균월세":"평균월세(만원)","생활물가평균":"생활물가평균(원)"}),
            use_container_width=True,
            hide_index=True
        )

with tab2:
    st.markdown('<div class="section-title">서울 자치구 지도</div>', unsafe_allow_html=True)
    st.caption("지도에서 구역을 클릭하면 기본 정보를 팝업으로 볼 수 있어요. 아래 선택창으로 지역 상세도 함께 확인할 수 있습니다.")

    map_df = recommend_df.copy()
    if map_df.empty:
        map_df = summary.copy()

    m = folium.Map(location=[37.55,126.98], zoom_start=11, tiles="CartoDB positron")
    color_scale = linear.YlGnBu_09.scale(map_df["추천점수"].min(), map_df["추천점수"].max() if map_df["추천점수"].max() != map_df["추천점수"].min() else map_df["추천점수"].min()+1)

    if geojson_data:
        popup_map = map_df.set_index("자치구").to_dict(orient="index")

        def style_fn(feature):
            gu = feature["properties"].get("name")
            row = popup_map.get(gu, None)
            score = row["추천점수"] if row and "추천점수" in row else 0.5
            return {
                "fillColor": color_scale(score),
                "color": "#334155",
                "weight": 1.2,
                "fillOpacity": 0.72
            }

        for feat in geojson_data.get("features", []):
            gu = feat["properties"].get("name")
            row = popup_map.get(gu)
            popup_html = f"<b>{gu}</b><br>데이터 없음"
            if row:
                popup_html = (
                    f"<b>{gu}</b><br>"
                    f"대표 월세: {int(row['대표월세'])}만원<br>"
                    f"생활물가 평균: {int(row['생활물가평균']):,}원<br>"
                    f"지하철역: {int(row['지하철역수'])}개<br>"
                    f"문화공간: {int(row['문화공간수'])}개<br>"
                    f"공원: {int(row['공원수'])}개<br>"
                    f"도서관: {int(row['공공도서관수'])}개<br>"
                    f"추천점수: {row['추천점수']:.2f}"
                )
            gj = folium.GeoJson(
                data=feat,
                style_function=style_fn,
                tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["자치구"]),
                popup=folium.Popup(popup_html, max_width=280),
                highlight_function=lambda x: {"weight": 3, "color": "#0f172a", "fillOpacity": 0.85}
            )
            gj.add_to(m)
    else:
        for _, row in map_df.iterrows():
            lat, lon = DISTRICT_COORDS[row["자치구"]]
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                color="#0f172a",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.75,
                popup=folium.Popup(
                    f"<b>{row['자치구']}</b><br>대표 월세 {int(row['대표월세'])}만원<br>추천점수 {row['추천점수']:.2f}",
                    max_width=250
                )
            ).add_to(m)

    st_folium(m, use_container_width=True, height=560)

    district_options = summary["자치구"].tolist()
    selected_district = st.selectbox("지역 상세 보기", district_options, index=district_options.index(default_district))
    detail = summary[summary["자치구"] == selected_district].iloc[0]
    story = district_story(selected_district)
    _, top_types, top_fac = district_culture_details(selected_district)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("대표 월세", f"{int(detail['대표월세'])}만원", f"서울 평균 대비 {detail['평균월세'] - RENT_META['overall_mean']:+.1f}만원")
    c2.metric("생활물가 평균", f"{int(detail['생활물가평균']):,}원")
    c3.metric("지하철역 수", f"{int(detail['지하철역수'])}개")
    c4.metric("문화공간 수", f"{int(detail['문화공간수'])}개")

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown(f"### {selected_district} 현실 자취생 시선")
        st.markdown(f'<div class="good-box"><b>한 줄 정리</b><br>{story["one_line"]}</div>', unsafe_allow_html=True)
        st.markdown(f"**지역 특징**  \n{story['summary']}")
        st.markdown("**장점**")
        for x in story["pros"]:
            st.markdown(f"- {x}")
        st.markdown("**주의할 점**")
        for x in story["cons"]:
            st.markdown(f"- {x}")
        st.markdown("**지하철 노선**")
        st.markdown(detail["지하철노선"] if detail["지하철노선"] else "표시 가능한 노선 정보가 부족합니다.")
        st.markdown("**주요 역**")
        st.markdown(detail["주요역"] if detail["주요역"] else "표시 가능한 역 정보가 부족합니다.")

    with right:
        st.markdown("### 문화생활은 무엇이 많을까?")
        if top_types.empty:
            st.info("문화공간 데이터가 부족합니다.")
        else:
            st.dataframe(top_types.rename(columns={"주제분류":"문화 유형","count":"개수"}), use_container_width=True, hide_index=True)
            st.markdown("**대표 시설 예시**")
            st.dataframe(top_fac.rename(columns={"문화시설명":"시설명","주제분류":"문화 유형"}), use_container_width=True, hide_index=True)

with tab3:
    st.markdown('<div class="section-title">비교 분석</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            summary.sort_values("대표월세"),
            x="자치구", y="대표월세",
            color="대표월세",
            color_continuous_scale="Blues",
            title="자치구별 대표 월세 비교"
        )
        fig.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = px.scatter(
            summary,
            x="생활물가평균", y="대표월세",
            size="문화공간수", color="지하철역수",
            hover_name="자치구",
            title="월세 vs 생활물가 vs 문화공간"
        )
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

    selected_for_radar = st.selectbox("레이더 차트 지역 선택", summary["자치구"], index=summary["자치구"].tolist().index(default_district))
    rr = summary[summary["자치구"] == selected_for_radar].iloc[0]
    radar_categories = ["월세점수","물가점수","교통점수","문화점수","공원점수","도서관점수"]
    radar_labels = ["월세","물가","교통","문화","공원","도서관"]
    radar_vals = [rr[c] for c in radar_categories]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatterpolar(r=radar_vals, theta=radar_labels, fill='toself', name=selected_for_radar))
    fig3.update_layout(height=460, showlegend=False, polar=dict(radialaxis=dict(visible=True, range=[0,1])))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 전체 비교 테이블")
    compare_cols = ["자치구","대표월세","평균월세","생활물가평균","지하철역수","문화공간수","공원수","공공도서관수","지하철노선"]
    st.dataframe(summary[compare_cols].rename(columns={"대표월세":"대표월세(만원)","평균월세":"평균월세(만원)","생활물가평균":"생활물가평균(원)"}), use_container_width=True, hide_index=True)

with tab4:
    st.markdown('<div class="section-title">2030 자취생을 위한 실용 기능</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("### 대학생/상경러 체크포인트")
        st.markdown(
            """
            - **통학 15분 룰**: 학교/알바/출근 동선이 15분 내로 줄어드는지 먼저 보세요.  
            - **언덕/골목 확인**: 지도상 가까워도 실제 체감은 다릅니다. 특히 밤길과 오르막은 꼭 체크.  
            - **관리비 포함 실지출**: 월세만이 아니라 관리비, 전기, 가스, 인터넷까지 합산해 보세요.  
            - **생활권의 결**: 조용한 동네를 원하면 대학가 한복판보다 1~2정거장 옆 생활권이 나을 수 있어요.  
            """
        )
        st.markdown("### 저예산 선택 시 꼭 볼 것")
        for x in LOW_BUDGET_WARNINGS:
            st.markdown(f"- {x}")
    with g2:
        st.markdown("### 서울메이트형 고도화 아이디어")
        st.markdown(
            """
            - **거품 탐지기**: 구 평균 시세 대비 매물 가격 과열 여부 표시  
            - **밤길 안심 스코어**: CCTV/가로등/귀가동선 기반 안전 체감 레이어  
            - **실시간 역세권 컷**: 도보 + 지하철 + 환승 시간을 묶은 통학/출근 시간 계산  
            - **자취 레벨 큐레이션**: 비기너 / 프로 자취러 / 동네 정착러별 추천  
            """
        )
        st.markdown("### 추천 대상별 빠른 추천")
        quick = pd.DataFrame([
            ["가성비 대학생", "관악구, 동작구, 동대문구, 성북구", "월세 부담과 통학/생활 인프라 균형"],
            ["문화생활 중시", "마포구, 성동구, 광진구, 종로구", "전시·공연·복합문화공간 접근 우수"],
            ["직주근접 중시", "강남구, 서초구, 영등포구, 성동구", "업무지구 이동 효율"],
            ["산책/공원 중시", "종로구, 강서구, 은평구, 강동구", "공원·녹지 접근성이 상대적으로 좋음"],
        ], columns=["유형","추천 구","이유"])
        st.dataframe(quick, use_container_width=True, hide_index=True)

st.markdown('<div class="small-note">월세 비교 기준은 업로드된 서울시 전월세가 CSV에서 1인 가구 적합 주택군(단독다가구·연립다세대·오피스텔)의 구별 대표 월세를 요약해 반영했습니다. 생활물가 평균은 업로드된 생필품 가격 데이터 평균값을 정수 반올림해 표시합니다.</div>', unsafe_allow_html=True)
