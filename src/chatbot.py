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


def initialize_rag():

    vector_store = load_vector_store()

    retriever = get_retriever(
        store=vector_store,
        k=10,
    )

    chain = create_rag_chain()

    return vector_store, retriever, chain


def make_search_question(
    question,
    messages,
):

    chat_history = format_chat_history(
        messages
    )

    if chat_history.strip():

        search_question = rewrite_query(
            question=question,
            chat_history=chat_history,
        )

    else:

        search_question = question

    return search_question


def retrieve_documents(
    search_question,
    retriever,
    vector_store,
):

    documents = retriever.invoke(
        search_question
    )

    documents = expand_related_appendices(
        store=vector_store,
        documents=documents,
    )

    return documents


def generate_answer(
    question,
    messages,
    vector_store,
    retriever,
    chain,
):

    search_question = make_search_question(
        question=question,
        messages=messages,
    )

    documents = retrieve_documents(
        search_question=search_question,
        retriever=retriever,
        vector_store=vector_store,
    )

    context = build_context(
        documents
    )

    response = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    answer = response.get(
        "answer",
        "답변을 생성하지 못했습니다.",
    )

    used_chunk_ids = response.get(
        "used_chunk_ids",
        [],
    )

    sources = build_sources(
        documents=documents,
        used_chunk_ids=used_chunk_ids,
    )

    return {
        "answer": answer,
        "sources": sources,
        "documents": documents,
        "search_question": search_question,
    }