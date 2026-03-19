import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="서울시 대기질-보건 통합 대시보드",
    page_icon="🌫️",
    layout="wide",
)

# -----------------------------
# Mock data based on the report
# -----------------------------
district_data = pd.DataFrame(
    {
        "지역": ["강서구", "중구", "서초구", "강동구", "강북구"],
        "PM2.5": [55.7, 57.3, 50.8, 46.0, 41.3],
        "PM10": [84.8, 88.8, 77.0, 75.1, 69.8],
        "질환발생률(%)": [18.2, 19.5, 15.1, 11.5, 9.8],
        "기관지환자비율": [22.4, 24.1, 18.5, 13.8, 11.2],
        "인구밀도점수": ["상", "최상", "중", "중하", "하"],
    }
)

monthly_data = pd.DataFrame(
    {
        "월": ["1월", "4월", "8월", "11월"],
        "강서구": [88, 52, 20, 67],
        "중구": [92, 55, 22, 70],
        "서초구": [80, 48, 16, 60],
        "강동구": [74, 43, 13, 56],
        "강북구": [69, 40, 11, 52],
    }
)

correlation_value = 0.84
odds_ratio_value = 1.15

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("설정")
selected_district = st.sidebar.selectbox("지역 선택", district_data["지역"].tolist())
show_raw_data = st.sidebar.checkbox("원본 데이터 보기", value=False)

st.title("2026 서울시 대기질-보건 통합 분석 대시보드")
st.caption("보고서 기반 러프 프로토타입")

st.markdown(
    """
이 앱은 업로드된 보고서의 핵심 내용을 빠르게 시각화하기 위한 초안입니다.

- 자치구별 대기오염도 비교
- PM2.5와 기관지 질환의 관계 확인
- 월별 초미세먼지 추이 확인
- 정책 시사점 요약
"""
)

# -----------------------------
# KPI cards
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

highest_pm25_row = district_data.loc[district_data["PM2.5"].idxmax()]
lowest_pm25_row = district_data.loc[district_data["PM2.5"].idxmin()]

with col1:
    st.metric("고오염 지역", highest_pm25_row["지역"])
with col2:
    st.metric("저오염 지역", lowest_pm25_row["지역"])
with col3:
    st.metric("상관계수 (r)", f"{correlation_value:.2f}")
with col4:
    st.metric("질환 위험 증가 OR", f"{odds_ratio_value:.2f}배")

st.divider()

# -----------------------------
# Charts row 1
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("자치구별 대기오염 농도 비교")
    chart_df = district_data.melt(
        id_vars="지역",
        value_vars=["PM2.5", "PM10"],
        var_name="오염물질",
        value_name="농도"
    )
    fig_bar = px.bar(
        chart_df,
        x="지역",
        y="농도",
        color="오염물질",
        barmode="group",
        title="연평균 PM2.5 / PM10 비교"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.subheader("월별 PM2.5 추이")
    line_df = monthly_data.melt(
        id_vars="월",
        var_name="지역",
        value_name="PM2.5"
    )
    fig_line = px.line(
        line_df,
        x="월",
        y="PM2.5",
        color="지역",
        markers=True,
        title="지역별 월별 초미세먼지 추이"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# -----------------------------
# Charts row 2
# -----------------------------
left2, right2 = st.columns(2)

with left2:
    st.subheader("PM2.5 농도 vs 기관지 환자 비율")
    fig_scatter = px.scatter(
        district_data,
        x="PM2.5",
        y="기관지환자비율",
        text="지역",
        size="질환발생률(%)",
        hover_data=["PM10", "인구밀도점수"],
        title="PM2.5와 건강지표의 관계"
    )
    fig_scatter.update_traces(textposition="top center")
    st.plotly_chart(fig_scatter, use_container_width=True)

with right2:
    st.subheader(f"{selected_district} 상세")
    row = district_data[district_data["지역"] == selected_district].iloc[0]

    st.write(f"**PM2.5:** {row['PM2.5']} μg/m³")
    st.write(f"**PM10:** {row['PM10']} μg/m³")
    st.write(f"**질환 발생률:** {row['질환발생률(%)']}%")
    st.write(f"**기관지 환자 비율:** {row['기관지환자비율']}")
    st.write(f"**인구밀도 점수:** {row['인구밀도점수']}")

    if selected_district == "중구":
        st.info("도시 협곡(Street Canyon)과 고밀도 유동 인구의 영향을 대표하는 지역")
    elif selected_district == "강서구":
        st.info("서해안발 외부 오염 유입과 대기 정체 영향을 대표하는 지역")
    elif selected_district == "강북구":
        st.info("북한산 숲세권 및 산곡풍 환기 효과가 상대적으로 큰 지역")
    elif selected_district == "서초구":
        st.info("광역 교통망 및 이동 오염원 영향이 큰 지역")
    elif selected_district == "강동구":
        st.info("주거 중심 개발 특성을 가진 비교 지역")

st.divider()

# -----------------------------
# Policy summary
# -----------------------------
st.subheader("정책 시사점")
st.markdown(
    """
- **행정구역 중심 관리의 한계**: 대기오염은 경계 없이 이동하므로 광역 대응이 필요
- **보건 연계 강화 필요**: 농도 저감뿐 아니라 고위험군 보호 중심 정책 필요
- **비도로 이동 오염원 관리 필요**: 건설기계, 생활오염원 등 사각지대 보완 필요
- **디지털 트윈 / AI 예보 도입**: 초정밀 예측 및 실외활동 알림 시스템 고도화 필요
"""
)

# -----------------------------
# Raw data
# -----------------------------
if show_raw_data:
    st.subheader("원본 데이터")
    st.dataframe(district_data, use_container_width=True)
    st.dataframe(monthly_data, use_container_width=True)

st.divider()
st.caption(
    "본 앱의 수치는 업로드된 보고서의 요약 수치와 시각 자료를 바탕으로 구성한 프로토타입입니다."
)
