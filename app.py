import base64

import streamlit as st

from src.config import ASSET_DIR

from src.ui.home import (
    get_frequent_tasks,
    get_recommended_questions,
    get_department_info,
)

from src.rag.chatbot import (
    initialize_rag,
    generate_answer,
)

from src.ui.chat_ui import (
    inject_chatbot_css,
    render_chat_welcome,
    render_example_questions,
    render_user_message,
    render_randy_message,
    render_randy_error,
)

from src.rag.ingest import (
    get_embeddings,
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
# Embedding Model Cache
#
# 무거운 HuggingFace Embedding 모델은
# Streamlit 프로세스당 한 번만 생성한다.
# =========================================================

@st.cache_resource(show_spinner=False)
def get_cached_embedding_model():

    return get_embeddings()


# =========================================================
# RAG Cache
#
# Embedding Model
# → Chroma
# → Retriever
# → RAG Chain
#
# 전체를 한 번 초기화하고 재사용한다.
# =========================================================

@st.cache_resource(show_spinner=False)
def get_cached_rag():

    embeddings = get_cached_embedding_model()

    return initialize_rag(
        embeddings=embeddings
    )


# =========================================================
# 홈 → 챗봇 이동
# =========================================================

def move_to_chatbot(question):

    st.session_state.pending_question = question
    st.session_state.next_page = "💬 규정 챗봇"

    st.rerun()


# =========================================================
# 다음 페이지 처리
# =========================================================

if st.session_state.next_page is not None:

    st.session_state.page = (
        st.session_state.next_page
    )

    st.session_state.next_page = None


# =========================================================
# 전체 CSS
# =========================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --green:#168b54;
        --dark:#15221f;
        --line:#dfe7e4;
        --soft:#f4f8f6;
    }

    html,
    body,
    [class*="css"] {
        font-family:'Noto Sans KR', sans-serif;
    }

    .stApp {
        background:#f6f8f7;
        color:var(--dark);
    }

    [data-testid="stSidebar"] {
        background:#f8fbfa;
        border-right:1px solid #e4ece9;
        min-width:16vw;
        max-width:16vw;
    }

    [data-testid="stSidebar"] section {
        padding:2rem 1rem;
    }

    [data-testid="stSidebar"]
    [role="radiogroup"]
    label > div:first-child {
        display:none;
    }

    [data-testid="stSidebar"]
    [role="radiogroup"]
    label {
        border-radius:10px;
        padding:.65rem .75rem;
        margin:.2rem 0;
        color:#25352e;
    }

    [data-testid="stSidebar"]
    [role="radiogroup"]
    label:has(input:checked) {
        background:#168b54;
        color:#fff;
    }

    .brand {
        text-align:center;
        padding:.3rem 0 1.8rem;
    }

    .brand-mark {
        color:var(--green);
        font-size:3.5rem;
        font-weight:800;
        letter-spacing:-.12em;
        line-height:1;
    }

    .brand-name {
        font-weight:800;
        font-size:1rem;
        margin-top:.7rem;
    }

    .brand-sub {
        color:var(--green);
        font-weight:700;
        margin-top:.25rem;
    }

    .hero {
        position:relative;
        padding:1.2rem 0 .5rem;
        min-height:190px;
        overflow:hidden;
    }

    .hero h1 {
        font-size:2rem;
        line-height:1.35;
        letter-spacing:-.06em;
        margin:1rem 0 .9rem;
        color:#111;
    }

    .hero h1 span {
        color:var(--green);
    }

    .hero p {
        color:#6b7774;
        margin:0;
    }

    .hero-mascot {
        position:absolute;
        right:2%;
        bottom:-10px;
        width:225px;
        max-height:205px;
        object-fit:contain;
    }

    .speech {
        position:absolute;
        right:18%;
        top:1rem;
        z-index:1;
        padding:.75rem 1.1rem;
        border:2px solid var(--green);
        border-radius:20px;
        background:#fff;
        color:#111;
        font-weight:700;
        text-align:center;
        line-height:1.35;
        box-shadow:0 3px 8px rgba(17,48,39,.04);
    }

    .speech:after {
        content:"";
        position:absolute;
        right:18px;
        bottom:-12px;
        width:18px;
        height:18px;
        background:#fff;
        border-right:2px solid var(--green);
        border-bottom:2px solid var(--green);
        transform:rotate(35deg);
    }

    .search-wrap {
        background:white;
        border:1px solid #d8e1dd;
        border-radius:14px;
        padding:.25rem;
        box-shadow:0 4px 18px rgba(17,48,39,.06);
    }

    .section-title {
        font-size:1.25rem;
        font-weight:800;
        letter-spacing:-.04em;
        margin:.25rem 0 .85rem;
    }

    .section-title span {
        color:var(--green);
    }

    .card {
        background:#fff;
        border:1px solid var(--line);
        border-radius:18px;
        padding:1.2rem 1.3rem;
        box-shadow:0 5px 18px rgba(17,48,39,.05);
        height:100%;
    }

    .card h3 {
        margin:0 0 .7rem;
        font-size:1.15rem;
        letter-spacing:-.04em;
    }

    .card-desc {
        color:#68736f;
        font-size:.9rem;
        margin-bottom:.8rem;
    }

    .rank-row {
        display:flex;
        align-items:center;
        gap:.7rem;
        padding:.65rem 0;
        border-bottom:1px solid #edf1ef;
        font-size:.9rem;
    }

    .rank-row:last-child {
        border-bottom:0;
    }

    .rank {
        width:25px;
        height:25px;
        display:grid;
        place-items:center;
        border-radius:50%;
        background:#e7f4ed;
        color:var(--green);
        font-weight:800;
    }

    .recent-row {
        padding:.55rem 0;
        border-bottom:1px solid #edf1ef;
        font-size:.9rem;
    }

    .recent-row:last-child {
        border-bottom:0;
    }

    .department-table {
        width:100%;
        border-collapse:collapse;
        font-size:.78rem;
        color:#24312c;
    }

    .department-table th {
        background:#edf3f0;
        font-weight:700;
        text-align:left;
        padding:.45rem .5rem;
        border-bottom:1px solid #dfe8e3;
    }

    .department-table td {
        padding:.45rem .5rem;
        border-bottom:1px solid #edf1ef;
        vertical-align:top;
    }

    .department-table tr:last-child td {
        border-bottom:0;
    }

    .stButton > button {
        border-radius:12px;
        border:1px solid #e1e8e5;
        background:#fff;
        color:#16231e;
        min-height:46px;
    }

    .stButton > button:hover {
        border-color:#168b54;
        color:#0b6b3a;
    }

    @media (max-width: 900px) {

        .hero-mascot {
            opacity:.35;
            right:-35px;
        }

        .hero h1 {
            font-size:1.65rem;
        }

        [data-testid="stSidebar"] {
            min-width:0;
            max-width:none;
        }

        .speech {
            right:25%;
            transform:scale(.82);
            transform-origin:top right;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">LX</div>
            <div class="brand-name">
                한국국토정보공사
            </div>
            <div class="brand-sub">
                LXpert
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "메뉴",
        [
            "🏠 홈",
            "💬 규정 챗봇",
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
#
# 중요:
# 홈에서는 initialize_rag()를 호출하지 않는다.
# =========================================================

if page == "🏠 홈":

    # -----------------------------------------------------
    # Hero
    # -----------------------------------------------------

    mascot_path = (
        ASSET_DIR
        / "Welcome 랜디.png"
    )

    mascot_src = ""

    if mascot_path.exists():

        mascot_src = (
            "data:image/png;base64,"
            + base64.b64encode(
                mascot_path.read_bytes()
            ).decode("ascii")
        )

    st.markdown(
        f'''
    <div class="hero">
        <h1>안녕하세요! 오늘도 <span>규정 검색</span>을 도와드릴게요.</h1>
        <p>궁금한 규정이나 업무를 빠르게 찾아보세요.</p>
        <div class="speech">궁금한 규정이나<br>업무를 검색해보세요!</div>
        <img class="hero-mascot" src="{mascot_src}">
    </div>
    ''',
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # 검색창
    # -----------------------------------------------------

    search_col, button_col = st.columns(
        [5, 1],
        vertical_alignment="bottom",
    )

    with search_col:

        search_query = st.text_input(
            "규정 검색",
            placeholder="규정이나 업무를 검색하세요",
            label_visibility="collapsed",
        )

    with button_col:

        search_clicked = st.button(
            "검색",
            use_container_width=True,
            type="primary",
        )

    if (
        search_clicked
        and search_query.strip()
    ):

        move_to_chatbot(
            search_query.strip()
        )


    # -----------------------------------------------------
    # 빠른 검색
    # -----------------------------------------------------

    popular_keyword = st.pills(
        "빠른 검색",
        [
            "연차",
            "출장비",
            "초과근무수당",
            "승진",
            "휴직",
        ],
        label_visibility="collapsed",
    )

    if popular_keyword:

        move_to_chatbot(
            f"{popular_keyword} 관련 규정을 알려줘"
        )


    # -----------------------------------------------------
    # 자주 찾는 업무
    # -----------------------------------------------------

    try:

        tasks = get_frequent_tasks()

    except Exception:

        tasks = []


    upper_left, upper_right = st.columns(
        2,
        gap="medium",
    )

    lower_left, lower_right = st.columns(
        2,
        gap="medium",
    )


    with upper_left:

        with st.container(border=True):

            st.markdown(
                "### 🚀 자주 찾는 업무"
            )

            st.caption(
                "필요한 업무를 빠르게 확인해보세요."
            )

            task_cols = st.columns(
                3,
                gap="small",
            )

            for index, task in enumerate(
                tasks[:6]
            ):

                with task_cols[index % 3]:

                    if st.button(
                        f'{task["icon"]}  '
                        f'{task["label"]}',
                        key=f"task_{index}",
                        use_container_width=True,
                    ):

                        move_to_chatbot(
                            task["question"]
                        )


    # -----------------------------------------------------
    # 추천 질문
    # -----------------------------------------------------

    with upper_right:

        with st.container(border=True):

            st.markdown(
                "### 💡 추천 질문"
            )

            st.caption(
                "자주 확인하는 규정을 "
                "빠르게 찾아보세요."
            )

            try:

                questions = (
                    get_recommended_questions()
                )

            except Exception:

                questions = []

            for index, question in enumerate(
                questions[:5]
            ):

                q_col, b_col = st.columns(
                    [1, 12],
                    vertical_alignment="center",
                )

                with q_col:

                    st.markdown(
                        f"""
                        <div class="rank">
                            {index + 1}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with b_col:

                    if st.button(
                        question,
                        key=f"recommended_{index}",
                        use_container_width=True,
                    ):

                        move_to_chatbot(
                            question
                        )


    # -----------------------------------------------------
    # 최근 질문
    # -----------------------------------------------------

    with lower_left:

        with st.container(border=True):

            st.markdown(
                "### 🕘 나의 최근 질문"
            )

            user_messages = [
                message["content"]
                for message
                in st.session_state.messages
                if message["role"] == "user"
            ]

            if user_messages:

                for (
                    index,
                    recent_question,
                ) in enumerate(
                    user_messages[-5:][::-1]
                ):

                    if st.button(
                        f"•  {recent_question}",
                        key=f"recent_{index}",
                        use_container_width=True,
                    ):

                        move_to_chatbot(
                            recent_question
                        )

            else:

                st.info(
                    "아직 질문 기록이 없습니다."
                )


    # -----------------------------------------------------
    # 담당 부서
    # -----------------------------------------------------

    with lower_right:

        with st.container(border=True):

            st.markdown(
                "### ☎ 담당 부서 안내"
            )

            st.caption(
                "규정만으로 해결되지 않는 경우, "
                "담당 부서에 문의해 주세요."
            )

            try:

                departments = (
                    get_department_info()
                )

                headers = [
                    "업무 분야",
                    "지사/부서",
                    "연락처",
                ]

                rows = "".join(

                    "<tr>"
                    + "".join(
                        f"<td>"
                        f"{item.get(header, '')}"
                        f"</td>"
                        for header
                        in headers
                    )
                    + "</tr>"

                    for item
                    in departments
                )

                table = (
                    "<table class='department-table'>"
                    "<thead>"
                    "<tr>"
                    + "".join(
                        f"<th>{header}</th>"
                        for header
                        in headers
                    )
                    + "</tr>"
                    "</thead>"
                    f"<tbody>{rows}</tbody>"
                    "</table>"
                )

                st.markdown(
                    table,
                    unsafe_allow_html=True,
                )

            except Exception:

                st.info(
                    "담당 부서 정보가 없습니다."
                )


# =========================================================
# PAGE 2
# CHATBOT
# =========================================================

elif page == "💬 규정 챗봇":

    inject_chatbot_css()

    st.markdown(
        """
        <h1 class="chatbot-page-title">
            💬 사내 문서 챗봇
        </h1>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================
    # RAG 초기화
    #
    # 첫 챗봇 페이지 진입 시 한 번만 실행
    # 이후 cache_resource에서 재사용
    # =====================================================

    try:

        vector_store, retriever, chain = (
            get_cached_rag()
        )

    except Exception as e:

        render_randy_error(
            (
                "랜디가 규정 검색을 "
                "준비하지 못했어요.\n\n"
                "잠시 후 다시 시도해 주세요."
            ),
            e,
        )

        st.stop()


    # =====================================================
    # 질문 입력
    # =====================================================

    typed_question = st.chat_input(
        (
            "예: 시간단위 연차 사용 기준은 "
            "어떻게 되나요?"
        ),
        key="chatbot_question_input",
    )

    pending_question = (
        st.session_state.pending_question
    )

    if pending_question:

        question = pending_question

        st.session_state.pending_question = None

    else:

        question = typed_question


    # =====================================================
    # 최초 안내 화면
    # =====================================================

    if (
        not st.session_state.messages
        and not question
    ):

        render_chat_welcome()
        render_example_questions()


    # =====================================================
    # 기존 대화 출력
    # =====================================================

    for message in (
        st.session_state.messages
    ):

        if message["role"] == "assistant":

            render_randy_message(
                message["content"],
                message.get("sources"),
                ASSET_DIR,
            )

        else:

            render_user_message(
                message["content"]
            )


    # =====================================================
    # 새로운 질문 처리
    # =====================================================

    if question:

        previous_messages = (
            st.session_state.messages.copy()
        )

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        render_user_message(
            question
        )


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
                    "answer"
                )

                sources = result.get(
                    "sources",
                    [],
                )

                followup_questions = result.get(
                    "followup_questions",
                    [],
                )

                if (
                    not answer
                    or not str(answer).strip()
                ):

                    raise ValueError(
                        "응답에 answer가 없습니다."
                    )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "followup_questions": followup_questions,
                    }
                )

                st.rerun()


            except Exception as e:

                render_randy_error(
                    error=e,
                    asset_dir=ASSET_DIR,
                )


    # =====================================================
    # 후속 질문
    # =====================================================

    if (
        st.session_state.messages
        and st.session_state.messages[-1].get(
            "role"
        ) == "assistant"
        and not question
    ):

        follow_col1, follow_col2 = (
            st.columns(2)
        )

        followups = st.session_state.messages[-1].get(
            "followup_questions",
            [],
        )

        for (
            follow_col,
            followup,
        ) in zip(
            (follow_col1, follow_col2),
            followups,
        ):

            with follow_col:

                if st.button(
                    followup,
                    key=(
                        f"followup_"
                        f"{len(st.session_state.messages)}_"
                        f"{followup}"
                    ),
                    use_container_width=True,
                ):

                    st.session_state.pending_question = (
                        followup
                    )

                    st.rerun()