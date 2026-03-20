import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

st.set_page_config(
page_title="서울 자취 추천 플랫폼",
layout="wide"
)

st.title("서울 자취 추천 플랫폼")

st.markdown("당신의 우선순위를 선택하면 자취하기 좋은 지역을 추천합니다.")

# -----------------------------------
# 데이터 로드
# -----------------------------------

culture = pd.read_csv("서울시 문화공간 정보.csv")
library = pd.read_csv("서울시 공공도서관 현황정보.csv")
subway = pd.read_csv("서울교통공사_역주소 및 전화번호.csv")
parks = pd.read_excel("서울시 주요 공원현황(2026 상반기).xlsx")

# -----------------------------------
# 자치구별 집계
# -----------------------------------

culture_count = culture.groupby("자치구").size()
library_count = library.groupby("자치구").size()
park_count = parks.groupby("자치구").size()
subway_count = subway.groupby("자치구").size()

df = pd.DataFrame({
"문화시설":culture_count,
"도서관":library_count,
"공원":park_count,
"지하철":subway_count
}).fillna(0)

# -----------------------------------
# 정규화
# -----------------------------------

scaler = MinMaxScaler()

df_scaled = pd.DataFrame(
scaler.fit_transform(df),
columns=df.columns,
index=df.index
)

# -----------------------------------
# 사용자 우선순위
# -----------------------------------

st.sidebar.title("우선순위 설정")

culture_w = st.sidebar.slider("문화시설",0.0,1.0,0.5)
park_w = st.sidebar.slider("공원",0.0,1.0,0.5)
transport_w = st.sidebar.slider("지하철",0.0,1.0,0.5)
library_w = st.sidebar.slider("도서관",0.0,1.0,0.5)

# -----------------------------------
# 추천 점수
# -----------------------------------

df_scaled["score"] = (
df_scaled["문화시설"] * culture_w +
df_scaled["공원"] * park_w +
df_scaled["지하철"] * transport_w +
df_scaled["도서관"] * library_w
)

recommend = df_scaled.sort_values("score",ascending=False)

# -----------------------------------
# 추천 결과
# -----------------------------------

st.subheader("추천 지역 TOP5")

st.dataframe(recommend.head())

# -----------------------------------
# 그래프
# -----------------------------------

fig = px.bar(
recommend.reset_index(),
x="자치구",
y="score",
title="자취 추천 점수"
)

st.plotly_chart(fig)
