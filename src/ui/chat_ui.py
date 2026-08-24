from pathlib import Path

from PIL import Image, ImageChops
import streamlit as st

from src.config import ASSET_DIR


_Randy_ASSETS = {
    "computer": ("컴퓨터하는 랜디.png", "🤖"),
    "hello": ("안녕~ 랜디.png", "🌱"),
    "idea": ("아이디어 랜디.png", "💡"),
    "error": ("NO하는 랜디.png", "⚠️"),

    # 새로 추가하는 사진만 별도 키 사용
    "talk_4": ("천사 랜디.png", "😊"),
    "talk_5": ("돋보기 랜디.png", "📚"),
}


def get_randy_avatar(kind="hello"):
    filename, fallback = _Randy_ASSETS.get(
        kind,
        _Randy_ASSETS["hello"],
    )

    path = ASSET_DIR / filename

    return str(path) if path.exists() else fallback


@st.cache_data(show_spinner=False)
def load_cropped_randy_image(image_path_str):
    image_path = Path(image_path_str)

    if not image_path.exists():
        return None

    image = Image.open(
        image_path
    ).convert("RGBA")

    alpha = image.getchannel("A")
    bbox = alpha.getbbox()

    full_bbox = (
        0,
        0,
        image.width,
        image.height,
    )

    if bbox == full_bbox:
        background = Image.new(
            "RGBA",
            image.size,
            image.getpixel((0, 0)),
        )

        difference = ImageChops.difference(
            image,
            background,
        ).convert("L")

        difference = difference.point(
            lambda value: 255 if value > 15 else 0
        )

        detected_bbox = difference.getbbox()

        if detected_bbox:
            bbox = detected_bbox

    if bbox:
        image = image.crop(bbox)

    padding = 10

    padded = Image.new(
        "RGBA",
        (
            image.width + padding * 2,
            image.height + padding * 2,
        ),
        (0, 0, 0, 0),
    )

    padded.paste(
        image,
        (padding, padding),
        image,
    )

    return padded


# =========================================================
# 챗봇 CSS
# =========================================================

def inject_chatbot_css():

    st.html(
        """
<style>

section.main > div {
    padding-top:1rem !important;
    padding-bottom:6rem !important;
}

.chatbot-page {
    background:#F8F8F3;
}

.chatbot-page-title {
    color:#1F3029;
    letter-spacing:-.04em;
    margin:0 0 1.1rem;
    font-size:2rem;
    font-weight:800;
}

.chatbot-page-caption {
    color:#66736E;
    margin-bottom:.4rem;
}


/* ==================================================
   챗봇 상단 안내 카드
================================================== */

.chatbot-guide {
    width:100%;
    min-height:205px;
    box-sizing:border-box;

    background:#FFFFFF;

    border:1px solid #DCE5E1;
    border-radius:18px;

    padding:1.25rem 1.3rem;

    box-shadow:
        0 4px 16px
        rgba(27,64,51,.045);
}


/* 안내 카드 제목 */

.chatbot-guide h4 {
    margin:0 0 1rem;

    color:#0B6B3A;

    font-size:1.3rem;
    font-weight:800;

    letter-spacing:-.03em;
}


/* 내부 공통 영역 */

.chatbot-guide-inner {
    border-radius:12px;

    padding:1rem 1.1rem;

    min-height:112px;

    box-sizing:border-box;
}


/* 왼쪽 질문 안내 */

.chatbot-guide-question {
    background:#EEF6FF;

    border:1px solid #D3E4F6;

    color:#263B4A;
}


/* 오른쪽 답변 활용 안내 */

.chatbot-guide-answer {
    background:#FFF8E9;

    border:1px solid #F0DFB9;

    color:#423B2D;
}


/* 내부 일반 텍스트 */

.chatbot-guide p {
    margin:.15rem 0;

    color:inherit;

    font-size:.9rem;

    line-height:1.6;
}


/* 좋은 질문 예시 */

.chatbot-example-title {
    margin-top:.45rem;

    color:#173B2D;

    font-weight:800;

    font-size:.9rem;
}

.chatbot-example-text {
    margin-top:.15rem;

    color:#263B4A;

    font-size:.9rem;

    font-weight:600;

    line-height:1.55;
}


/* ==================================================
   랜디 답변
================================================== */

.chatbot-brand {
    color:#0B6B3A;

    font-size:.78rem;

    font-weight:700;

    margin-bottom:.25rem;
}

.chatbot-error {
    background:#FFF7F5;

    border:1px solid #F2D8D2;

    border-radius:14px;

    padding:.9rem 1rem;

    color:#7A3228;
}

[data-testid="stChatMessage"] {
    border-radius:14px;
}

.randy-name {
    display:inline-block;

    color:#0B6B3A;

    background:#EDF7EF;

    border:1px solid #CFE4D3;

    border-radius:999px;

    padding:.25rem .65rem;

    font-size:.86rem;

    font-weight:700;

    margin-bottom:.7rem;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.randy-name) {
    background:#F4FAF5;

    border:1px solid #D6E7D9;

    border-left:4px solid #159447;

    border-radius:0 16px 16px 16px;

    box-shadow:
        0 8px 24px
        rgba(30,88,55,.06);
}

div[data-testid="stVerticalBlockBorderWrapper"]:has(.randy-name)
div[data-testid="stExpander"] {
    background:#FFFFFF;

    border-color:#DCE7DE;
}


/* ==================================================
   사용자 질문
================================================== */

.chatbot-user-row {
    display:flex;

    justify-content:flex-end;

    max-width:980px;

    margin:.7rem auto;
}

.chatbot-user-card {
    max-width:62%;

    background:#F3F4F3;

    border:1px solid #DDE2DF;

    border-radius:16px;

    padding:.75rem 1rem;

    color:#26352F;
}

.chatbot-followups {
    max-width:980px;

    margin:0 auto 1rem;
}

</style>
"""
    )


# =========================================================
# 예시 질문
# =========================================================

EXAMPLE_QUESTIONS = [
    (
        "🌴",
        "시간단위 연차 사용 기준은 어떻게 되나요?",
    ),
    (
        "💰",
        "휴직 중에도 직무급을 받을 수 있나요?",
    ),
    (
        "✈️",
        "1급 이하 직원의 국내 출장 식비는 얼마인가요?",
    ),
    (
        "📈",
        "기능직 4등급의 승진소요 최저연수는 얼마인가요?",
    ),
    (
        "🏠",
        "육아휴직을 신청하려면 어떤 절차가 필요한가요?",
    ),
    (
        "🔐",
        "공개제한 공간정보는 어떻게 관리해야 하나요?",
    ),
]


# =========================================================
# 챗봇 시작 안내
# =========================================================

def render_chat_welcome():

    guide_left, guide_right = st.columns(
        2,
        gap="medium",
    )

    # -----------------------------------------------------
    # 왼쪽 - 질문 방법
    # -----------------------------------------------------

    with guide_left:

        st.html(
            """
<div class="chatbot-guide">

    <h4>
        ✨ 이렇게 질문해 보세요
    </h4>

    <div class="chatbot-guide-inner chatbot-guide-question">

        <p>
            궁금한 업무와 상황을 함께 적으면
            더 정확한 규정을 찾을 수 있어요.
        </p>

        <div class="chatbot-example-title">
            좋은 질문 예시
        </div>

        <div class="chatbot-example-text">
            “1급 이하 직원이 부산으로 1박 2일 출장할 때
            숙박비 상한액은 얼마인가요?”
        </div>

    </div>

</div>
"""
        )

    # -----------------------------------------------------
    # 오른쪽 - 답변 활용
    # -----------------------------------------------------

    with guide_right:

        st.html(
            """
<div class="chatbot-guide">

    <h4>
        📚 답변 활용 안내
    </h4>

    <div class="chatbot-guide-inner chatbot-guide-answer">

        <p>
            답변 아래의 <b>‘참고한 규정’</b>을 열면
            근거 문서를 확인할 수 있어요.
        </p>

        <p style="margin-top:.65rem;">
            개인별 승인이나 최종 판단이 필요한 내용은
            담당 부서에 다시 확인해 주세요.
        </p>

    </div>

</div>
"""
        )


# =========================================================
# 예시 질문 버튼
# =========================================================

def render_example_questions():

    mascot_col, title_col, _ = st.columns(
        [0.7, 2.3, 7],
        gap="small",
        vertical_alignment="center",
    )

    with mascot_col:

        idea_path = (
            ASSET_DIR
            / _Randy_ASSETS["idea"][0]
        )

        idea_image = load_cropped_randy_image(
            str(idea_path)
        )

        st.image(
            (
                idea_image
                if idea_image is not None
                else get_randy_avatar("idea")
            ),
            width=90,
        )

    with title_col:

        st.markdown(
            "### 💡 예시 질문"
        )

    columns = st.columns(
        3,
        gap="small",
    )

    for index, (
        icon,
        question,
    ) in enumerate(
        EXAMPLE_QUESTIONS
    ):

        with columns[
            index % 3
        ]:

            if st.button(
                f"{icon}  {question}",
                key=f"example_question_{index}",
                use_container_width=True,
            ):

                st.session_state.pending_question = (
                    question
                )

                st.rerun()


# =========================================================
# 사용자 메시지
# =========================================================

def render_user_message(content):

    st.markdown(
        (
            '<div class="chatbot-user-row">'
            '<div class="chatbot-user-card">'
            f'🧑‍💼&nbsp;&nbsp;{content}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# 랜디 답변
# =========================================================

def render_randy_message(
    content,
    sources=None,
    asset_dir=None,
    randy_kind="hello",
):

    current_asset_dir = (
        Path(asset_dir)
        if asset_dir
        else ASSET_DIR
    )

    randy_path = (
        current_asset_dir
        / _Randy_ASSETS.get(
            randy_kind,
            _Randy_ASSETS["hello"],
        )[0]
    )

    randy_image = load_cropped_randy_image(
        str(randy_path)
    )

    _, conversation_col, _ = st.columns(
        [0.6, 8.8, 0.6]
    )

    with conversation_col:

        randy_col, answer_col = st.columns(
            [1.15, 8.85],
            gap="medium",
            vertical_alignment="top",
        )

        with randy_col:

            if randy_image is not None:

                st.image(
                    randy_image,
                    width=92,
                )

            else:

                st.markdown(
                    (
                        '<div '
                        'style="'
                        'font-size:3.5rem;'
                        'text-align:center'
                        '">'
                        '🌱'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

        with answer_col:

            with st.container(
                border=True
            ):

                st.markdown(
                    (
                        '<div class="randy-name">'
                        '랜디 · LX 규정 도우미'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                st.markdown(
                    content
                )

                if sources:

                    with st.expander(
                        "📚 참고한 규정"
                    ):

                        for source in sources:

                            st.write(
                                source
                            )


# =========================================================
# 랜디 오류 메시지
# =========================================================

def render_randy_error(
    message=(
        "랜디가 답변을 준비하지 못했어요.\n\n"
        "잠시 후 다시 질문해 주세요."
    ),
    error=None,
    asset_dir=None,
):

    current_asset_dir = (
        Path(asset_dir)
        if asset_dir
        else ASSET_DIR
    )

    error_path = (
        current_asset_dir
        / _Randy_ASSETS["error"][0]
    )

    error_image = load_cropped_randy_image(
        str(error_path)
    )

    _, conversation_col, _ = st.columns(
        [0.6, 8.8, 0.6]
    )

    with conversation_col:

        randy_col, answer_col = st.columns(
            [1.15, 8.85],
            gap="medium",
            vertical_alignment="top",
        )

        with randy_col:

            if error_image is not None:

                st.image(
                    error_image,
                    width=92,
                )

            else:

                st.markdown(
                    (
                        '<div '
                        'style="'
                        'font-size:3.5rem;'
                        'text-align:center'
                        '">'
                        '⚠️'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

        with answer_col:

            with st.container(
                border=True
            ):

                st.markdown(
                    (
                        '<div class="randy-name">'
                        '랜디 · LX 규정 도우미'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                st.error(
                    message
                )

                if error:

                    with st.expander(
                        "오류 상세 내용"
                    ):

                        st.exception(
                            error
                        )