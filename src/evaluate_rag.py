from retriever import retrieve_context
from rag_chain import create_rag_chain
from source import build_sources
import pandas as pd

EVALSET_PATH = "evaluation/questions/rag_eval_set.csv"

evalset = pd.read_csv(
    EVALSET_PATH,
    encoding="utf-8",
)

rag_chain = create_rag_chain()

for row in evalset.itertuples():
    question = row.query

    results, context_docs, context = retrieve_context(
        question=question
    )
    answer = rag_chain.invoke({
    "context": context,
    "question": question,
    })
    sources = build_sources(context_docs)