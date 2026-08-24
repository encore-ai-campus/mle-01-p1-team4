import base64
import random

import streamlit as st

from src.config import ASSET_DIR

from src.ui.home import (
    get_recommended_questions,
    get_department_info,
    get_regulation_pdfs,
    render_travel_expense,
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

from src.rag.ingest import get_embeddings


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
# 업무 상황 데이터
# =========================================================

WORK_SCENARIOS = {
    "✈️ 출장 준비": {
        "items": [
            "식비 지급 기준",
            "숙박비 지역별 상한",
            "교통비 지급 기준",
        ],
        "question": (
            "국내 출장 시 식비, 숙박비, "
            "교통비 지급 기준을 알려줘"
        ),
    },
    "🏖️ 연차 사용": {
        "items": [
            "연차휴가 사용 기준",
            "시간단위 연차 기준",
            "연차 관련 유의사항",
        ],
        "question": (
            "연차휴가와 시간단위 연차 "
            "사용 기준을 알려줘"
        ),
    },
    "🏠 휴직 신청": {
        "items": [
            "휴직 가능 사유",
            "휴직 기간",
            "휴직 중 급여·직무급",
        ],
        "question": (
            "휴직 사유와 기간, 휴직 중 "
            "급여 및 직무급 지급 기준을 알려줘"
        ),
    },
    "💰 급여 확인": {
        "items": [
            "급여 지급 기준",
            "수당 지급 기준",
            "직무급 지급 여부",
        ],
        "question": (
            "급여, 수당, 직무급 지급 기준을 알려줘"
        ),
    },
}


# =========================================================
# Embedding Model Cache
# =========================================================

@st.cache_resource(show_spinner=False)
def get_cached_embedding_model():
    return get_embeddings()


# =========================================================
# RAG Cache
# =========================================================

@st.cache_resource(show_spinner=False)
def get_cached_rag():

    embeddings = get_cached_embedding_model()

    return initialize_rag(
        embeddings=embeddings
    )


# =========================================================
# 홈 -> 챗봇 이동
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
#
# 중요:
# st.markdown 대신 st.html 사용
# =========================================================

st.html(
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


/* ==================================================
   Sidebar
================================================== */

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
    font-weight:700 !important;
}

[data-testid="stSidebar"]
[role="radiogroup"]
label:has(input:checked) {
    background:#168b54;
    color:#fff;
}


/* ==================================================
   Brand
================================================== */

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
    color:#15221f;
}

.brand-sub {
    color:var(--green);
    font-weight:700;
    margin-top:.25rem;
}


/* ==================================================
   Hero
================================================== */

.hero {
    position:relative;
    padding:1.2rem 0 .5rem;
    min-height:210px;
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
    bottom:15px;
    width:225px;
    max-height:205px;
    object-fit:contain;
}

.speech {
    position:absolute;
    right:22%;
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
    right:-13px;
    bottom:18px;
    width:24px;
    height:24px;
    background:#fff;
    border-right:2px solid var(--green);
    border-bottom:2px solid var(--green);
    transform:rotate(-45deg);
}


/* ==================================================
   공통 UI
================================================== */

.rank {
    width:28px;
    height:28px;
    display:grid;
    place-items:center;
    border-radius:50%;
    background:#e7f4ed;
    color:var(--green);
    font-weight:800;
}

.department-table {
    width:100%;
    border-collapse:collapse;
    font-size:.78rem;
    color:#24312c;
}

.department-table th {
    font-weight:700;
    text-align:left;
    padding:.55rem .6rem;
    border-bottom:1px solid #dfe8e3;
}

.department-table td {
    padding:.55rem .6rem;
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


/* ==================================================
   4개 메인 카드
================================================== */

.st-key-pdf_card,
.st-key-question_card,
.st-key-work_card,
.st-key-department_card {
    background:#ffffff !important;
    border:1px solid #dce5e1 !important;
    border-radius:18px !important;
    padding:1.25rem 1.3rem !important;
    box-shadow:0 4px 16px rgba(27,64,51,.045);
    overflow:hidden;
}

.st-key-pdf_card h3,
.st-key-question_card h3,
.st-key-work_card h3,
.st-key-department_card h3 {
    margin-top:0 !important;
    letter-spacing:-.04em;
}


/* ==================================================
   PDF 카드
================================================== */

.st-key-pdf_card
[data-testid="stDownloadButton"] button {
    background:#eef6ff !important;
    border:1px solid #cfdef2 !important;
    color:#163550 !important;
    border-radius:11px !important;
    min-height:48px;
    font-weight:700 !important;
    box-shadow:none !important;
    transition:
        background .15s ease,
        border-color .15s ease,
        transform .15s ease;
}

.st-key-pdf_card
[data-testid="stDownloadButton"] button:hover {
    background:#deedff !important;
    border-color:#9fc2eb !important;
    color:#0c5f9f !important;
    transform:translateY(-1px);
}


/* ==================================================
   추천 질문
================================================== */

.st-key-question_card
.stButton > button {
    background:#fff8e9 !important;
    border:1px solid #f0dfb9 !important;
    color:#29342f !important;
    border-radius:12px !important;
    min-height:52px;
    font-weight:700 !important;
    box-shadow:none !important;
    transition:
        background .15s ease,
        border-color .15s ease,
        transform .15s ease;
}

.st-key-question_card
.stButton > button:hover {
    background:#fff0cf !important;
    border-color:#dfc16f !important;
    color:#765500 !important;
    transform:translateY(-1px);
}


/* ==================================================
   업무 상황
================================================== */

.st-key-work_card
[data-testid="stPills"] button {
    background:#edf8f2 !important;
    border:1px solid #cce7d9 !important;
    color:#17613e !important;
    border-radius:999px !important;
    min-height:40px;
}

.st-key-work_card
[data-testid="stPills"] button:hover {
    background:#dff2e8 !important;
    border-color:#9acbb2 !important;
}

.st-key-work_card
[data-testid="stPills"]
button[aria-pressed="true"] {
    background:#168b54 !important;
    border-color:#168b54 !important;
    color:#ffffff !important;
}

.st-key-work_card
[data-testid="stAlert"] {
    background:#eef6ff !important;
    border:1px solid #cee1f5 !important;
    border-radius:12px !important;
}

.st-key-work_card
.stButton > button[kind="primary"] {
    background:#168b54 !important;
    color:#ffffff !important;
    border-color:#168b54 !important;
}


/* ==================================================
   담당 부서
================================================== */

.st-key-department_card
.department-table {
    background:#fafcfb;
    border:1px solid #dfe8e3;
    border-radius:10px;
    overflow:hidden;
}

.st-key-department_card
.department-table th {
    background:#e8f4ee;
    color:#17382a;
}

.st-key-department_card
.department-table td {
    background:#fbfdfc;
}

.st-key-department_card
.department-table tr:nth-child(even) td {
    background:#f3f8f5;
}


/* ==================================================
   모바일
================================================== */

@media (max-width:900px) {

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
"""
)


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.html(
        """
<div class="brand">
    <div class="brand-mark">LX</div>
    <div class="brand-name">한국국토정보공사</div>
    <div class="brand-sub">LXpert</div>
</div>
"""
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
# =========================================================

if page == "🏠 홈":

    # -----------------------------------------------------
    # Hero
    # -----------------------------------------------------

    mascot_path = (
        ASSET_DIR / "Welcome 랜디.png"
    )

    mascot_src = ""

    if mascot_path.exists():

        mascot_src = (
            "data:image/png;base64,"
            + base64.b64encode(
                mascot_path.read_bytes()
            ).decode("ascii")
        )

    hero_html = f"""
<div class="hero">
    <h1>
        안녕하세요! 오늘도
        <span>규정 검색</span>을 도와드릴게요.
    </h1>

    <p>
        궁금한 규정이나 업무를 빠르게 찾아보세요.
    </p>

    <div class="speech">
        궁금한 규정이나<br>
        업무를 검색해보세요!
    </div>

    <img
        class="hero-mascot"
        src="{mascot_src}"
        alt="LXpert 랜디"
    >
</div>
"""

    st.html(hero_html)


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
            placeholder=(
                "규정이나 업무를 검색하세요"
            ),
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
    # PDF 목록
    # -----------------------------------------------------

    try:

        pdfs = get_regulation_pdfs()

    except Exception as e:

        st.error(
            f"PDF 목록을 불러오지 못했습니다: {e}"
        )

        pdfs = []


    # =====================================================
    # 상단 카드
    # =====================================================

    upper_left, upper_right = st.columns(
        2,
        gap="medium",
    )


    # -----------------------------------------------------
    # PDF 원문
    # -----------------------------------------------------

    with upper_left:

        with st.container(
            border=True,
            height=500,
            key="pdf_card",
        ):

            st.markdown(
                "### 📚 규정 PDF 원문"
            )

            st.caption(
                "원문이 필요한 규정을 "
                "바로 열어 확인할 수 있습니다."
            )

            if pdfs:

                pdf_cols = st.columns(
                    2,
                    gap="small",
                )

                for index, pdf in enumerate(
                    pdfs
                ):

                    pdf_path = pdf["path"]

                    with pdf_cols[
                        index % 2
                    ]:

                        if pdf_path.exists():

                            st.download_button(
                                label=(
                                    f'📄 {pdf["document_name"]}'
                                ),
                                data=pdf_path.read_bytes(),
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                key=f"pdf_{index}",
                                use_container_width=True,
                            )

            else:

                st.info(
                    "표시할 규정 PDF가 없습니다."
                )


    # -----------------------------------------------------
    # 추천 질문
    # -----------------------------------------------------

    with upper_right:

        with st.container(
            border=True,
            height=500,
            key="question_card",
        ):

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

                    st.html(
                        f"""
<div class="rank">
    {index + 1}
</div>
"""
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


    # =====================================================
    # 하단 카드
    # =====================================================

    lower_left, lower_right = st.columns(
        2,
        gap="medium",
    )


    # -----------------------------------------------------
    # 업무 상황
    # -----------------------------------------------------

    with lower_left:

        with st.container(
            border=True,
            height=430,
            key="work_card",
        ):

            st.markdown(
                "### 🧭 지금 어떤 업무를 하고 있나요?"
            )

            st.caption(
                "업무 상황을 선택하면 "
                "확인하면 좋은 규정을 안내해 드립니다."
            )

            selected_scenario = st.pills(
                "업무 상황",
                list(
                    WORK_SCENARIOS.keys()
                ),
                label_visibility="collapsed",
                key="work_scenario",
            )

            if selected_scenario:

                scenario = (
                    WORK_SCENARIOS[
                        selected_scenario
                    ]
                )

                st.markdown(
                    f"**{selected_scenario} 시 "
                    "확인하면 좋은 항목**"
                )

                for item in scenario["items"]:

                    st.markdown(
                        f"- {item}"
                    )

                if st.button(
                    "💬 AI에게 물어보기",
                    key="scenario_chat_button",
                    use_container_width=True,
                    type="primary",
                ):

                    move_to_chatbot(
                        scenario["question"]
                    )

            else:

                st.info(
                    "출장, 연차, 휴직, 급여 중 "
                    "하나를 선택해 보세요."
                )


    # -----------------------------------------------------
    # 담당 부서
    # -----------------------------------------------------

    with lower_right:

        with st.container(
            border=True,
            height=430,
            key="department_card",
        ):

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
                        (
                            "<td>"
                            + str(
                                item.get(
                                    header,
                                    "",
                                )
                            )
                            + "</td>"
                        )
                        for header in headers
                    )
                    + "</tr>"
                    for item in departments
                )

                table = (
                    "<table class='department-table'>"
                    "<thead>"
                    "<tr>"
                    + "".join(
                        (
                            "<th>"
                            + header
                            + "</th>"
                        )
                        for header in headers
                    )
                    + "</tr>"
                    "</thead>"
                    f"<tbody>{rows}</tbody>"
                    "</table>"
                )

                # Markdown 파서 사용 안 함
                st.html(table)

            except Exception:

                st.info(
                    "담당 부서 정보가 없습니다."
                )


    # -----------------------------------------------------
    # 출장 여비
    # -----------------------------------------------------

    render_travel_expense()


# =========================================================
# PAGE 2
# CHATBOT
# =========================================================

elif page == "💬 규정 챗봇":

    inject_chatbot_css()

    # 이것도 HTML 전용 API 사용
    st.html(
        """
<h1 class="chatbot-page-title">
    💬 사내 문서 챗봇
</h1>
"""
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

    for message in st.session_state.messages:

        if message["role"] == "assistant":

            render_randy_message(
                message["content"],
                message.get("sources"),
                ASSET_DIR,
                message.get("randy_kind", "hello"),
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

                randy_candidates = [
                    "hello",
                    "computer",
                    "idea",
                    "talk_4",
                    "talk_5",
                ]

                previous_randy = next(
                    (
                        message.get("randy_kind")
                        for message in reversed(
                            st.session_state.messages
                        )
                        if message["role"] == "assistant"
                    ),
                    None,
                )

                available_candidates = [
                    kind
                    for kind in randy_candidates
                    if kind != previous_randy
                ]

                selected_randy = random.choice(
                    available_candidates
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "followup_questions": followup_questions,
                        "randy_kind": selected_randy,
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
        and st.session_state.messages[
            -1
        ].get("role") == "assistant"
        and not question
    ):

        follow_col1, follow_col2 = (
            st.columns(2)
        )

        followups = (
            st.session_state.messages[-1]
            .get(
                "followup_questions",
                [],
            )
        )

        for (
            follow_col,
            followup,
        ) in zip(
            (
                follow_col1,
                follow_col2,
            ),
            followups,
        ):

            with follow_col:

                if st.button(
                    followup,
                    key=(
                        "followup_"
                        f"{len(st.session_state.messages)}_"
                        f"{followup}"
                    ),
                    use_container_width=True,
                ):

                    st.session_state.pending_question = (
                        followup
                    )

                    st.rerun()