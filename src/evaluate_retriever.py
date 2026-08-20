import pandas as pd
from retriever import retrieve_context
from rag_chain import create_rag_chain

rag_chain = create_rag_chain()

EVALSET_PATH = "evaluation/questions/rag_eval_set.csv"

evalset = pd.read_csv(
    EVALSET_PATH,
    encoding="utf-8",
)

def hit_at_k(predicted, relevant, k):
    """상위 k개 중 정답이 하나라도 있으면 1, 없으면 0."""
    return 1 if any(p in relevant for p in predicted[:k]) else 0


def precision_at_k(predicted, relevant, k):
    """상위 k개 중 정답의 비율(정답 개수 / k)."""
    return sum(1 for p in predicted[:k] if p in relevant) / k


def recall_at_k(predicted, relevant, k):
    """전체 정답 중 상위 k개가 건진 비율(찾은 정답 수 / 전체 정답 수)."""
    return sum(1 for p in predicted[:k] if p in relevant) / len(relevant)


def mrr_at_k(predicted, relevant, k):
    """첫 정답 순위의 역수(1위면 1, 2위면 0.5 ...). 상위 k개 안에 없으면 0."""
    for rank, p in enumerate(predicted[:k], 1):
        if p in relevant:
            # 처음 만난 정답에서 바로 끝낸다
            return 1 / rank
    return 0.0
    
# 라벨을 '문항 id -> 정답 조각 목록' 사전으로 만듦
gold_map = {row.query_id: row.gold_chunks.split('|') for row in evalset.itertuples()}

def evaluate(k):
    rows = []

    for row in evalset.itertuples():

        results, _, _ = retrieve_context(
            question=row.query,
            k=k,
            window=1,
        )

        predicted = [
            doc.metadata["chunk_id"]
            for doc in results
        ]

        relevant = gold_map[row.query_id]

        rows.append({
            "query_id": row.query_id,
            "Hit": hit_at_k(predicted, relevant, k),
            "P": precision_at_k(predicted, relevant, k),
            "R": recall_at_k(predicted, relevant, k),
            "MRR": mrr_at_k(predicted, relevant, k),
        })

    return pd.DataFrame(rows)


scores = evaluate(3)
print('잰 문항 수:', len(scores))

# 결과 시각화
detail = scores.merge(evalset[['query_id', 'query', '정답수']], on='query_id')
print(detail[['query_id', 'Hit', 'P', 'R', 'MRR', '정답수', 'query']].round(3))

# 평균
print('K = 3 평균')
print(scores[['Hit', 'P', 'R', 'MRR']].mean().round(3).to_string())

# k를 바꿀 때 평가지표가 어떻게 달라지는가?
compare = pd.DataFrame([{'K': k, **evaluate(k)[['Hit', 'P', 'R', 'MRR']].mean().round(3)}
                        for k in (3, 10)])
print(compare)


for row in evalset.itertuples():
    question = row.query

    results, neighbor_results, context = retrieve_context(
        question=question
    )

