import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import numpy as np
import os

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="서울시 반려동물 생활 환경 분석",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 전역 CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap');
:root {
    --bg:#0d1117; --surface:#161b22; --surface2:#1c2330; --border:#30363d;
    --accent:#f7971e; --accent2:#ffd200; --green:#3fb950;
    --blue:#58a6ff; --purple:#bc8cff; --red:#ff7b72;
    --text:#e6edf3; --muted:#7d8590;
}
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;background:var(--bg);color:var(--text);}
.main{background:var(--bg);}
.block-container{padding-top:1.5rem;padding-bottom:3rem;}
section[data-testid="stSidebar"]{background:var(--surface);border-right:1px solid var(--border);}

.hero{background:linear-gradient(135deg,#0d1117 0%,#1c2330 50%,#0d1117 100%);
      border:1px solid var(--border);border-radius:16px;padding:2.4rem 3rem;
      margin-bottom:1.5rem;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
               background:linear-gradient(90deg,var(--accent),var(--accent2),var(--accent));}
.hero-title{font-size:2.1rem;font-weight:900;color:var(--text);margin:0 0 .35rem;line-height:1.2;}
.hero-title span{color:var(--accent);}
.hero-sub{color:var(--muted);font-size:.95rem;margin:0;}

.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;}
.kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;
           padding:1.2rem 1.4rem;position:relative;overflow:hidden;}
.kpi-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px;}
.kpi-card.c1::after{background:var(--accent);}
.kpi-card.c2::after{background:var(--accent2);}
.kpi-card.c3::after{background:var(--green);}
.kpi-card.c4::after{background:var(--blue);}
.kpi-label{font-size:.73rem;color:var(--muted);margin-bottom:.35rem;}
.kpi-value{font-size:1.75rem;font-weight:900;font-family:'Space Mono',monospace;color:var(--text);}
.kpi-unit{font-size:.78rem;color:var(--muted);margin-top:.15rem;}

.sec-wrap{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--border);
           padding-bottom:.7rem;margin:2.4rem 0 1.4rem;}
.sec-num{width:32px;height:32px;border-radius:8px;background:var(--accent);color:#000;
          font-family:'Space Mono',monospace;font-weight:700;font-size:.88rem;
          display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.sec-title{font-size:1.2rem;font-weight:700;margin:0;color:var(--text);}
.sec-desc{font-size:.82rem;color:var(--muted);margin:0;}

.sql-label{font-size:.68rem;font-weight:700;letter-spacing:.12em;color:var(--blue);
            text-transform:uppercase;margin-bottom:.45rem;font-family:'Space Mono',monospace;}
.sql-panel{background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--blue);
            border-radius:8px;padding:1rem 1.2rem;font-family:'Space Mono',monospace;
            font-size:.76rem;color:#a5d6ff;white-space:pre;overflow-x:auto;line-height:1.75;}

.insight{background:linear-gradient(135deg,#161b22,#1c2330);border:1px solid var(--border);
          border-left:4px solid var(--accent);border-radius:10px;padding:1.1rem 1.4rem;margin-top:1rem;}
.insight-title{font-size:.68rem;font-weight:700;letter-spacing:.12em;color:var(--accent);
                text-transform:uppercase;margin-bottom:.5rem;font-family:'Space Mono',monospace;}
.insight p{color:#c9d1d9;font-size:.88rem;line-height:1.8;margin:0;}
.insight p strong{color:var(--accent2);}

.rank-wrap{background:var(--surface);border:1px solid var(--border);
            border-radius:12px;overflow:hidden;max-height:560px;overflow-y:auto;}
.rank-row{display:flex;align-items:center;padding:9px 14px;border-bottom:1px solid #21262d;gap:12px;}
.rank-row:last-child{border-bottom:none;}
.rank-medal{width:26px;font-size:1rem;text-align:center;flex-shrink:0;}
.rank-name{flex:1;font-size:.9rem;font-weight:500;}
.rank-score{width:88px;text-align:right;}
.rank-score .val{font-size:.88rem;font-weight:700;color:var(--text);}
.score-bar{height:5px;border-radius:3px;margin-top:4px;}

[data-baseweb="tab-list"]{background:var(--surface)!important;border-radius:8px;padding:4px;border:1px solid var(--border);}
[data-baseweb="tab"]{color:var(--muted)!important;border-radius:6px!important;}
[aria-selected="true"]{background:var(--accent)!important;color:#000!important;font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

# ── DB 연결 ───────────────────────────────────────────────────────────────────
DB_PATHS = ['/mnt/user-data/uploads/pet.db', './pet.db', '/home/claude/pet.db']

@st.cache_resource
def get_conn():
    for p in DB_PATHS:
        if os.path.exists(p):
            return sqlite3.connect(p, check_same_thread=False)
    st.error("pet.db 파일을 찾을 수 없습니다. 앱과 같은 폴더에 pet.db를 놓아주세요.")
    st.stop()

@st.cache_data
def q(sql):
    return pd.read_sql(sql, get_conn())

# ── 플롯 공통 스타일 ──────────────────────────────────────────────────────────
BG = "#0d1117"; SRF = "#161b22"; GRID = "#21262d"; TXT = "#e6edf3"; MUT = "#7d8590"
BASE = dict(
    plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(family="Noto Sans KR", color=TXT, size=12),
    xaxis=dict(gridcolor=GRID, linecolor="#30363d", tickfont=dict(size=11)),
    yaxis=dict(gridcolor=GRID, linecolor="#30363d", tickfont=dict(size=11)),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hoverlabel=dict(bgcolor=SRF, bordercolor="#30363d", font=dict(color=TXT)),
)

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────
def section(num, title, desc=""):
    st.markdown(f"""
    <div class="sec-wrap">
      <div class="sec-num">{num}</div>
      <div>
        <p class="sec-title">{title}</p>
        {"<p class='sec-desc'>"+desc+"</p>" if desc else ""}
      </div>
    </div>""", unsafe_allow_html=True)

def sql_block(sql):
    st.markdown('<div class="sql-label">📋 사용된 SQL</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sql-panel">{sql}</div>', unsafe_allow_html=True)

def insight(html):
    st.markdown(f"""
    <div class="insight">
      <div class="insight-title">💡 Insight</div>
      <p>{html}</p>
    </div>""", unsafe_allow_html=True)

def norm(s):
    mn, mx = s.min(), s.max()
    return pd.Series([50.0]*len(s), index=s.index) if mx == mn else (s-mn)/(mx-mn)*100

# ══════════════════════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🐾 분석 필터")
    all_gu = q("SELECT DISTINCT 자치구 FROM 반려동물등록현황 ORDER BY 자치구")['자치구'].tolist()
    sel_gu = st.multiselect("자치구 선택", all_gu, default=all_gu)
    if not sel_gu:
        sel_gu = all_gu
    gu_in = "'" + "','".join(sel_gu) + "'"

    st.markdown("---")
    st.markdown("**📂 pet.db 테이블**")
    st.caption("• 반려동물등록현황 (429행)\n• 반려동물_동반시설 (11,831행)\n• 공원현황 (133행)")
    st.markdown("---")
    st.caption("데이터 출처: 서울 열린데이터광장\n기준일: 자치구별 상이 (2019–2026)")

# ══════════════════════════════════════════════════════════════════════════════
# 히어로 + KPI
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <p class="hero-title">🐾 서울시 <span>반려동물</span> 생활 환경 분석</p>
  <p class="hero-sub">공원현황 · 반려동물등록현황 · 반려동물_동반시설 — pet.db 3-table JOIN 분석 대시보드</p>
</div>""", unsafe_allow_html=True)

v1 = int(q(f"SELECT SUM(동물등록수) FROM 반려동물등록현황 WHERE 자치구 IN ({gu_in})").iloc[0,0] or 0)
v2 = int(q(f"SELECT SUM(CAST(동물소유자수 AS INTEGER)) FROM 반려동물등록현황 WHERE 자치구 IN ({gu_in})").iloc[0,0] or 0)
v3 = int(q(f"SELECT COUNT(*) FROM 공원현황 WHERE 지역 IN ({gu_in})").iloc[0,0] or 0)
v4 = int(q(f"SELECT COUNT(*) FROM 반려동물_동반시설 WHERE 시군구 IN ({gu_in})").iloc[0,0] or 0)

st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card c1"><div class="kpi-label">총 반려동물 등록수</div>
    <div class="kpi-value">{v1:,}</div><div class="kpi-unit">마리</div></div>
  <div class="kpi-card c2"><div class="kpi-label">반려동물 소유자</div>
    <div class="kpi-value">{v2:,}</div><div class="kpi-unit">명</div></div>
  <div class="kpi-card c3"><div class="kpi-label">반려동물 동반 공원</div>
    <div class="kpi-value">{v3}</div><div class="kpi-unit">개소</div></div>
  <div class="kpi-card c4"><div class="kpi-label">반려동물 동반시설</div>
    <div class="kpi-value">{v4:,}</div><div class="kpi-unit">개소</div></div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 분석 1  공원 환경 밀도 분석
# ══════════════════════════════════════════════════════════════════════════════
section("01", "공원 환경 밀도 분석",
        "반려동물등록현황 × 공원현황 × 반려동물_동반시설 — 3-table LEFT JOIN · 공원 1개당 반려동물 수 + 시설 혼잡도 복합 평가")

SQL1 = """\
WITH pet_sum AS (
    SELECT 자치구,
           SUM(동물등록수)                    AS 총등록수,
           SUM(CAST(동물소유자수 AS INTEGER))  AS 총소유자수
    FROM   반려동물등록현황
    GROUP  BY 자치구
),
park_cnt AS (
    SELECT 지역 AS 자치구, COUNT(*) AS 공원수
    FROM   공원현황
    WHERE  지역 LIKE '%구'
    GROUP  BY 지역
),
fac_cnt AS (
    SELECT 시군구 AS 자치구, COUNT(*) AS 총시설수
    FROM   반려동물_동반시설
    GROUP  BY 시군구
)
SELECT
    p.자치구,
    p.총등록수,
    COALESCE(pk.공원수,   0) AS 공원수,
    COALESCE(f.총시설수,  0) AS 총시설수,
    ROUND(p.총등록수 * 1.0 / NULLIF(pk.공원수,  0), 0) AS 공원당반려동물수,
    ROUND(p.총등록수 * 1.0 / NULLIF(f.총시설수, 0), 1) AS 시설당반려동물수
FROM   pet_sum p
LEFT JOIN park_cnt pk ON p.자치구 = pk.자치구
LEFT JOIN fac_cnt   f ON p.자치구 = f.자치구
ORDER  BY 공원당반려동물수 DESC"""

raw1 = q(SQL1)
df1  = raw1[raw1['자치구'].isin(sel_gu)].copy()
df1['공원당반려동물수'] = pd.to_numeric(df1['공원당반려동물수'], errors='coerce').fillna(0)
df1['시설당반려동물수'] = pd.to_numeric(df1['시설당반려동물수'], errors='coerce').fillna(0)
df1_asc = df1.sort_values('공원당반려동물수', ascending=True)

tab1a, tab1b, tab1c = st.tabs(["📊 시각화", "📋 SQL", "💡 인사이트"])

with tab1a:
    c1l, c1r = st.columns([3, 2])

    with c1l:
        med = df1_asc['공원당반려동물수'].median()
        bar_colors = ['#f7971e' if v > med else '#3fb950' for v in df1_asc['공원당반려동물수']]
        fig = go.Figure(go.Bar(
            y=df1_asc['자치구'], x=df1_asc['공원당반려동물수'], orientation='h',
            marker_color=bar_colors,
            text=df1_asc['공원당반려동물수'].apply(lambda x: f"{int(x):,}"),
            textposition='outside',
            hovertemplate="<b>%{y}</b><br>공원당 반려동물: %{x:,.0f}마리<extra></extra>",
        ))
        fig.add_vline(x=med, line_color=MUT, line_dash="dot",
                      annotation_text=f"중앙값 {int(med):,}",
                      annotation_font_color=MUT, annotation_position="top right")
        fig.update_layout(**BASE,
            title=dict(text="공원 1개당 반려동물 수  (🟠 중앙값 초과 / 🟢 이하)", font=dict(size=13), x=0),
            height=520, xaxis_title="마리 / 공원",
            xaxis=dict(**BASE['xaxis'], tickformat=",",
                       range=[0, df1_asc['공원당반려동물수'].max()*1.2]),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c1r:
        fig2 = go.Figure(go.Scatter(
            x=df1['공원수'], y=df1['총등록수'],
            mode='markers+text', text=df1['자치구'],
            textposition='top center', textfont=dict(size=9, color=TXT),
            marker=dict(
                size=df1['총시설수'] / 15,
                color=df1['시설당반려동물수'],
                colorscale=[[0,'#3fb950'],[.5,'#f7971e'],[1,'#ff7b72']],
                showscale=True,
                colorbar=dict(title="시설당<br>반려동물", tickfont=dict(size=9)),
                sizemin=8,
                line=dict(width=1, color='rgba(255,255,255,0.15)'),
            ),
            hovertemplate="<b>%{text}</b><br>공원수: %{x}개<br>총등록수: %{y:,}마리<extra></extra>",
        ))
        fig2.update_layout(**BASE,
            title=dict(text="공원수 vs 등록수\n(크기=시설수 / 색=시설혼잡도)", font=dict(size=12), x=0),
            height=520, xaxis_title="공원 수 (개)", yaxis_title="총 등록수 (마리)",
            yaxis=dict(**BASE['yaxis'], tickformat=","),
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab1b:
    sql_block(SQL1)

with tab1c:
    worst = df1.sort_values('공원당반려동물수', ascending=False).iloc[0]
    best  = df1.sort_values('공원당반려동물수').iloc[0]
    insight(
        f"<strong>공원 접근성이 가장 열악한 자치구는 {worst['자치구']}</strong>으로 "
        f"공원 {int(worst['공원수'])}개에 <strong>{int(worst['공원당반려동물수']):,}마리/공원</strong>이 몰려 있습니다. "
        f"반면 <strong>{best['자치구']}</strong>은 공원 {int(best['공원수'])}개로 "
        f"<strong>{int(best['공원당반려동물수']):,}마리/공원</strong>의 여유로운 환경입니다. "
        f"버블 차트에서 <em>공원이 많다고 시설 혼잡도가 낮지 않다</em>는 사실이 확인되며, "
        f"단순 공원 수가 아닌 <strong>복합 인프라 지수</strong>로 평가해야 함을 시사합니다."
    )


# ══════════════════════════════════════════════════════════════════════════════
# 분석 2  카테고리별 최적 자치구 분석
# ══════════════════════════════════════════════════════════════════════════════
section("02", "상황별 최적 자치구 분석",
        "반려동물_동반시설 × 반려동물등록현황 — 의료·여가·서비스·카페 카테고리별 만 마리당 시설 밀도 비교")

SQL2 = """\
WITH pet_sum AS (
    SELECT 자치구, SUM(동물등록수) AS 총등록수
    FROM   반려동물등록현황
    GROUP  BY 자치구
),
fac_cat AS (
    SELECT 시군구       AS 자치구,
           카테고리,
           세부카테고리,
           COUNT(*)     AS 시설수
    FROM   반려동물_동반시설
    GROUP  BY 시군구, 카테고리, 세부카테고리
)
SELECT
    f.자치구,
    f.카테고리,
    f.세부카테고리,
    f.시설수,
    p.총등록수,
    ROUND(f.시설수 * 10000.0 / NULLIF(p.총등록수, 0), 2) AS 만마리당시설수
FROM   fac_cat f
JOIN   pet_sum p ON f.자치구 = p.자치구
ORDER  BY f.카테고리, 만마리당시설수 DESC"""

raw2 = q(SQL2)
df2  = raw2[raw2['자치구'].isin(sel_gu)].copy()
df2['만마리당시설수'] = pd.to_numeric(df2['만마리당시설수'], errors='coerce').fillna(0)

CAT_COLOR = {
    '반려의료':'#58a6ff', '반려동물 서비스':'#3fb950',
    '반려동물식당카페':'#f7971e', '반려동반여행':'#bc8cff',
}
CAT_ICON = {
    '반려의료':'🏥', '반려동물 서비스':'✂️',
    '반려동물식당카페':'☕', '반려동반여행':'🎨',
}

tab2a, tab2b, tab2c = st.tabs(["📊 시각화", "📋 SQL", "💡 인사이트"])

with tab2a:
    sel_cat = st.selectbox(
        "카테고리 선택",
        sorted(df2['카테고리'].unique()),
        format_func=lambda x: f"{CAT_ICON.get(x,'')} {x}",
    )
    df2c = df2[df2['카테고리'] == sel_cat].copy()
    c2l, c2r = st.columns([3, 2])

    with c2l:
        pivot = (df2c.pivot_table(
                    index='자치구', columns='세부카테고리',
                    values='만마리당시설수', aggfunc='sum')
                 .fillna(0))
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

        fig_h = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0,'#0d1117'],[.3,'#1c4a2e'],[.7,'#3fb950'],[1,'#ffd200']],
            text=np.round(pivot.values, 1), texttemplate="%{text}", textfont=dict(size=9),
            hovertemplate="<b>%{y}</b> · %{x}<br>만 마리당: %{z:.1f}<extra></extra>",
            showscale=True,
            colorbar=dict(title="만 마리당<br>시설수", tickfont=dict(size=9)),
        ))
        fig_h.update_layout(**BASE,
            title=dict(text=f"{CAT_ICON.get(sel_cat,'')} {sel_cat} — 밀도 히트맵", font=dict(size=13), x=0),
            height=520,
            xaxis=dict(**BASE['xaxis'], tickangle=0),
            yaxis=dict(**BASE['yaxis'], autorange="reversed"),
        )
        st.plotly_chart(fig_h, use_container_width=True)

    with c2r:
        top10 = (df2c.groupby('자치구')['시설수'].sum()
                     .sort_values(ascending=False).head(10).reset_index())
        c = CAT_COLOR.get(sel_cat, '#f7971e')
        fig_t = go.Figure(go.Bar(
            x=top10['자치구'], y=top10['시설수'],
            marker=dict(color=top10['시설수'],
                        colorscale=[[0,'#1c2330'],[1,c]], showscale=False),
            text=top10['시설수'], textposition='outside',
            hovertemplate="<b>%{x}</b><br>시설수: %{y}개<extra></extra>",
        ))
        fig_t.update_layout(**BASE,
            title=dict(text="시설 수 Top 10 자치구", font=dict(size=13), x=0),
            height=520,
            xaxis=dict(**BASE['xaxis'], tickangle=-35),
            yaxis=dict(**BASE['yaxis']), yaxis_title="시설 수 (개)",
        )
        st.plotly_chart(fig_t, use_container_width=True)

    # 레이더 차트
    st.markdown("---")
    st.markdown("#### 🕸 자치구별 4대 카테고리 종합 레이더")
    radar_df = (df2.groupby(['자치구','카테고리'])['만마리당시설수']
                    .sum().reset_index()
                    .pivot(index='자치구', columns='카테고리', values='만마리당시설수')
                    .fillna(0))
    top_choices = radar_df.sum(axis=1).sort_values(ascending=False).head(10).index.tolist()
    sel_radar = st.multiselect("비교 자치구 (최대 5개)", top_choices, default=top_choices[:5])

    cats_r = radar_df.columns.tolist()
    r_cols = ['#f7971e','#58a6ff','#3fb950','#bc8cff','#ff7b72']
    fig_r = go.Figure()
    for i, gu in enumerate(sel_radar[:5]):
        vals = radar_df.loc[gu].values.tolist()
        rc = r_cols[i]
        rv, gv, bv = int(rc[1:3],16), int(rc[3:5],16), int(rc[5:7],16)
        fig_r.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats_r+[cats_r[0]],
            name=gu, fill='toself',
            fillcolor=f"rgba({rv},{gv},{bv},0.12)",
            line=dict(color=rc, width=2),
            hovertemplate="%{theta}: %{r:.1f}<extra>"+gu+"</extra>",
        ))
    fig_r.update_layout(
        polar=dict(
            bgcolor=SRF,
            radialaxis=dict(visible=True, gridcolor=GRID, linecolor=GRID,
                            tickfont=dict(size=9, color=MUT)),
            angularaxis=dict(gridcolor=GRID, linecolor=GRID,
                             tickfont=dict(size=11, color=TXT)),
        ),
        paper_bgcolor=BG, font=dict(family="Noto Sans KR", color=TXT),
        showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=430, margin=dict(l=40,r=40,t=40,b=20),
    )
    st.plotly_chart(fig_r, use_container_width=True)

with tab2b:
    sql_block(SQL2)

with tab2c:
    def best_gu(cat):
        return df2[df2['카테고리']==cat].groupby('자치구')['만마리당시설수'].sum().idxmax()
    insight(
        f"반려동물 <strong>의료 접근성</strong> 최우수 자치구는 <strong>{best_gu('반려의료')}</strong>이며, "
        f"<strong>여가·문화</strong> 인프라는 <strong>{best_gu('반려동반여행')}</strong>이 가장 풍부합니다. "
        f"카페·식당 동반은 <strong>{best_gu('반려동물식당카페')}</strong>, "
        f"미용·위탁 서비스는 <strong>{best_gu('반려동물 서비스')}</strong>가 선도합니다. "
        f"레이더 차트에서 <em>자치구마다 인프라 구성 패턴이 크게 다르다</em>는 점을 확인할 수 있으며, "
        f"반려인의 라이프스타일 우선순위에 따라 <strong>최적 거주지가 달라집니다.</strong>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# 분석 3  종합 반려동물 생활지수
# ══════════════════════════════════════════════════════════════════════════════
section("03", "반려동물 생활지수 — 종합 순위",
        "3개 테이블 통합 · 공원 접근성(30%) + 의료 밀도(35%) + 카테고리 다양성(20%) + 실내시설 비율(15%) 가중 정규화")

SQL3 = """\
WITH pet_sum AS (
    SELECT 자치구, SUM(동물등록수) AS 총등록수
    FROM   반려동물등록현황
    GROUP  BY 자치구
),
park_cnt AS (
    SELECT 지역 AS 자치구, COUNT(*) AS 공원수
    FROM   공원현황
    WHERE  지역 LIKE '%구'
    GROUP  BY 지역
),
fac_agg AS (
    SELECT
        시군구 AS 자치구,
        SUM(CASE WHEN 카테고리 = '반려의료'         THEN 1 ELSE 0 END) AS 의료시설수,
        SUM(CASE WHEN 카테고리 = '반려동반여행'      THEN 1 ELSE 0 END) AS 여가시설수,
        SUM(CASE WHEN 카테고리 = '반려동물식당카페'  THEN 1 ELSE 0 END) AS 카페식당수,
        SUM(CASE WHEN 카테고리 = '반려동물 서비스'   THEN 1 ELSE 0 END) AS 서비스시설수,
        SUM(CASE WHEN 실내여부 = 'TRUE' THEN 1 ELSE 0 END)
            * 100.0 / NULLIF(COUNT(*), 0)              AS 실내시설비율,
        COUNT(DISTINCT 세부카테고리)                    AS 카테고리다양성
    FROM   반려동물_동반시설
    GROUP  BY 시군구
)
SELECT
    p.자치구,
    p.총등록수,
    COALESCE(pk.공원수, 0)                                                    AS 공원수,
    COALESCE(fa.의료시설수, 0)                                                 AS 의료시설수,
    ROUND(COALESCE(fa.실내시설비율,    0), 1)                                  AS 실내시설비율,
    COALESCE(fa.카테고리다양성,        0)                                       AS 카테고리다양성,
    ROUND(COALESCE(fa.의료시설수,0) * 10000.0 / NULLIF(p.총등록수, 0), 2)     AS 만마리당의료수,
    ROUND(COALESCE(pk.공원수,   0) * 10000.0 / NULLIF(p.총등록수, 0), 4)     AS 만마리당공원수
FROM   pet_sum p
LEFT JOIN park_cnt pk ON p.자치구 = pk.자치구
LEFT JOIN fac_agg  fa ON p.자치구 = fa.자치구
ORDER  BY p.총등록수 DESC"""

raw3 = q(SQL3)
df3  = raw3[raw3['자치구'].isin(sel_gu)].copy()
for col in ['만마리당공원수','만마리당의료수','카테고리다양성','실내시설비율','총등록수']:
    df3[col] = pd.to_numeric(df3[col], errors='coerce').fillna(0)

df3['s_공원']   = norm(df3['만마리당공원수'])
df3['s_의료']   = norm(df3['만마리당의료수'])
df3['s_다양성'] = norm(df3['카테고리다양성'])
df3['s_실내']   = norm(df3['실내시설비율'])
df3['종합점수'] = (df3['s_공원']*0.30 + df3['s_의료']*0.35 +
                   df3['s_다양성']*0.20 + df3['s_실내']*0.15).round(1)
df3 = df3.sort_values('종합점수', ascending=False).reset_index(drop=True)
df3['순위'] = df3.index + 1

tab3a, tab3b, tab3c = st.tabs(["📊 시각화", "📋 SQL", "💡 인사이트"])

with tab3a:
    c3l, c3r = st.columns([2, 3])

    with c3l:
        medals = {1:"🥇", 2:"🥈", 3:"🥉"}
        rows = ""
        for _, row in df3.iterrows():
            rk = int(row['순위']); sc = row['종합점수']
            bc = "#3fb950" if sc >= 65 else ("#f7971e" if sc >= 40 else "#ff7b72")
            rows += f"""
            <div class="rank-row">
              <div class="rank-medal">{medals.get(rk, f'#{rk}')}</div>
              <div class="rank-name">{row['자치구']}</div>
              <div class="rank-score">
                <div class="val">{sc:.1f}점</div>
                <div class="score-bar" style="background:{bc};width:{int(sc)}%"></div>
              </div>
            </div>"""
        st.markdown(f'<div class="rank-wrap">{rows}</div>', unsafe_allow_html=True)

    with c3r:
        df3p = df3.sort_values('종합점수', ascending=True)
        score_items = [
            ('s_공원',   '공원 접근성 (30%)',     '#3fb950'),
            ('s_의료',   '의료 밀도 (35%)',       '#58a6ff'),
            ('s_다양성', '카테고리 다양성 (20%)',  '#f7971e'),
            ('s_실내',   '실내시설 비율 (15%)',    '#bc8cff'),
        ]
        weights = [0.30, 0.35, 0.20, 0.15]
        fig_s = go.Figure()
        for (col, label, color), w in zip(score_items, weights):
            fig_s.add_trace(go.Bar(
                y=df3p['자치구'], x=df3p[col]*w,
                name=label, orientation='h', marker_color=color,
                hovertemplate=f"<b>%{{y}}</b><br>{label}: %{{x:.1f}}점<extra></extra>",
            ))
        fig_s.update_layout(**BASE,
            title=dict(text="항목별 점수 기여도 (가중 합산)", font=dict(size=13), x=0),
            barmode='stack', height=560, xaxis_title="가중 점수 합계",
            xaxis=dict(**BASE['xaxis']), yaxis=dict(**BASE['yaxis']),
            legend=dict(orientation='h', y=1.05, x=0,
                        bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
        )
        st.plotly_chart(fig_s, use_container_width=True)

    # 산포도 + 사분면
    st.markdown("---")
    st.markdown("#### 📈 종합점수 vs 반려동물 등록수 — 사분면 분석")
    med_x = df3['총등록수'].median()
    med_y = df3['종합점수'].median()

    fig_sc = go.Figure(go.Scatter(
        x=df3['총등록수'], y=df3['종합점수'],
        mode='markers+text', text=df3['자치구'],
        textposition='top center', textfont=dict(size=9, color=TXT),
        marker=dict(
            size=14, color=df3['종합점수'],
            colorscale=[[0,'#ff7b72'],[.5,'#f7971e'],[1,'#3fb950']],
            showscale=True,
            colorbar=dict(title="종합점수", tickfont=dict(size=9)),
            line=dict(width=1, color='rgba(255,255,255,0.15)'),
        ),
        hovertemplate="<b>%{text}</b><br>등록수: %{x:,}마리<br>종합점수: %{y:.1f}점<extra></extra>",
    ))
    fig_sc.add_hline(y=med_y, line_color=GRID, line_dash="dot")
    fig_sc.add_vline(x=med_x, line_color=GRID, line_dash="dot")
    for txt, ax, ay, ac in [
        ("🟢 인프라 우수·등록 적음",  med_x*.35, med_y*1.06+5,  "#3fb950"),
        ("🔵 인프라 우수·등록 많음",  med_x*1.3, med_y*1.06+5,  "#58a6ff"),
        ("⚪ 인프라 부족·등록 적음",  med_x*.35, med_y*.6,      MUT),
        ("🔴 인프라 부족·등록 많음",  med_x*1.3, med_y*.6,      "#ff7b72"),
    ]:
        fig_sc.add_annotation(x=ax, y=ay, text=txt, showarrow=False,
                               font=dict(size=9, color=ac))
    fig_sc.update_layout(**BASE,
        height=400, xaxis_title="총 등록수 (마리)", yaxis_title="종합 생활 점수",
        xaxis=dict(**BASE['xaxis'], tickformat=","),
        yaxis=dict(**BASE['yaxis']),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

with tab3b:
    sql_block(SQL3)

with tab3c:
    t1 = df3.iloc[0]; t2 = df3.iloc[1]; tl = df3.iloc[-1]
    insight(
        f"공원 접근성·의료 밀도·다양성·실내시설 비율을 가중 정규화한 결과, "
        f"<strong>{t1['자치구']}({t1['종합점수']}점)</strong>이 반려동물 생활 환경 종합 1위를 기록했습니다. "
        f"<strong>{t2['자치구']}({t2['종합점수']}점)</strong>이 근소한 차이로 2위이며, "
        f"<strong>{tl['자치구']}({tl['종합점수']}점)</strong>은 공원 밀도와 의료 인프라 모두 열위로 개선이 시급합니다. "
        f"사분면 분석의 <em>🔵 인프라 우수·등록 많음</em> 구간이 반려동물 가구에게 "
        f"<strong>실질적으로 가장 유리한 자치구</strong>임을 확인할 수 있습니다."
    )

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#7d8590;font-size:.8rem;padding:1rem 0;">
    🐾 서울시 반려동물 생활 환경 분석 대시보드 &nbsp;|&nbsp;
    DB: pet.db (반려동물등록현황 · 반려동물_동반시설 · 공원현황) &nbsp;|&nbsp;
    3-table JOIN 분석
</div>""", unsafe_allow_html=True)
