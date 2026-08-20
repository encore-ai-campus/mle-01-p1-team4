from retriever import retrieve_context


def main():

    question = "휴직 중 직무급을 받을 수 있나요?"

    results, neighbor_results, context = (
        retrieve_context(
            question=question,
            k=3,
            window=1,
        )
    )

    print("\n질문:")
    print(question)

    print("\n" + "=" * 70)
    print("Retriever Top-k 결과")
    print("=" * 70)

    print("검색 결과 수:", len(results))

    for index, doc in enumerate(
        results,
        start=1,
    ):

        print("\n" + "-" * 70)
        print(f"검색 결과 {index}")

        print(
            "문서:",
            doc.metadata.get("document_name"),
        )

        print(
            "chunk_id:",
            doc.metadata.get("chunk_id"),
        )

        print(
            "chunk_no:",
            doc.metadata.get("chunk_no"),
        )

        print(
            "article_no:",
            doc.metadata.get("article_no"),
        )

        print(
            "appendix_no:",
            doc.metadata.get("appendix_no"),
        )

        print("\n내용:")
        print(doc.page_content)

    print("\n" + "=" * 70)
    print("1위 결과 기준 ±1 Window")
    print("=" * 70)

    for doc in neighbor_results:

        print(
            doc.metadata.get("document_name"),
            "| chunk_no:",
            doc.metadata.get("chunk_no"),
            "| chunk_id:",
            doc.metadata.get("chunk_id"),
        )

    print("\n" + "=" * 70)
    print("LLM 전달 Context")
    print("=" * 70)

    print(context)


if __name__ == "__main__":
    main()