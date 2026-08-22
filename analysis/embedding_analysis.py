import re

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from umap import UMAP

from src.rag.ingest import get_embeddings


DOCUMENT_TOPICS = {
    "급여규정": "급여·수당",
    "복무규정": "복무·근태",
    "연차_휴가에_관한_예규": "휴가·연차",
    "여비규정": "출장·여비",
    "인사규정": "인사·복무",
    "승진임용규칙": "승진·인사",
    "보안업무예규": "보안·자료",
    "공간정보보안업무예규": "공간정보 보안",
}


def load_golden_set(csv_path):

    df = pd.read_csv(csv_path)

    df = df.dropna(
        subset=["query"]
    )

    return df


def embed_questions(df, embedding_model=None):
    if embedding_model is None:
        embedding_model = get_embeddings()
    questions = df["query"].tolist()
    vectors = embedding_model.embed_documents(questions)
    return np.array(vectors)


def reduce_embeddings(
    embeddings,
    n_neighbors=15,
    min_dist=0.1,
):

    reducer = UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=42,
    )


    reduced = reducer.fit_transform(
        embeddings
    )

    return reduced


def cluster_embeddings(
    embeddings,
    n_clusters=5,
):

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init="auto",
    )


    labels = model.fit_predict(
        embeddings
    )

    return labels



def get_cluster_summary(
    analysis_df,
):

    summary = (
        analysis_df["cluster"]
        .value_counts()
        .sort_index()
        .rename_axis("cluster")
        .reset_index(name="question_count")
    )

    total = len(
        analysis_df
    )

    summary["ratio"] = (
        summary["question_count"]
        / total
        * 100
    )


    return summary


def add_cluster_topics(analysis_df):
    """Add readable topic and source-document labels to cluster results."""
    result = analysis_df.copy()

    def document_names(value):
        if pd.isna(value):
            return []
        names = []
        for chunk_id in str(value).split("|"):
            match = re.match(r"^(.+)_\d+$", chunk_id.strip())
            if match:
                names.append(match.group(1))
        return names

    result["source_documents"] = result.get("gold_chunks", "").apply(
        lambda value: ", ".join(dict.fromkeys(document_names(value)))
    )

    cluster_topics = {}
    for cluster_id, cluster_df in result.groupby("cluster"):
        documents = []
        for value in cluster_df.get("gold_chunks", []):
            documents.extend(document_names(value))
        if documents:
            representative = pd.Series(documents).value_counts().index[0]
            topic = DOCUMENT_TOPICS.get(representative, representative.replace("_", " "))
        else:
            topic = f"주제 {cluster_id}"
        cluster_topics[cluster_id] = topic

    result["topic"] = result["cluster"].map(cluster_topics)
    return result, cluster_topics


def build_embedding_analysis_from_embeddings(
    df,
    embeddings,
    n_clusters=5,
    n_neighbors=15,
    min_dist=0.1,
):

    reduced = reduce_embeddings(
        embeddings=embeddings,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
    )

    clusters = cluster_embeddings(
        embeddings=embeddings,
        n_clusters=n_clusters,
    )

    result = df.copy()

    result["x"] = reduced[:, 0]
    result["y"] = reduced[:, 1]
    result["cluster"] = clusters

    return result


def load_experiment_summary(
    csv_path,
):

    df = pd.read_csv(
        csv_path
    )

    required_columns = [
        "model",
        "k",
        "avg_search_time",
        "avg_generation_time",
        "avg_total_time",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"필수 컬럼이 없습니다: "
            f"{missing_columns}"
        )

    numeric_columns = [
        "k",
        "avg_search_time",
        "avg_generation_time",
        "avg_total_time",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=numeric_columns
    )

    df = df.sort_values(
        [
            "model",
            "k",
        ]
    ).reset_index(
        drop=True
    )

    return df
