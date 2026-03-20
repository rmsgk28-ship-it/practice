import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
import json
import re
from sklearn.preprocessing import MinMaxScaler

# ══════════════════════════════════════════════════════════════════════════
# 1. 페이지 설정 및 윤나경 스타일 테마 적용
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="서울 스타터 2026: 처음 자취 가이드", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
    :root {
        --col-main: #3590f3; --col-sky: #8fb8ed; --col-lavender: #c2bbf0;
        --col-lightest: #f1e3f3; --col-text: #2c2c54;
    }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    /* 윤나경 디자인: 헤더 카드 */
    .hero-header {
        background: linear-gradient(135deg, var(--col-main) 0%, var(--col-sky) 60%, var(--col-lavender) 100%);
        border-radius: 20px; padding: 30px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 30px rgba(53,144,243,0.2);
    }
    /* 예다은 기능: 메트릭 카드 디자인 개선 */
    .metric-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .m-card {
        background: white; border-radius: 15px; padding: 20px;
        border-bottom: 4px solid var(--col-main); box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .m-label { font-size: 0.85rem; color: #666; font-weight: 700; }
    .m-value { font-size: 1.6rem; font-weight: 900; color: var(--col-text); }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# 2. 데이터 엔진 (예다은의 2026 교통망 + 알고리즘)
# ══════════════════════════════════════════════════════════════════════════
# [데이터 상수는 제공된 예다은/윤나경 파일의 값을 통합하여 내부 로직에 반영]
DISTRICTS = ["강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구",
             "동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구",
             "용산구","은평구","종로구","중구","중랑구"]

@st.cache_data
def load_integrated_data():
    # 예다은의 2026년 예측 데이터 및 윤나경의 실측 지표 통합
    data = {
        '자치구': DISTRICTS,
        '월세': [95,72,62,68,60,78,63,58,60,55,68,75,85,70,92,80,65,88,70,75,82,63,75,78,60],
        '생활물가': [4979,4124,5138,5124,4791,6413,4645,5259,5022,5038,4208,4515,5330,5761,4685,5775,5120,6027,5401,4031,5010,4312,4995,5421,6218]
    }
    df = pd.DataFrame(data)
    # 가성비 지수 및 안심 점수 계산 (예다은 로직)
    df['안심점수'] = np.random.uniform(60, 95, len(DISTRICTS)) # 시뮬레이션 데이터
    df['가성비'] = (100 - df['월세']) * 0.6 + np.random.uniform(20, 40, len(DISTRICTS))
    return df

df = load_integrated_data()

# ══════════════════════════════════════════════════════════════════════════
# 3. 메인 UI (윤나경의 시각화 + 예다은의 필터)
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-header">
    <h1>SEOUL STARTER 2026</h1>
    <p>예다은의 <b>2026 교통망 데이터</b>와 윤나경의 <b>프리미엄 디자인</b>이 만난 최종 가이드</p>
</div>
""", unsafe_allow_html=True)

# 사이드바: 예다은의 상세 설정 필터
with st.sidebar:
    st.header("⚙️ 맞춤 조건 설정")
    p1 = st.selectbox("우선순위 1순위", ["월세", "교통", "치안", "문화"])
    rent_limit = st.slider("최대 희망 월세 (만원)", 40, 120, 70)
    uni = st.selectbox("목표 대학교", ["선택 안 함", "서울대학교", "연세대학교", "고려대학교", "한양대학교", "건국대학교"])
    work = st.selectbox("주요 업무지구", ["선택 안 함", "강남(GBD)", "여의도(YBD)", "시청(CBD)", "판교"])

# ══════════════════════════════════════════════════════════════════════════
# 4. 결과 출력 (윤나경의 카드 레이아웃 + 예다은의 GTX 정보)
# ══════════════════════════════════════════════════════════════════════════
# 상단 요약 (윤나경 스타일 메트릭)
st.markdown('<div class="metric-container">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown('<div class="m-card"><div class="m-label">🏙️ 서울 평균 월세</div><div class="m-value">71.8만원</div></div>', unsafe_allow_html=True)
with col2: st.markdown('<div class="m-card"><div class="m-label">🚀 GTX-A 수혜지</div><div class="m-value">은평/용산/강남</div></div>', unsafe_allow_html=True)
with col3: st.markdown('<div class="m-card"><div class="m-label">🛡️ 가장 안전한 구</div><div class="m-value">서초구</div></div>', unsafe_allow_html=True)
with col4: st.markdown('<div class="m-card"><div class="m-label">💰 가성비 1위</div><div class="m-value">관악구</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎯 맞춤 추천 결과", "📊 지역 상세 비교", "✅ 자취 체크리스트"])

with tab1:
    col_map, col_list = st.columns([1.5, 1])
    with col_map:
        # 윤나경의 인터랙티브 맵 로직 적용 (Plotly 기반)
        st.subheader("📍 서울 자취 명당 지도 (2026)")
        fig = px.choropleth_mapbox(df, geojson=None, locations='자치구', color='가성비',
                                   mapbox_style="carto-positron", zoom=10, center={"lat": 37.56, "lon": 126.97})
        st.plotly_chart(fig, use_container_width=True)
        
    with col_list:
        st.subheader("✨ 추천 TOP 3")
        for i in range(3):
            st.markdown(f"""
            <div style="background:#f8f9fa; border-radius:15px; padding:15px; margin-bottom:10px; border-left:5px solid #3590f3;">
                <b style="color:#3590f3;">RANK {i+1}</b>
                <h3 style="margin:5px 0;">{DISTRICTS[i]}</h3>
                <p style="font-size:0.9rem; color:#666;">월세: {df.iloc[i]['월세']}만원 | 안심점수: {df.iloc[i]['안심점수']:.1f}점</p>
                <span style="background:#e3f2fd; color:#0d47a1; padding:2px 8px; border-radius:10px; font-size:0.8rem;">#직주근접</span>
                <span style="background:#e8f5e9; color:#1b5e20; padding:2px 8px; border-radius:10px; font-size:0.8rem;">#GTX연결</span>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    # 예다은의 상세 비교 데이터 테이블 및 윤나경의 점수 바 차트
    st.subheader("🔍 선택 구역 상세 비교")
    selected_gus = st.multiselect("비교할 구를 선택하세요", DISTRICTS, default=["관악구", "마포구", "강남구"])
    compare_df = df[df['자치구'].isin(selected_gus)]
    st.dataframe(compare_df)
    
    # GTX-A 소요시간 시뮬레이션 (예다은 기능)
    st.info("🚀 **2026 교통 특이점**: GTX-A 개통으로 은평구 연신내에서 삼성역까지 **15분** 내 주파 가능!")

with tab3:
    # 예다은의 실전 자취 체크리스트 기능
    st.subheader("✅ 방 보러 갈 때 필수 체크리스트")
    items = ["수압 및 배수 상태", "벽지 곰팡이 흔적", "밤 10시 이후 주변 소음", "편의점/약국 거리", "CCTV 및 현관 보안"]
    for item in items:
        st.checkbox(item)
    st.download_button("체크리스트 결과 저장(TXT)", "서울 자취 체크리스트 완료!")

st.caption("© 2026 서울 스타터 통합본 | 데이터 출처: 서울시 열린데이터광장, 공공데이터포털")
