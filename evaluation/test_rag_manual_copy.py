from pathlib import Path
import time

import pandas as pd


from rag.retriever import retrieve_context
from rag_chain import create_rag_chain
from source import build_sources


EVALSET_PATH = "evaluation/golden_set.csv"
OUTPUT_PATH = Path(
    "evaluation/results/rag_result_k5_gpt-5-mini.csv"
)


evalset = pd.read_csv(
    EVALSET_PATH,
    encoding="utf-8",
)

print("컬럼명:", evalset.columns.tolist())
print(evalset.head())


rag_chain = create_rag_chain()

# 질문별 결과를 저장할 리스트
evaluation_rows = []
# 전체 평가 시간 측정 시작
total_start_time = time.perf_counter()


# 질문뿐만 아니라 골든셋의 전체 행을 순회
for _, row in evalset.iterrows():

    question = row["query"]
    # 현재 질문의 전체 처리 시간 측정 시작
    question_start_time = time.perf_counter()

    # 골든셋 정답 및 정답 chunk_id
    # 실제 CSV 컬럼명에 맞게 수정
    golden_answer = row.get(
        "answer",
        "",
    )

    expected_chunk_ids = row.get(
        "source",
        "",
    )

    print("\n" + "=" * 80)
    print("질문:", question)
    print("=" * 80)

    retrieval_start_time = time.perf_counter()

    results, context_docs, context = retrieve_context(
        question=question,
        k=5,
        window=1,
    )

    retrieval_end_time = time.perf_counter()

    retrieval_time = (
        retrieval_end_time
        - retrieval_start_time
    )

    generation_start_time = time.perf_counter()

    rag_result = rag_chain.invoke({
        "context": context,
        "question": question,
    })

    generation_end_time = time.perf_counter()

    generation_time = (
        generation_end_time
        - generation_start_time
    )

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

    # --------------------------------------------
    # 파일에 저장할 형태로 결과 정리
    # --------------------------------------------

    retriever_top_k = "\n".join(
        [
            (
                f"{index}. "
                f"{doc.metadata.get('chunk_id', '출처 없음')} "
                f"({doc.metadata.get('document_name', '문서명 없음')})"
            )
            for index, doc in enumerate(
                results,
                start=1,
            )
        ]
    )

    context_chunk_ids = "\n".join(
        [
            (
                f"{doc.metadata.get('chunk_id', '출처 없음')} "
                f"(chunk_no={doc.metadata.get('chunk_no', '없음')})"
            )
            for doc in context_docs
        ]
    )

    # used_chunk_ids가 리스트일 때 한 줄로 변환
    used_chunk_ids_text = (
        "|".join(used_chunk_ids)
        if isinstance(used_chunk_ids, list)
        else str(used_chunk_ids)
    )

    # sources가 리스트일 때 줄바꿈 문자열로 변환
    sources_text = (
        "\n".join(str(source) for source in sources)
        if isinstance(sources, list)
        else str(sources)
    )

    question_end_time = time.perf_counter()

    question_total_time = (
        question_end_time
        - question_start_time
    )

    print("\n[처리 시간]")
    print(f"검색 시간: {retrieval_time:.3f}초")
    print(f"답변 생성 시간: {generation_time:.3f}초")
    print(f"질문 전체 시간: {question_total_time:.3f}초")

    evaluation_rows.append({
        "질문": question,
        "골든 답변": golden_answer,
        "생성 답변": answer,
        "정답 chunk_id": expected_chunk_ids,
        "LLM 사용 chunk_id": used_chunk_ids_text,
        "생성 답변 출처": sources_text,
        "Retriever Top-3": retriever_top_k,
        "실제 LLM Context chunk": context_chunk_ids,

        # 시간 측정 결과 추가
        "검색 시간(초)": round(retrieval_time, 3),
        "답변 생성 시간(초)": round(generation_time, 3),
        "질문 전체 시간(초)": round(question_total_time, 3),
    })


# --------------------------------------------
# 모든 질문의 평가가 끝난 후 파일 저장
# --------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

result_df = pd.DataFrame(
    evaluation_rows
)

result_df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

total_end_time = time.perf_counter()

total_elapsed_time = (
    total_end_time
    - total_start_time
)

average_elapsed_time = (
    total_elapsed_time
    / len(evalset)
    if len(evalset) > 0
    else 0
)

print("\n" + "=" * 80)
print("평가 완료")
print("결과 저장 위치:", OUTPUT_PATH.resolve())
print("=" * 80)
print(f"전체 평가 시간: {total_elapsed_time:.3f}초")
print(f"질문당 평균 시간: {average_elapsed_time:.3f}초")

if not result_df.empty:
    print(
        "평균 검색 시간:",
        f"{result_df['검색 시간(초)'].mean():.3f}초",
    )

    print(
        "평균 답변 생성 시간:",
        f"{result_df['답변 생성 시간(초)'].mean():.3f}초",
    )

    print(
        "평균 질문 전체 시간:",
        f"{result_df['질문 전체 시간(초)'].mean():.3f}초",
    )