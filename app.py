import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ── 페이지 설정 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="서울시 반려동물 공공데이터 분석",
    page_icon="🐾",
    layout="wide",
)

# ── DB 연결 ────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "pet.db")

@st.cache_data
def query(sql: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(sql, conn)

# ── 헤더 ───────────────────────────────────────────────────────────────────────
st.title("🐾 서울시 반려동물 공공데이터 분석 대시보드")
st.caption("데이터 출처: 서울시 반려동물 등록현황 · 공원현황 · 반려동물 동반시설 · 인구밀도 (2025)")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 – 면적 대비 동물 의료시설 접근 용이성
# ══════════════════════════════════════════════════════════════════════════════
st.header("📍 Chart 1. 면적 대비 동물 의료시설 접근 용이성")
st.markdown(
    "반려동물이 아플 때 즉각 조치가 가능한지를 진단합니다. "
    "**의료시설 밀도** (동물병원+약국 수 ÷ 면적 km²)를 기본 지표로 삼되, "
    "등록 반려동물 1,000마리당 의료시설 수를 병행하여 **수요 대비 공급** 측면도 함께 봅니다."
)

SQL_1 = """
SELECT
    pf.district                                        AS 자치구,
    COUNT(*)                                           AS 의료시설수,
    pd.area_km2                                        AS 면적_km2,
    pr_sum.total_registered                            AS 등록동물수,
    ROUND(COUNT(*) * 1.0 / pd.area_km2, 2)            AS 면적당_의료시설,
    ROUND(COUNT(*) * 1000.0 / pr_sum.total_registered, 2) AS 동물1000마리당_시설
FROM pet_facilities pf
JOIN population_density pd
    ON pf.district = pd.district
JOIN (
    SELECT district, SUM(total_registered) AS total_registered
    FROM pet_registration
    GROUP BY district
) pr_sum ON pf.district = pr_sum.district
WHERE pf.sub_category IN ('동물병원', '동물약국')
GROUP BY pf.district
ORDER BY 면적당_의료시설 DESC
"""

df1 = query(SQL_1)

col_chart1, col_sql1 = st.columns([3, 2])

with col_chart1:
    # 버블차트: x=면적당 의료시설, y=동물1000마리당 시설, size=의료시설수, color=자치구
    fig1 = px.scatter(
        df1,
        x="면적당_의료시설",
        y="동물1000마리당_시설",
        size="의료시설수",
        color="자치구",
        text="자치구",
        title="자치구별 동물 의료시설 접근성 (버블 크기 = 시설 수)",
        labels={
            "면적당_의료시설": "면적당 의료시설 (개/km²)",
            "동물1000마리당_시설": "등록동물 1,000마리당 시설 수",
        },
        height=480,
        template="plotly_white",
    )
    fig1.update_traces(
        textposition="top center",
        marker=dict(opacity=0.75, line=dict(width=1, color="white")),
    )
    # 사분면 기준선 (중앙값)
    med_x = df1["면적당_의료시설"].median()
    med_y = df1["동물1000마리당_시설"].median()
    fig1.add_vline(x=med_x, line_dash="dot", line_color="gray", opacity=0.5)
    fig1.add_hline(y=med_y, line_dash="dot", line_color="gray", opacity=0.5)
    fig1.add_annotation(x=med_x, y=df1["동물1000마리당_시설"].max(),
                        text="중앙값", showarrow=False, font=dict(color="gray", size=10))
    st.plotly_chart(fig1, use_container_width=True)

with col_sql1:
    st.markdown("#### 🗄️ 사용한 SQL")
    st.code(SQL_1, language="sql")
    st.markdown("#### 💡 인사이트")
    st.info(
        "**중구·동대문구·양천구**는 면적당 의료시설 밀도가 높아 공간적 접근성이 뛰어납니다. "
        "반면 **서초구·종로구**는 면적이 넓어 밀도가 낮지만, 등록 동물 수 대비 시설은 충분한 편입니다. "
        "우상단(두 지표 모두 높음)에 위치한 자치구가 반려동물 의료 인프라가 가장 잘 갖춰진 지역입니다."
    )
    # 상위 5 테이블
    st.markdown("#### 📊 면적당 의료시설 밀도 TOP 5")
    st.dataframe(
        df1[["자치구", "의료시설수", "면적_km2", "면적당_의료시설", "동물1000마리당_시설"]]
        .head(5)
        .reset_index(drop=True),
        use_container_width=True,
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 – 실내/실외 반려시설 유형과 지역 특성
# ══════════════════════════════════════════════════════════════════════════════
st.header("🌳 Chart 2. 실내/실외 반려시설 유형과 지역 특성 분석")
st.markdown(
    "**실내 시설 비율**(인구밀도 높은 도심 → 실내 중심)과 "
    "**공원 수**(녹지 풍부 지역 → 실외 활동 가능)를 연계하여 "
    "지역의 '반려동물 친화 환경' 유형을 파악합니다."
)

SQL_2 = """
SELECT
    pf.district                                             AS 자치구,
    SUM(pf.is_indoor)                                       AS 실내시설수,
    SUM(pf.is_outdoor)                                      AS 실외시설수,
    COUNT(*)                                                AS 전체시설수,
    ROUND(SUM(pf.is_indoor) * 100.0 / COUNT(*), 1)         AS 실내비율_pct,
    ROUND(SUM(pf.is_outdoor) * 100.0 / COUNT(*), 1)        AS 실외비율_pct,
    COALESCE(pk.park_count, 0)                              AS 공원수,
    pd.pop_density                                          AS 인구밀도
FROM pet_facilities pf
LEFT JOIN (
    SELECT district, COUNT(*) AS park_count
    FROM parks
    GROUP BY district
) pk ON pf.district = pk.district
JOIN population_density pd ON pf.district = pd.district
GROUP BY pf.district
ORDER BY 실내비율_pct DESC
"""

df2 = query(SQL_2)

col_chart2, col_sql2 = st.columns([3, 2])

with col_chart2:
    # 정렬: 실내비율 내림차순
    df2_sorted = df2.sort_values("실내비율_pct", ascending=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=df2_sorted["자치구"],
        x=df2_sorted["실내비율_pct"],
        name="실내 시설 비율",
        orientation="h",
        marker_color="#4C9BE8",
    ))
    fig2.add_trace(go.Bar(
        y=df2_sorted["자치구"],
        x=df2_sorted["실외비율_pct"],
        name="실외 시설 비율",
        orientation="h",
        marker_color="#56C596",
    ))

    # 공원 수 scatter (보조 축)
    fig2.add_trace(go.Scatter(
        y=df2_sorted["자치구"],
        x=df2_sorted["공원수"],
        name="공원 수",
        mode="markers",
        marker=dict(symbol="diamond", size=10, color="#F4845F",
                    line=dict(width=1, color="white")),
        xaxis="x2",
    ))

    fig2.update_layout(
        title="자치구별 실내/실외 시설 비율 및 공원 수",
        barmode="stack",
        xaxis=dict(title="시설 비율 (%)", range=[0, 105]),
        xaxis2=dict(title="공원 수", overlaying="x", side="top",
                    range=[0, df2_sorted["공원수"].max() * 2.5]),
        yaxis=dict(title=""),
        legend=dict(orientation="h", y=-0.12),
        height=560,
        template="plotly_white",
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_sql2:
    st.markdown("#### 🗄️ 사용한 SQL")
    st.code(SQL_2, language="sql")
    st.markdown("#### 💡 인사이트")
    st.info(
        "대부분의 자치구에서 실내 시설이 80% 이상을 차지하나, "
        "**강서구·노원구·서초구**는 공원 수가 많아 실외 시설 비율도 상대적으로 높습니다. "
        "인구밀도가 높은 도심 자치구(동대문·중랑)는 실내 중심의 반려문화가 형성되어 있으며, "
        "녹지가 풍부한 외곽 자치구는 실내·실외 균형형으로 분류됩니다."
    )
    st.markdown("#### 📊 실외 비율 상위 5개 자치구")
    st.dataframe(
        df2.sort_values("실외비율_pct", ascending=False)
        [["자치구", "실내비율_pct", "실외비율_pct", "공원수", "인구밀도"]]
        .head(5)
        .reset_index(drop=True),
        use_container_width=True,
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 – 반려동물 밀집 지역 분석
# ══════════════════════════════════════════════════════════════════════════════
st.header("🐶 Chart 3. 반려동물 밀집 지역 분석")
st.markdown(
    "단순 등록 수 외에 **인구 대비 반려동물 비율**(반려화율)과 "
    "**면적 대비 반려동물 밀도**를 함께 활용합니다. "
    "반려화율이 높을수록 해당 자치구 주민의 반려동물 친화도가 높음을 의미합니다."
)

SQL_3 = """
SELECT
    pr.district                                                      AS 자치구,
    SUM(pr.total_registered)                                         AS 등록동물수,
    pd.population                                                    AS 인구수,
    pd.area_km2                                                      AS 면적_km2,
    pd.pop_density                                                   AS 인구밀도,
    ROUND(SUM(pr.total_registered) * 100.0 / pd.population, 2)      AS 반려화율_pct,
    ROUND(SUM(pr.total_registered) * 1.0 / pd.area_km2, 1)          AS 동물밀도_per_km2,
    COALESCE(fac.facility_count, 0)                                  AS 반려시설수
FROM pet_registration pr
JOIN population_density pd ON pr.district = pd.district
LEFT JOIN (
    SELECT district, COUNT(*) AS facility_count
    FROM pet_facilities
    GROUP BY district
) fac ON pr.district = fac.district
GROUP BY pr.district
ORDER BY 반려화율_pct DESC
"""

df3 = query(SQL_3)

col_chart3, col_sql3 = st.columns([3, 2])

with col_chart3:
    # 트리맵: 면적=등록동물수, 색상=반려화율
    fig3 = px.treemap(
        df3,
        path=["자치구"],
        values="등록동물수",
        color="반려화율_pct",
        color_continuous_scale="YlOrRd",
        hover_data={
            "인구수": True,
            "반려화율_pct": ":.2f",
            "동물밀도_per_km2": ":.1f",
            "반려시설수": True,
        },
        title="자치구별 반려동물 밀집도<br>(면적=등록동물수, 색상=반려화율%)",
        height=480,
    )
    fig3.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,}마리<br>반려화율 %{color:.1f}%",
        textfont_size=13,
    )
    fig3.update_layout(coloraxis_colorbar=dict(title="반려화율(%)"))
    st.plotly_chart(fig3, use_container_width=True)

    # 보조: 산점도 - 인구밀도 vs 반려화율
    fig3b = px.scatter(
        df3,
        x="인구밀도",
        y="반려화율_pct",
        size="등록동물수",
        color="동물밀도_per_km2",
        text="자치구",
        color_continuous_scale="Blues",
        labels={
            "인구밀도": "인구밀도 (명/km²)",
            "반려화율_pct": "반려화율 (%)",
            "동물밀도_per_km2": "동물밀도(마리/km²)",
        },
        title="인구밀도 vs 반려화율 (버블 크기 = 등록동물 수)",
        height=400,
        template="plotly_white",
    )
    fig3b.update_traces(textposition="top center",
                        marker=dict(opacity=0.8, line=dict(width=1, color="white")))
    st.plotly_chart(fig3b, use_container_width=True)

with col_sql3:
    st.markdown("#### 🗄️ 사용한 SQL")
    st.code(SQL_3, language="sql")
    st.markdown("#### 💡 인사이트")
    st.info(
        "**강북구·은평구·강남구**는 반려화율(등록동물/인구)이 높아 "
        "반려동물 친화적 주거 문화가 정착된 지역으로 볼 수 있습니다. "
        "인구밀도와 반려화율 사이에는 뚜렷한 음의 상관관계가 나타나, "
        "인구가 밀집한 도심보다 상대적으로 여유 공간이 있는 외곽 자치구에서 "
        "반려동물 양육 비율이 더 높은 경향이 확인됩니다."
    )
    st.markdown("#### 📊 반려화율 TOP 5")
    st.dataframe(
        df3[["자치구", "등록동물수", "인구수", "반려화율_pct", "동물밀도_per_km2"]]
        .head(5)
        .reset_index(drop=True),
        use_container_width=True,
    )

st.divider()

# ── 푸터 ───────────────────────────────────────────────────────────────────────
st.caption(
    "※ 반려화율은 등록된 동물 수 기준이므로 미등록 반려동물은 포함되지 않습니다. "
    "실제 반려동물 수는 더 많을 수 있습니다."
)
