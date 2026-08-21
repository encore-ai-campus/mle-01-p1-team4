def build_sources(
    documents,
    used_chunk_ids,
):
    sources = []
    seen_sources = set()

    # LLM이 이상한 ID를 반환해도 무시할 수 있도록 set으로 변환
    used_chunk_ids = set(used_chunk_ids)

    for doc in documents:
        metadata = doc.metadata

        chunk_id = metadata.get("chunk_id")

        # LLM이 실제 근거로 사용했다고 한 chunk만 출처로 사용
        if chunk_id not in used_chunk_ids:
            continue

        document_name = metadata.get(
            "document_name",
            "문서명 없음",
        )

        section_type = metadata.get(
            "section_type"
        )

        if section_type == "main":
            article_no = metadata.get(
                "article_no"
            )

            if article_no:
                source_key = (
                    f"{document_name} {article_no}"
                )
            else:
                source_key = document_name

        elif section_type == "appendix":
            appendix_no = metadata.get(
                "appendix_no"
            )

            appendix_title = metadata.get(
                "appendix_title"
            )

            if appendix_no and appendix_title:
                source_key = (
                    f"{document_name} "
                    f"{appendix_no} - "
                    f"{appendix_title}"
                )

            elif appendix_no:
                source_key = (
                    f"{document_name} "
                    f"{appendix_no}"
                )

            elif appendix_title:
                source_key = (
                    f"{document_name} - "
                    f"{appendix_title}"
                )

            else:
                source_key = document_name

        else:
            source_key = document_name

        if source_key in seen_sources:
            continue

        seen_sources.add(source_key)

        source = source_key
        sources.append(source)

    return sources