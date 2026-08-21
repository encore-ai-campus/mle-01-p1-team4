from pathlib import Path

import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent / "assets"

_Randy_ASSETS = {
    "computer": ("컴퓨터하는 랜디.png", "🤖"),
    "hello": ("안녕~ 랜디.png", "🌱"),
    "idea": ("아이디어 랜디.png", "💡"),
    "error": ("NO하는 랜디.png", "⚠️"),
}


def get_randy_avatar(kind="hello"):
    filename, fallback = _Randy_ASSETS.get(kind, _Randy_ASSETS["hello"])
    path = ASSET_DIR / filename
    return str(path) if path.exists() else fallback


def inject_chatbot_css():
    st.markdown(
        """
        <style>
        .chatbot-page-title { color:#243B32; letter-spacing:-.04em; }
        .chatbot-page-caption { color:#66736E; margin-bottom:1rem; }
        .chatbot-guide { background:#F4FAF5; border:1px solid #DFE9E1; border-radius:16px; padding:1rem 1.1rem; min-height:135px; }
        .chatbot-guide h4 { margin:0 0 .45rem; color:#0B6B3A; }
        .chatbot-guide p { margin:.2rem 0; color:#66736E; font-size:.9rem; line-height:1.55; }
        .chatbot-brand { color:#0B6B3A; font-size:.78rem; font-weight:700; margin-bottom:.25rem; }
        .chatbot-error { background:#FFF7F5; border:1px solid #F2D8D2; border-radius:14px; padding:.9rem 1rem; color:#7A3228; }
        [data-testid="stChatMessage"] { border-radius:14px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


EXAMPLE_QUESTIONS = [
    ("🌴", "시간단위 연차 사용 기준은 어떻게 되나요?"),
    ("💰", "휴직 중에도 직무급을 받을 수 있나요?"),
    ("✈️", "1급 이하 직원의 국내 출장 식비는 얼마인가요?"),
    ("📈", "기능직 4등급의 승진소요 최저연수는 얼마인가요?"),
    ("🏠", "육아휴직을 신청하려면 어떤 절차가 필요한가요?"),
    ("🔐", "공개제한 공간정보는 어떻게 관리해야 하나요?"),
]


def render_chat_welcome():
    title_col, image_col = st.columns([5, 1], vertical_alignment="center")
    with title_col:
        st.markdown('<h1 class="chatbot-page-title">💬 사내 규정 AI 챗봇</h1>', unsafe_allow_html=True)
        st.markdown('<p class="chatbot-page-caption">사내 규정을 기반으로 필요한 기준과 근거 문서를 빠르게 찾아드려요.</p>', unsafe_allow_html=True)
    with image_col:
        st.image(get_randy_avatar("computer"), width=145)

    guide_left, guide_right = st.columns(2, gap="medium")
    with guide_left:
        st.markdown(
            '<div class="chatbot-guide"><h4>✨ 이렇게 질문해 보세요</h4><p>궁금한 업무와 상황을 함께 적으면 더 정확한 규정을 찾을 수 있어요.</p><p><b>좋은 질문 예시</b><br>“1급 이하 직원이 부산으로 1박 2일 출장할 때 숙박비 상한액은 얼마인가요?”</p></div>',
            unsafe_allow_html=True,
        )
    with guide_right:
        st.markdown(
            '<div class="chatbot-guide"><h4>📚 답변 활용 안내</h4><p>답변 아래의 ‘참고한 규정’을 열면 근거 문서를 확인할 수 있어요.</p><p>개인별 승인이나 최종 판단이 필요한 내용은 담당 부서에 다시 확인해 주세요.</p></div>',
            unsafe_allow_html=True,
        )


def render_example_questions():
    st.markdown("### 💡 예시 질문")
    columns = st.columns(3, gap="small")
    for index, (icon, question) in enumerate(EXAMPLE_QUESTIONS):
        with columns[index % 3]:
            if st.button(f"{icon}  {question}", key=f"example_question_{index}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()


def render_user_message(content):
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(content)


def render_randy_message(content, sources=None):
    with st.chat_message("assistant", avatar=get_randy_avatar("hello")):
        st.markdown('<div class="chatbot-brand">랜디 · LX 규정 도우미</div>', unsafe_allow_html=True)
        st.markdown(content)
        if sources:
            with st.expander("📚 참고한 규정"):
                for source in sources:
                    st.write(source)


def render_randy_error(message="랜디가 답변을 준비하지 못했어요.\n\n잠시 후 다시 질문해 주세요.", error=None):
    with st.chat_message("assistant", avatar=get_randy_avatar("error")):
        st.markdown('<div class="chatbot-error">' + message.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
        if error:
            with st.expander("개발자 오류 상세"):
                st.exception(error)
