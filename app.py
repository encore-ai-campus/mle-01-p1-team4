import streamlit as st

from retriever import (
    load_vector_store,
    get_retriever,
    build_context,
    expand_related_appendices,
)
from rag_chain import create_rag_chain
from source import build_sources
from query_rewriter import rewrite_query, format_chat_history


st.set_page_config(
    page_title="사내 규정 챗봇",
    page_icon="📚",
    layout="centered",
)


@st.cache_resource
def initialize_rag():
    """Vector Store, Retriever, RAG Chain을 초기화"""

    vector_store = load_vector_store()

    retriever = get_retriever(
        store=vector_store,
        k=10,
    )

    chain = create_rag_chain()

    return vector_store, retriever, chain


st.title("📚 사내 규정 챗봇")
st.caption("사내 규정을 기반으로 질문에 답변합니다.")


try:
    vector_store, retriever, chain = initialize_rag()

except Exception as e:
    st.error("RAG 시스템을 초기화하는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and message.get("sources")
        ):
            with st.expander("📚 참고한 규정"):
                for source in message["sources"]:
                    st.markdown(f"- {source}")


question = st.chat_input(
    "사내 규정에 대해 궁금한 내용을 입력하세요."
)


if question:

    # =====================================================
    # 1. 이전 대화 확인
    # =====================================================
    chat_history = format_chat_history(
        st.session_state.messages
    )


    # =====================================================
    # 2. 검색용 질문 결정
    #
    # 첫 질문:
    #   → 원래 질문 그대로 사용
    #
    # 후속 질문:
    #   → 이전 대화를 참고해 독립 질문으로 재작성
    # =====================================================
    try:

        if chat_history.strip():
            search_question = rewrite_query(
                question=question,
                chat_history=chat_history,
            )

        else:
            search_question = question

    except Exception as e:
        st.error("검색 질문을 생성하는 중 오류가 발생했습니다.")
        st.exception(e)
        st.stop()


    # =====================================================
    # 3. 원래 사용자 질문 저장
    # =====================================================
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )


    # =====================================================
    # 4. 사용자 질문 출력
    # =====================================================
    with st.chat_message("user"):
        st.markdown(question)


    # =====================================================
    # 5. Assistant 답변 생성
    # =====================================================
    with st.chat_message("assistant"):

        with st.spinner("관련 규정을 찾고 있습니다..."):

            try:

                # -------------------------------------------------
                # Retriever에는 검색에 최적화된 질문 사용
                # -------------------------------------------------
                docs = retriever.invoke(search_question)

                docs = expand_related_appendices(
                    store=vector_store,
                    documents=docs,
                )

                # -------------------------------------------------
                # 검색된 문서를 Context로 변환
                # -------------------------------------------------
                context = build_context(docs)

                # -------------------------------------------------
                # 최종 답변 생성에는
                # 사용자가 실제로 입력한 원래 질문을 사용
                # -------------------------------------------------
                chain_input = {
                    "question": question,
                    "context": context,
                }


                # -------------------------------------------------
                # RAG Chain 실행
                # -------------------------------------------------
                response = chain.invoke(
                    chain_input
                )


                # -------------------------------------------------
                # 답변 추출
                # -------------------------------------------------
                answer = response.get(
                    "answer",
                    "답변 생성 실패",
                )


                # -------------------------------------------------
                # 실제 사용 Chunk 기준 출처 생성
                # -------------------------------------------------
                sources = build_sources(
                    documents=docs,
                    used_chunk_ids=response.get(
                        "used_chunk_ids",
                        [],
                    ),
                )


                # -------------------------------------------------
                # 답변 출력
                # -------------------------------------------------
                st.markdown(answer)


                # -------------------------------------------------
                # 출처 출력
                # -------------------------------------------------
                if sources:
                    with st.expander("📚 참고한 규정"):
                        for source in sources:
                            st.markdown(
                                f"- {source}"
                            )


                # -------------------------------------------------
                # Assistant 답변 저장
                # -------------------------------------------------
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    }
                )


            except Exception as e:
                st.error(
                    "답변을 생성하는 중 오류가 발생했습니다."
                )
                st.exception(e)


with st.sidebar:

    st.header("챗봇 정보")

    st.markdown(
        """
        사내 규정을 검색하여 관련 문서를 찾고,
        검색된 내용을 기반으로 답변합니다.
        """
    )

    st.divider()


    # =====================================================
    # 대화 초기화
    # =====================================================
    if st.button("🗑️ 대화 내용 초기화"):

        st.session_state.messages = []

        st.rerun()