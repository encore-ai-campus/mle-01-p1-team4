import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

from src.home import (
    get_frequent_tasks,
    get_recommended_questions,
    get_department_info,
    get_regulation_pdfs,
)

from src.chatbot import (
    initialize_rag,
    generate_answer,
)

from src.analysis import (
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

PROJECT_ROOT = Path(__file__).resolve().parent

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
    st.session_state.page = "💬 규정 챗봇"

    st.rerun()


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    logo_path = ASSET_DIR / "lx_logo.png"

    if logo_path.exists():
        st.image(
            logo_path,
            width=160,
        )

    st.title(
        "LX AI 규정 도우미"
    )

    st.divider()

    page = st.radio(
        "메뉴",
        [
            "🏠 홈",
            "💬 규정 챗봇",
            "📊 데이터 분석",
        ],
        key="page",
        label_visibility="collapsed",
    )

    st.divider()

    if st.button(
        "🗑️ 대화 초기화",
        use_container_width=True,
    ):

        st.session_state.messages = []
        st.session_state.pending_question = None

        st.rerun()


# =========================================================
# PAGE 1
# HOME
# =========================================================

if page == "🏠 홈":

    # =====================================================
    # Header
    # =====================================================

    left, right = st.columns(
        [3, 1],
        vertical_alignment="center",
    )

    with left:

        st.title(
            "안녕하세요! 오늘도 규정 검색을 도와드릴게요. 👋"
        )

        st.caption(
            "궁금한 규정이나 업무를 빠르게 찾아보세요."
        )

    with right:

        mascot_path = ASSET_DIR / "mascot.png"

        if mascot_path.exists():

            st.image(
                mascot_path,
                width=170,
            )


    # =====================================================
    # 검색
    # =====================================================

    search_col, button_col = st.columns(
        [5, 1],
        vertical_alignment="bottom",
    )

    with search_col:

        search_query = st.text_input(
            "규정 검색",
            placeholder="예: 휴직 중에도 직무급을 받을 수 있나요?",
            label_visibility="collapsed",
        )

    with button_col:

        search_clicked = st.button(
            "🔍 검색",
            use_container_width=True,
        )

    if search_clicked and search_query.strip():

        move_to_chatbot(
            search_query.strip()
        )


    # =====================================================
    # 인기/빠른 검색어
    # =====================================================

    st.markdown(
        "#### 🔥 빠른 검색"
    )

    popular_keyword = st.pills(
        "빠른 검색",
        [
            "연차",
            "출장비",
            "직무급",
            "승진",
            "휴직",
        ],
        label_visibility="collapsed",
    )

    if popular_keyword:

        move_to_chatbot(
            f"{popular_keyword} 관련 규정을 알려줘"
        )


    st.divider()


    # =====================================================
    # 자주 찾는 업무
    # =====================================================

    st.subheader(
        "⭐ 자주 찾는 업무"
    )

    try:

        tasks = get_frequent_tasks()

    except Exception as e:

        st.error(
            "자주 찾는 업무 데이터를 불러오지 못했습니다."
        )

        st.exception(e)

        tasks = []


    if tasks:

        task_cols = st.columns(3)

        for index, task in enumerate(tasks):

            col = task_cols[
                index % 3
            ]

            with col:

                clicked = st.button(
                    f"{task['icon']} {task['label']}",
                    key=f"task_{index}",
                    use_container_width=True,
                )

                if clicked:

                    move_to_chatbot(
                        task["question"]
                    )


    st.divider()


    # =====================================================
    # 추천 질문 / 담당 부서
    # =====================================================

    left_col, right_col = st.columns(2)


    # =====================================================
    # 추천 질문
    # =====================================================

    with left_col:

        with st.container(
            border=True
        ):

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


    # =====================================================
    # PDF
    # =====================================================

    st.divider()

    st.subheader(
        "📚 규정 원문 바로가기"
    )

    try:

        pdfs = get_regulation_pdfs()

        if pdfs:

            selected_pdf = st.selectbox(
                "규정 선택",
                pdfs,
                format_func=lambda x:
                    x["document_name"],
            )

            pdf_path = (
                selected_pdf["path"]
            )

            if pdf_path.exists():

                pdf_data = (
                    pdf_path.read_bytes()
                )

                st.download_button(
                    "📄 PDF 원문 다운로드",
                    data=pdf_data,
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "선택한 PDF 파일을 찾을 수 없습니다."
                )

        else:

            st.info(
                "등록된 규정 PDF가 없습니다."
            )

    except Exception as e:

        st.error(
            "PDF 목록을 불러오지 못했습니다."
        )

        st.exception(e)


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