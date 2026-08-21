from retriever import (
    load_vector_store,
    get_retriever,
    build_context,
    expand_related_appendices,
)

from rag_chain import create_rag_chain

from query_rewriter import (
    rewrite_query,
    format_chat_history,
)

from source import build_sources


# =========================================================
# RAG 초기화
# =========================================================

def initialize_rag():

    # TODO 1
    # 저장되어 있는 Chroma Vector Store를 불러오세요.

    vector_store = load_vector_store()


    # TODO 2
    # Vector Store를 이용하여 Retriever를 생성하세요.
    #
    # 현재 실험 결과에서 결정한
    # k=10을 사용하세요.

    retriever = get_retriever(
        store=vector_store,
        k=10,
    )


    # TODO 3
    # 현재 사용 중인 RAG Chain을 생성하세요.

    chain = create_rag_chain()


    return vector_store, retriever, chain


# =========================================================
# 검색 질문 생성
# =========================================================

def make_search_question(
    question,
    messages,
):

    # TODO 4
    # 기존 messages를 검색 질문 재작성에 사용할 수 있도록
    # 문자열 형태의 chat_history로 변환하세요.

    chat_history = format_chat_history(messages)


    # TODO 5
    # 이전 대화가 존재하는 경우
    # 현재 질문을 독립적으로 이해할 수 있는
    # 검색용 질문으로 재작성하세요.
    #
    # 이전 대화가 없다면
    # 현재 질문을 그대로 사용하세요.

    if chat_history.strip():

        search_question = rewrite_query(
            question=question,
            chat_history=chat_history,
        )

    else:

        search_question = question


    return search_question


# =========================================================
# 관련 문서 검색
# =========================================================

def retrieve_documents(
    search_question,
    retriever,
    vector_store,
):

    # TODO 6
    # Retriever를 이용하여
    # 검색 질문과 관련된 Top-K 문서를 검색하세요.

    documents = retriever.invoke(
        search_question
    )


    # TODO 7
    # 검색된 문서가 특정 조항과 연결된 별표를 참조하는 경우
    # 관련 별표까지 검색 결과에 추가하세요.
    #
    # 이전에 구현한 별표 확장 함수를 재사용합니다.

    documents = expand_related_appendices(
        store=vector_store,
        documents=documents,
    )


    return documents


# =========================================================
# 최종 답변 생성
# =========================================================

def generate_answer(
    question,
    messages,
    vector_store,
    retriever,
    chain,
):

    # TODO 8
    # 현재 질문과 이전 대화를 이용하여
    # Retriever 검색용 질문을 생성하세요.

    search_question = make_search_question(
        question=question,
        messages=messages,
    )


    # TODO 9
    # 검색 질문을 이용하여
    # 관련 사내 규정 문서를 검색하세요.

    documents = retrieve_documents(
        search_question=search_question,
        retriever=retriever,
        vector_store=vector_store,
    )


    # TODO 10
    # 검색된 Document들을
    # LLM에게 전달할 하나의 Context로 구성하세요.

    context = build_context(
        documents
    )


    # TODO 11
    # 현재 RAG Chain에
    # question과 context를 전달하여
    # 답변을 생성하세요.
    #
    # rag_chain.py의 실제 입력 변수 구조와
    # 일치하는지 확인하세요.

    response = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )


    # TODO 12
    # RAG Chain의 결과에서
    # 실제 사용자에게 보여줄 답변을 추출하세요.

    answer = response.get(
        "answer",
        "답변을 생성하지 못했습니다.",
    )


    # TODO 13
    # LLM이 실제 답변 생성에 사용한 chunk_id를 이용하여
    # 사용자에게 보여줄 출처 정보를 생성하세요.

    used_chunk_ids = response.get(
        "used_chunk_ids",
        [],
    )

    sources = build_sources(
        documents=documents,
        used_chunk_ids=used_chunk_ids,
    )


    # TODO 14
    # app.py에서 답변, 출처, 원문 PDF 등을
    # 활용할 수 있도록 결과를 하나의 dict로 반환하세요.

    return {
        "answer": answer,
        "sources": sources,
        "documents": documents,
        "search_question": search_question,
    }
    
