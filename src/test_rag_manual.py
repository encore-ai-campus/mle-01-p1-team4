from retriever import retrieve_context
from rag_chain import create_rag_chain
from source import build_sources


rag_chain = create_rag_chain()


questions = [
    "휴직 중에도 직무급을 받을 수 있나요?",
    "점심시간은 몇 시부터 몇 시까지인가요?",
]


for question in questions:

    print("\n" + "=" * 80)
    print("질문:", question)
    print("=" * 80)

    results, context_docs, context = retrieve_context(
        question=question,
        k=3,
        window=1,
    )

    rag_result = rag_chain.invoke({
        "context": context,
        "question": question,
    })

    answer = rag_result.get(
        "answer",
        "답변 생성 실패",
    )

    used_chunk_ids = rag_result.get(
        "used_chunk_ids",
        [],
    )

    sources = build_sources(
        context_docs,
        used_chunk_ids,
    )

    print("\n[답변]")
    print(answer)

    print("\n[출처]")

    for source in sources:
        print("-", source)

    print("\n[Retriever Top-3]")

    for index, doc in enumerate(
        results,
        start=1,
    ):
        print(
            index,
            doc.metadata.get("chunk_id"),
            doc.metadata.get("document_name"),
        )

    print("\n[실제 LLM Context chunk]")

    for doc in context_docs:
        print(
            doc.metadata.get("chunk_id"),
            doc.metadata.get("chunk_no"),
        )