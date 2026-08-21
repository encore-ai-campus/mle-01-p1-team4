from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.cluster import KMeans
from umap import UMAP

from ingest import get_embeddings


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_DIR = PROJECT_ROOT / "evaluation"
RESULT_DIR = EVALUATION_DIR / "results"


def load_golden_set(csv_path):

    df = pd.read_csv(csv_path)

    df = df.dropna(
        subset=["query"]
    )

    return df


def embed_questions(df):

    embedding_model = get_embeddings()

    questions = df["query"].tolist()

    vectors = embedding_model.embed_documents(
        questions
    )

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
