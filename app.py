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


from chat_ui import (
    inject_chatbot_css,
    render_chat_welcome,
    render_example_questions,
    render_user_message,
    render_randy_message,
    render_randy_error,
)

from ingest import get_embeddings

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

@st.cache_resource
def get_cached_embedding_model():
    return get_embeddings()

@st.cache_resource
def get_cached_rag():
    embeddings = get_cached_embedding_model()
    return initialize_rag(embeddings=embeddings)

@st.cache_data(show_spinner=False)
def get_cached_embeddings(path_str, _embedding_model):
    df = get_cached_golden_set(path_str)
    return embed_questions(df, _embedding_model)

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
[data-testid="stSidebar"] { min-width:16vw; max-width:16vw; }
[data-testid="stSidebar"] section { padding:2rem 1rem; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none; }
[data-testid="stSidebar"] [role="radiogroup"] label { border-radius:10px; padding:.65rem .75rem; margin:.2rem 0; color:#25352e; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#168b54; color:#fff; }
.brand { text-align:center; padding:.3rem 0 1.8rem; }
.brand-mark { color:var(--green); font-size:3.5rem; font-weight:800; letter-spacing:-.12em; line-height:1; }
.brand-name { font-weight:800; font-size:1rem; margin-top:.7rem; }
.brand-sub { color:var(--green); font-weight:700; margin-top:.25rem; }
.hero { position:relative; padding:1.2rem 0 .5rem; min-height:190px; overflow:hidden; }
.hero h1 { font-size:2rem; line-height:1.35; letter-spacing:-.06em; margin:1rem 0 .9rem; color:#111; }
.hero h1 span { color:var(--green); }
.hero p { color:#6b7774; margin:0; }
.hero-mascot { position:absolute; right:2%; bottom:-10px; width:225px; max-height:205px; object-fit:contain; }
.speech { position:absolute; right:18%; top:1rem; z-index:1; padding:.75rem 1.1rem; border:2px solid var(--green); border-radius:20px; background:#fff; color:#111; font-weight:700; text-align:center; line-height:1.35; box-shadow:0 3px 8px rgba(17,48,39,.04); }
.speech:after { content:""; position:absolute; right:18px; bottom:-12px; width:18px; height:18px; background:#fff; border-right:2px solid var(--green); border-bottom:2px solid var(--green); transform:rotate(35deg); }
.search-wrap { background:white; border:1px solid #d8e1dd; border-radius:14px; padding:.25rem; box-shadow:0 4px 18px rgba(17,48,39,.06); }
.section-title { font-size:1.25rem; font-weight:800; letter-spacing:-.04em; margin:.25rem 0 .85rem; }
.section-title span { color:var(--green); }
.card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.2rem 1.3rem; box-shadow:0 5px 18px rgba(17,48,39,.05); height:100%; }
.card h3 { margin:0 0 .7rem; font-size:1.15rem; letter-spacing:-.04em; }
.card-desc { color:#68736f; font-size:.9rem; margin-bottom:.8rem; }
.pdf-icon { font-size:1.65rem; }
.pdf-name { font-weight:700; font-size:.92rem; line-height:1.35; }
.rank-row { display:flex; align-items:center; gap:.7rem; padding:.65rem 0; border-bottom:1px solid #edf1ef; font-size:.9rem; }
.rank-row:last-child { border-bottom:0; }
.rank { width:25px; height:25px; display:grid; place-items:center; border-radius:50%; background:#e7f4ed; color:var(--green); font-weight:800; }
.recent-row { padding:.55rem 0; border-bottom:1px solid #edf1ef; font-size:.9rem; }
.recent-row:last-child { border-bottom:0; }
.department-table { width:100%; border-collapse:collapse; font-size:.78rem; color:#24312c; }
.department-table th { background:#edf3f0; font-weight:700; text-align:left; padding:.45rem .5rem; border-bottom:1px solid #dfe8e3; }
.department-table td { padding:.45rem .5rem; border-bottom:1px solid #edf1ef; vertical-align:top; }
.department-table tr:last-child td { border-bottom:0; }
.stButton > button { border-radius:12px; border:1px solid #e1e8e5; background:#fff; color:#16231e; min-height:46px; }
.stButton > button:hover { border-color:#168b54; color:#0b6b3a; }
@media (max-width: 900px) { .hero-mascot { opacity:.35; right:-35px; } .hero h1 { font-size:1.65rem; } }
@media (max-width: 900px) { [data-testid="stSidebar"] { min-width:0; max-width:none; } .speech { right:25%; transform:scale(.82); transform-origin:top right; } }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">LX</div><div class="brand-name">한국국토정보공사</div><div class="brand-sub">LXpert</div></div>', unsafe_allow_html=True)
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
    st.markdown(f'<div class="hero"><h1>안녕하세요! 오늘도 <span>규정 검색</span>을 도와드릴게요.</h1><p>궁금한 규정이나 업무를 빠르게 찾아보세요.</p><div class="speech">궁금한 규정이나<br>업무를 검색해보세요!</div><img class="hero-mascot" src="{mascot_src}"></div>', unsafe_allow_html=True)
    search_col, button_col = st.columns([5, 1], vertical_alignment="bottom")
    with search_col:
        search_query = st.text_input("규정 검색", placeholder="규정이나 업무를 검색하세요", label_visibility="collapsed")
    with button_col:
        search_clicked = st.button("검색", use_container_width=True, type="primary")
    if search_clicked and search_query.strip():
        move_to_chatbot(search_query.strip())
    popular_keyword = st.pills("빠른 검색", ["연차", "출장비", "초과근무수당", "승진", "휴직"], label_visibility="collapsed")
    if popular_keyword:
        move_to_chatbot(f"{popular_keyword} 관련 규정을 알려줘")

    try:
        tasks = get_frequent_tasks()
    except Exception:
        tasks = []
    upper_left, upper_right = st.columns(2, gap="medium")
    lower_left, lower_right = st.columns(2, gap="medium")

    with upper_left:
        with st.container(border=True):
            st.markdown("### 🚀 자주 찾는 업무")
            st.caption("필요한 업무를 빠르게 확인해보세요.")
            task_cols = st.columns(3, gap="small")
            for index, task in enumerate(tasks[:6]):
                with task_cols[index % 3]:
                    if st.button(f'{task["icon"]}  {task["label"]}', key=f"task_{index}", use_container_width=True):
                        move_to_chatbot(task["question"])

    with upper_right:
        with st.container(border=True):
            st.markdown("### 💡 추천 질문")
            st.caption("자주 확인하는 규정을 빠르게 찾아보세요.")
            try:
                questions = get_recommended_questions()
            except Exception:
                questions = []
            for index, question in enumerate(questions[:5]):
                q_col, b_col = st.columns([1, 12], vertical_alignment="center")
                with q_col:
                    st.markdown(f'<div class="rank">{index + 1}</div>', unsafe_allow_html=True)
                with b_col:
                    if st.button(question, key=f"recommended_{index}", use_container_width=True):
                        move_to_chatbot(question)

    with lower_left:
        with st.container(border=True):
            st.markdown("### 🕘 나의 최근 질문")
            user_messages = [message["content"] for message in st.session_state.messages if message["role"] == "user"]
            if user_messages:
                for index, recent_question in enumerate(user_messages[-5:][::-1]):
                    if st.button(f"•  {recent_question}", key=f"recent_{index}", use_container_width=True):
                        move_to_chatbot(recent_question)
            else:
                st.info("아직 질문 기록이 없습니다.")

    with lower_right:
        with st.container(border=True):
            st.markdown("### ☎ 담당 부서 안내")
            st.caption("규정만으로 해결되지 않는 경우, 담당 부서에 문의해 주세요.")
            try:
                departments = get_department_info()
                headers = ["업무 분야", "지사/부서", "연락처"]
                rows = "".join(
                    "<tr>" + "".join(f"<td>{item.get(header, '')}</td>" for header in headers) + "</tr>"
                    for item in departments
                )
                table = "<table class='department-table'><thead><tr>" + "".join(f"<th>{header}</th>" for header in headers) + f"</tr></thead><tbody>{rows}</tbody></table>"
                st.markdown(table, unsafe_allow_html=True)
            except Exception:
                st.info("담당 부서 정보가 없습니다.")


# =========================================================
# PAGE 2
# CHATBOT
# =========================================================

elif page == "💬 규정 챗봇":
    inject_chatbot_css()
    st.markdown(
        '<h1 class="chatbot-page-title">💬 사내 문서 챗봇</h1>',
        unsafe_allow_html=True,
    )
    try:
        vector_store, retriever, chain = get_cached_rag()
    except Exception as e:
        render_randy_error("랜디가 규정 검색을 준비하지 못했어요.\n\n잠시 후 다시 시도해 주세요.", e)
        st.stop()

    typed_question = st.chat_input("예: 시간단위 연차 사용 기준은 어떻게 되나요?", key="chatbot_question_input")
    pending_question = st.session_state.pending_question
    if pending_question:
        question = pending_question
        st.session_state.pending_question = None
    else:
        question = typed_question

    if not st.session_state.messages and not question:
        render_chat_welcome()
        render_example_questions()

    for message in st.session_state.messages:
        if message["role"] == "assistant":
            render_randy_message(message["content"], message.get("sources"), ASSET_DIR)
        else:
            render_user_message(message["content"])

    if question:
        previous_messages = st.session_state.messages.copy()
        st.session_state.messages.append(
            {"role": "user", "content": question}
        )
        render_user_message(question)
        with st.spinner("관련 규정을 확인하고 있습니다..."):
            try:
                result = generate_answer(
                    question=question,
                    messages=previous_messages,
                    vector_store=vector_store,
                    retriever=retriever,
                    chain=chain,
                )
                answer = result.get("answer")
                sources = result.get("sources", [])
                if not answer or not str(answer).strip():
                    raise ValueError("응답에 answer가 없습니다.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
                st.rerun()
            except Exception as e:
                render_randy_error(error=e, asset_dir=ASSET_DIR)

    if st.session_state.messages and st.session_state.messages[-1].get("role") == "assistant" and not question:
        follow_col1, follow_col2 = st.columns(2)
        for follow_col, followup in zip((follow_col1, follow_col2), ("연차 신청 절차도 알려줘", "휴가 종류를 비교해줘")):
            with follow_col:
                if st.button(followup, key=f"followup_{len(st.session_state.messages)}_{followup}", use_container_width=True):
                    st.session_state.pending_question = followup
                    st.rerun()


# =========================================================
# PAGE 3
# ANALYSIS
# =========================================================

elif page == "📊 데이터 분석":

    # 이 페이지에 들어올 때만 무거운 라이브러리 로드
    from analysis import (
        load_golden_set,
        embed_questions,
        build_embedding_analysis_from_embeddings,
        get_cluster_summary,
        load_experiment_summary,
        add_cluster_topics,
    )
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

        title_col, image_col = st.columns([5, 1], vertical_alignment="center")
        with title_col:
            st.subheader("✨ 골든셋 질문 임베딩")
        with image_col:
            topic_mascot = ASSET_DIR / "아이디어 랜디.png"
            if topic_mascot.exists():
                st.image(topic_mascot, width=85)


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
        # 분석 파라미터는 서비스 화면에서 고정한다.
        # =================================================

        cluster_count = 5
        n_neighbors = 5
        min_dist = 0.1


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
            analysis_df, cluster_topics = add_cluster_topics(analysis_df)
            cluster_summary["topic"] = cluster_summary["cluster"].map(cluster_topics)

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
                "topic:N",
                title="대표 topic",
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
                color=alt.Color("topic:N", title="대표 topic"),
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


        distribution_chart = (
            alt.Chart(cluster_summary)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
            .encode(
                y=alt.Y("topic:N", title="대표 topic", sort="-x"),
                x=alt.X("question_count:Q", title="질문 수"),
                color=alt.Color("topic:N", legend=None),
                tooltip=[
                    alt.Tooltip("topic:N", title="대표 topic"),
                    alt.Tooltip("question_count:Q", title="질문 수"),
                ],
            )
            .properties(height=260)
        )
        st.altair_chart(distribution_chart, use_container_width=True)


        # =================================================
        # Cluster 질문 확인
        # =================================================

        st.subheader(
            "Cluster별 실제 질문"
        )


        selected_topic = st.selectbox("대표 topic 선택", list(cluster_topics.values()))


        cluster_questions = (
            analysis_df[
                analysis_df["topic"] == selected_topic
            ]
        )


        show_columns = [
            col
            for col in [
                "query_id",
                "query",
                "gold_answer",
                "source_documents",
                "topic",
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

        def horizontal_metric_chart(value_column, title):
            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                .encode(
                    y=alt.Y("experiment:N", title=None, sort="-x"),
                    x=alt.X(f"{value_column}:Q", title=title),
                    color=alt.Color("model:N", legend=None),
                    tooltip=[
                        alt.Tooltip("experiment:N", title="실험"),
                        alt.Tooltip(f"{value_column}:Q", title=title),
                    ],
                )
                .properties(height=max(260, len(chart_df) * 42))
            )
            st.altair_chart(chart, use_container_width=True)

        st.subheader("🔍 평균 검색 시간")
        horizontal_metric_chart("avg_search_time", "평균 검색 시간")


        # =================================================
        # 평균 답변 생성 시간
        # =================================================

        st.subheader("🤖 평균 답변 생성 시간")
        horizontal_metric_chart("avg_generation_time", "평균 답변 생성 시간")


        # =================================================
        # 평균 전체 응답 시간
        # =================================================

        st.subheader("⏱️ 평균 전체 응답 시간")
        horizontal_metric_chart("avg_total_time", "평균 전체 응답 시간")


        # =================================================
        # 최종 설정 안내
        # =================================================

        st.info(
            "현재 서비스 Retriever 설정: Top-K = 10"
        )
