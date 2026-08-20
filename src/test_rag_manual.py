import pandas as pd

from retriever import retrieve_context
from rag_chain import create_rag_chain
from source import build_sources


EVALSET_PATH = "evaluation/golden_set10.csv"

evalset = pd.read_csv(
    EVALSET_PATH,
    encoding="utf-8",
)

# 여기서 먼저 CSV 구조 확인
print("컬럼명:", evalset.columns.tolist())
print(evalset.head())

# 그 다음 query 컬럼 사용
questions = evalset["query"].tolist()

rag_chain = create_rag_chain()

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