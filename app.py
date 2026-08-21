import base64
import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import altair as alt


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.append(str(SRC_DIR))


from home import (
    get_frequent_tasks,
    get_recommended_questions,
    get_department_info,
    get_regulation_pdfs,
)

from chatbot import (
    initialize_rag,
    generate_answer,
)

from analysis import (
    load_golden_set,
    embed_questions,
    build_embedding_analysis_from_embeddings,
    get_cluster_summary,
    load_experiment_summary,
)


# =========================================================
# Streamlit 기본 설정
# =========================================================

st.set_page_config(
    page_title="LX AI 규정 도우미",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 경로
# app.py가 프로젝트 루트에 있으므로 parent 한 번만 사용
# =========================================================

ASSET_DIR = PROJECT_ROOT / "src" / "assets"

GOLDEN_SET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "golden_set.csv"
)

EXPERIMENT_SUMMARY_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "results"
    / "experiment_summary.csv"
)

# =========================================================
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "page" not in st.session_state:
    st.session_state.page = "🏠 홈"

if "next_page" not in st.session_state:
    st.session_state.next_page = None

# =========================================================
# RAG Cache
# =========================================================

@st.cache_resource
def get_cached_rag():
    return initialize_rag()


# =========================================================
# 분석 Cache
# =========================================================

@st.cache_data(show_spinner=False)
def get_cached_golden_set(path_str):
    return load_golden_set(
        Path(path_str)
    )


@st.cache_data(show_spinner=False)
def get_cached_embeddings(df):
    return embed_questions(df)


@st.cache_data(show_spinner=False)
def get_cached_embedding_analysis(
    df,
    embeddings,
    n_clusters,
    n_neighbors,
    min_dist,
):
    return build_embedding_analysis_from_embeddings(
        df=df,
        embeddings=embeddings,
        n_clusters=n_clusters,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
    )


@st.cache_data(show_spinner=False)
def get_cached_experiment_summary(path_str):
    return load_experiment_summary(
        Path(path_str)
    )


# =========================================================
# 홈 → 챗봇 이동 함수
# =========================================================

def move_to_chatbot(question):

    st.session_state.pending_question = question
    st.session_state.next_page = "💬 규정 챗봇"

    st.rerun()

if st.session_state.next_page is not None:

    st.session_state.page = (
        st.session_state.next_page
    )

    st.session_state.next_page = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root { --green:#168b54; --dark:#15221f; --line:#dfe7e4; --soft:#f4f8f6; }
html, body, [class*="css"] { font-family:'Noto Sans KR', sans-serif; }
.stApp { background:#f6f8f7; color:var(--dark); }
[data-testid="stSidebar"] { background:#f8fbfa; border-right:1px solid #e4ece9; }
[data-testid="stSidebar"] section { padding:2rem 1rem; }
.brand { text-align:center; padding:.3rem 0 1.8rem; }
.brand-mark { color:var(--green); font-size:3.5rem; font-weight:800; letter-spacing:-.12em; line-height:1; }
.brand-name { font-weight:800; font-size:1rem; margin-top:.7rem; }
.brand-sub { color:var(--green); font-weight:700; margin-top:.25rem; }
.hero { position:relative; padding:1.2rem 0 .5rem; min-height:190px; overflow:hidden; }
.hero h1 { font-size:2rem; line-height:1.35; letter-spacing:-.06em; margin:1rem 0 .9rem; color:#111; }
.hero h1 span { color:var(--green); }
.hero p { color:#6b7774; margin:0; }
.hero-mascot { position:absolute; right:2%; bottom:-10px; width:225px; max-height:205px; object-fit:contain; }
.search-wrap { background:white; border:1px solid #d8e1dd; border-radius:14px; padding:.25rem; box-shadow:0 4px 18px rgba(17,48,39,.06); }
.section-title { font-size:1.25rem; font-weight:800; letter-spacing:-.04em; margin:.25rem 0 .85rem; }
.section-title span { color:var(--green); }
.card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.2rem 1.3rem; box-shadow:0 5px 18px rgba(17,48,39,.05); height:100%; }
.card h3 { margin:0 0 .7rem; font-size:1.15rem; letter-spacing:-.04em; }
.card-desc { color:#68736f; font-size:.9rem; margin-bottom:.8rem; }
.pdf-card { min-height:112px; display:flex; flex-direction:column; justify-content:space-between; }
.pdf-icon { font-size:1.65rem; }
.pdf-name { font-weight:700; font-size:.92rem; line-height:1.35; }
.rank-row { display:flex; align-items:center; gap:.7rem; padding:.65rem 0; border-bottom:1px solid #edf1ef; font-size:.9rem; }
.rank-row:last-child { border-bottom:0; }
.rank { width:25px; height:25px; display:grid; place-items:center; border-radius:50%; background:#e7f4ed; color:var(--green); font-weight:800; }
.recent-row { padding:.55rem 0; border-bottom:1px solid #edf1ef; font-size:.9rem; }
.recent-row:last-child { border-bottom:0; }
@media (max-width: 900px) { .hero-mascot { opacity:.35; right:-35px; } .hero h1 { font-size:1.65rem; } }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">LX</div><div class="brand-name">한국국토정보공사</div><div class="brand-sub">AI 규정 대시보드</div></div>', unsafe_allow_html=True)
    page = st.radio("메뉴", ["🏠 홈", "💬 규정 챗봇", "📊 데이터 분석"], key="page", label_visibility="collapsed")
    st.divider()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()


# =========================================================
# PAGE 1
# HOME
# =========================================================

if page == "🏠 홈":
    mascot_path = ASSET_DIR / "Welcome 랜디.png"
    mascot_src = ""
    if mascot_path.exists():
        mascot_src = "data:image/png;base64," + base64.b64encode(mascot_path.read_bytes()).decode("ascii")
    st.markdown(f'<div class="hero"><h1>안녕하세요! 오늘도 <span>규정 검색</span>을 도와드릴게요.</h1><p>필요한 규정 원문을 빠르고 정확하게 찾아보세요.</p><img class="hero-mascot" src="{mascot_src}"></div>', unsafe_allow_html=True)
    search_col, button_col = st.columns([5, 1], vertical_alignment="bottom")
    with search_col:
        search_query = st.text_input("규정 검색", placeholder="규정이나 업무를 검색해보세요", label_visibility="collapsed")
    with button_col:
        search_clicked = st.button("검색", use_container_width=True, type="primary")
    if search_clicked and search_query.strip():
        move_to_chatbot(search_query.strip())
    popular_keyword = st.pills("인기 검색어", ["연차", "출장비", "초과근무수당", "승진", "휴직"], label_visibility="collapsed")
    if popular_keyword:
        move_to_chatbot(f"{popular_keyword} 관련 규정을 알려줘")

    st.markdown('<div class="section-title">🚀 <span>규정 원문</span> 바로가기</div>', unsafe_allow_html=True)
    try:
        tasks = get_frequent_tasks()
    except Exception:
        tasks = []
    if tasks:
        task_cols = st.columns(4)
        for index, task in enumerate(tasks):
            with task_cols[index % 4]:
                st.markdown(f'<div class="card pdf-card"><div class="pdf-icon">{task["icon"]}</div><div class="pdf-name">{task["label"]}</div></div>', unsafe_allow_html=True)
                pdf_path = task["path"]
                if pdf_path.exists():
                    st.download_button("PDF 원문 다운로드", data=pdf_path.read_bytes(), file_name=pdf_path.name, mime="application/pdf", key=f"pdf_{index}", use_container_width=True)


    # =====================================================
    # 추천 질문 / 담당 부서
    # =====================================================

    left_col, right_col = st.columns(2)


    # =====================================================
    # 추천 질문
    # =====================================================

    with left_col:
        with st.container(border=True):

            st.subheader(
                "💡 추천 질문"
            )

            try:

                questions = (
                    get_recommended_questions()
                )

            except Exception as e:

                st.error(
                    "추천 질문을 불러오지 못했습니다."
                )

                st.exception(e)

                questions = []


            for index, question in enumerate(
                questions
            ):

                if st.button(
                    question,
                    key=f"recommended_{index}",
                    use_container_width=True,
                ):

                    move_to_chatbot(
                        question
                    )


    # =====================================================
    # 담당 부서
    # =====================================================

    with right_col:

        with st.container(
            border=True
        ):

            st.subheader(
                "☎️ 담당 부서 안내"
            )

            try:

                departments = (
                    get_department_info()
                )

                department_df = (
                    pd.DataFrame(
                        departments
                    )
                )

                st.dataframe(
                    department_df,
                    hide_index=True,
                    use_container_width=True,
                )

            except Exception as e:

                st.error(
                    "담당 부서 정보를 불러오지 못했습니다."
                )

                st.exception(e)


    # =====================================================
    # 최근 질문
    # =====================================================

    st.subheader(
        "🕒 나의 최근 질문"
    )

    user_messages = [
        message["content"]
        for message
        in st.session_state.messages
        if message["role"] == "user"
    ]

    if user_messages:

        recent_questions = (
            user_messages[-5:][::-1]
        )

        for index, recent_question in enumerate(
            recent_questions
        ):

            if st.button(
                recent_question,
                key=f"recent_{index}",
            ):

                move_to_chatbot(
                    recent_question
                )

    else:

        st.info(
            "아직 질문 기록이 없습니다."
        )


# =========================================================
# PAGE 2
# CHATBOT
# =========================================================

elif page == "💬 규정 챗봇":

    st.title(
        "💬 사내 규정 AI 챗봇"
    )

    st.caption(
        "사내 규정을 기반으로 답변합니다."
    )


    # =====================================================
    # RAG 초기화
    # =====================================================

    try:

        (
            vector_store,
            retriever,
            chain,
        ) = get_cached_rag()

    except Exception as e:

        st.error(
            "RAG 시스템을 초기화하지 못했습니다."
        )

        st.exception(e)

        st.stop()


    # =====================================================
    # 이전 대화 출력
    # =====================================================

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

            if (
                message["role"] == "assistant"
                and message.get("sources")
            ):

                with st.expander(
                    "📚 참고한 규정"
                ):

                    for source in message[
                        "sources"
                    ]:

                        st.write(
                            source
                        )


    # =====================================================
    # 질문 입력
    # =====================================================

    typed_question = st.chat_input(
        "사내 규정에 대해 질문하세요."
    )


    # 홈에서 넘어온 질문
    pending_question = (
        st.session_state.pending_question
    )


    if pending_question:

        question = pending_question

        st.session_state.pending_question = None

    else:

        question = typed_question


    # =====================================================
    # 질문 처리
    # =====================================================

    if question:

        previous_messages = (
            st.session_state.messages.copy()
        )


        # =================================================
        # 사용자 메시지 저장
        # =================================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )


        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )


        # =================================================
        # RAG 답변
        # =================================================

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "관련 규정을 확인하고 있습니다..."
            ):

                try:

                    result = generate_answer(
                        question=question,
                        messages=previous_messages,
                        vector_store=vector_store,
                        retriever=retriever,
                        chain=chain,
                    )

                    answer = result.get(
                        "answer",
                        "답변을 생성하지 못했습니다.",
                    )

                    sources = result.get(
                        "sources",
                        [],
                    )

                    st.markdown(
                        answer
                    )

                    if sources:

                        with st.expander(
                            "📚 참고한 규정"
                        ):

                            for source in sources:

                                st.write(
                                    source
                                )


                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                        }
                    )


                except Exception as e:

                    st.error(
                        "답변 생성 중 오류가 발생했습니다."
                    )

                    st.exception(e)


# =========================================================
# PAGE 3
# ANALYSIS
# =========================================================

elif page == "📊 데이터 분석":

    st.title(
        "📊 RAG 데이터 분석"
    )

    st.caption(
        "골든셋 질문 임베딩과 "
        "모델·Retriever 실험 결과를 분석합니다."
    )


    tab1, tab2 = st.tabs(
        [
            "🧠 질문 임베딩 분석",
            "⚡ 실험 성능 비교",
        ]
    )


    # =====================================================
    # TAB 1
    # UMAP + K-Means
    # =====================================================

    with tab1:

        st.subheader(
            "🧠 골든셋 질문 임베딩"
        )


        if not GOLDEN_SET_PATH.exists():

            st.error(
                f"골든셋 파일이 없습니다: "
                f"{GOLDEN_SET_PATH}"
            )

            st.stop()


        try:

            df = get_cached_golden_set(
                str(GOLDEN_SET_PATH)
            )

            embeddings = (
                get_cached_embeddings(
                    df
                )
            )

        except Exception as e:

            st.error(
                "골든셋 또는 질문 임베딩을 "
                "불러오는 중 오류가 발생했습니다."
            )

            st.exception(e)

            st.stop()


        # =================================================
        # UMAP 설정
        # =================================================

        max_neighbors = max(
            2,
            min(
                30,
                len(df) - 1,
            ),
        )


        control1, control2, control3 = (
            st.columns(3)
        )


        with control1:

            cluster_count = st.slider(
                "Cluster 수",
                min_value=2,
                max_value=min(
                    10,
                    len(df),
                ),
                value=min(
                    5,
                    len(df),
                ),
            )


        with control2:

            n_neighbors = st.slider(
                "UMAP n_neighbors",
                min_value=2,
                max_value=max_neighbors,
                value=min(
                    15,
                    max_neighbors,
                ),
            )


        with control3:

            min_dist = st.slider(
                "UMAP min_dist",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.05,
            )


        try:

            analysis_df = (
                get_cached_embedding_analysis(
                    df=df,
                    embeddings=embeddings,
                    n_clusters=cluster_count,
                    n_neighbors=n_neighbors,
                    min_dist=min_dist,
                )
            )

            cluster_summary = (
                get_cluster_summary(
                    analysis_df
                )
            )

        except Exception as e:

            st.error(
                "UMAP/K-Means 분석 중 오류가 발생했습니다."
            )

            st.exception(e)

            st.stop()


        # =================================================
        # KPI
        # =================================================

        metric1, metric2, metric3 = (
            st.columns(3)
        )


        with metric1:

            st.metric(
                "총 질문 수",
                len(analysis_df),
            )


        with metric2:

            st.metric(
                "Cluster 수",
                cluster_count,
            )


        with metric3:

            largest_cluster = (
                cluster_summary[
                    "question_count"
                ].max()
            )

            st.metric(
                "최대 Cluster 질문 수",
                int(largest_cluster),
            )


        # =================================================
        # UMAP Scatter
        # =================================================

        st.subheader(
            "질문 의미 분포"
        )


        tooltip_columns = [
            alt.Tooltip(
                "query:N",
                title="질문",
            ),
            alt.Tooltip(
                "cluster:N",
                title="Cluster",
            ),
        ]


        if "query_id" in analysis_df.columns:

            tooltip_columns.insert(
                0,
                alt.Tooltip(
                    "query_id:N",
                    title="Query ID",
                ),
            )


        scatter_chart = (
            alt.Chart(
                analysis_df
            )
            .mark_circle(
                size=100
            )
            .encode(
                x=alt.X(
                    "x:Q",
                    title="UMAP 1",
                ),
                y=alt.Y(
                    "y:Q",
                    title="UMAP 2",
                ),
                color=alt.Color(
                    "cluster:N",
                    title="Cluster",
                ),
                tooltip=tooltip_columns,
            )
            .interactive()
        )


        st.altair_chart(
            scatter_chart,
            use_container_width=True,
        )


        # =================================================
        # Cluster 통계
        # =================================================

        st.subheader(
            "Cluster별 질문 분포"
        )


        st.bar_chart(
            cluster_summary,
            x="cluster",
            y="question_count",
        )


        st.dataframe(
            cluster_summary,
            hide_index=True,
            use_container_width=True,
        )


        # =================================================
        # Cluster 질문 확인
        # =================================================

        st.subheader(
            "Cluster별 실제 질문"
        )


        selected_cluster = st.selectbox(
            "Cluster 선택",
            sorted(
                analysis_df[
                    "cluster"
                ].unique()
            ),
        )


        cluster_questions = (
            analysis_df[
                analysis_df["cluster"]
                == selected_cluster
            ]
        )


        show_columns = [
            col
            for col in [
                "query_id",
                "query",
                "gold_chunks",
                "cluster",
            ]
            if col in cluster_questions.columns
        ]


        st.dataframe(
            cluster_questions[
                show_columns
            ],
            hide_index=True,
            use_container_width=True,
        )


    # =====================================================
    # TAB 2
    # 실험 성능 비교
    # =====================================================

    with tab2:

        st.subheader(
            "⚡ 모델 / Top-K 성능 비교"
        )


        if not EXPERIMENT_SUMMARY_PATH.exists():

            st.error(
                "experiment_summary.csv 파일이 없습니다."
            )

            st.stop()


        try:

            comparison_df = (
                get_cached_experiment_summary(
                    str(
                        EXPERIMENT_SUMMARY_PATH
                    )
                )
            )

        except Exception as e:

            st.error(
                "실험 결과를 불러오지 못했습니다."
            )

            st.exception(e)

            st.stop()


        # =================================================
        # 표시용 이름
        # =================================================

        chart_df = (
            comparison_df.copy()
        )

        chart_df["experiment"] = (
            chart_df["model"]
            + " / k="
            + chart_df["k"].astype(str)
        )


        # =================================================
        # 표
        # =================================================

        st.dataframe(
            comparison_df,
            hide_index=True,
            use_container_width=True,
        )


        # =================================================
        # 평균 검색 시간
        # =================================================

        st.subheader(
            "🔍 평균 검색 시간"
        )

        st.bar_chart(
            chart_df,
            x="experiment",
            y="avg_search_time",
        )


        # =================================================
        # 평균 답변 생성 시간
        # =================================================

        st.subheader(
            "🤖 평균 답변 생성 시간"
        )

        st.bar_chart(
            chart_df,
            x="experiment",
            y="avg_generation_time",
        )


        # =================================================
        # 평균 전체 응답 시간
        # =================================================

        st.subheader(
            "⏱️ 평균 전체 응답 시간"
        )

        st.bar_chart(
            chart_df,
            x="experiment",
            y="avg_total_time",
        )


        # =================================================
        # 최종 설정 안내
        # =================================================

        st.info(
            "현재 서비스 Retriever 설정: Top-K = 10"
        )
