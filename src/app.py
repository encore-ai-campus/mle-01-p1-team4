import streamlit as st
from retriever import load_vector_store, get_retriever, build_context
from rag_chain import create_rag_chain
from source import build_sources

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
        k=5,
    )

    chain = create_rag_chain()

    return retriever, chain



st.title("📚 사내 규정 챗봇")
st.caption("사내 규정을 기반으로 질문에 답변합니다.")

try:
    retriever, chain = initialize_rag()

except Exception as e:
    st.error("RAG 시스템을 초기화하는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("📚 참고한 규정"):
                for source in message["sources"]:
                    st.markdown(f"- {source}")

question = st.chat_input(
    "사내 규정에 대해 궁금한 내용을 입력하세요."
)


if question:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("관련 규정을 찾고 있습니다..."):

            try:
                docs = retriever.invoke(question)

                context = build_context(docs)

                chain_input = {
                    "question": question,
                    "context": context,
                }

                response = chain.invoke(chain_input)

                answer = response.get("answer", "답변 생성 실패")

                sources = build_sources(
                    documents=docs,
                    used_chunk_ids=response.get("used_chunk_ids", []),
                )


                st.markdown(answer)


                if sources:
                    with st.expander("📚 참고한 규정"):
                        for source in sources:
                            st.markdown(f"- {source}")


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

    # 대화 초기화 버튼
    if st.button("🗑️ 대화 내용 초기화"):
        st.session_state.messages = []
        st.rerun()
