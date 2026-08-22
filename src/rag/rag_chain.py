from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI


def create_rag_chain():

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 2. Prompt 생성
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
        당신은 회사 규정 및 사내 문서에 근거하여 답변하는 AI 어시스턴트입니다.

        답변 규칙:
        - Context에 없는 내용은 추측하거나 만들어내지 마세요.
        - 문서명, 조항 번호, 별표 번호 등의 출처 정보는 임의로 생성하지 마세요.
        - 질문과 직접 관련된 규정을 우선하여 답변하세요.
        - 서로 다른 급여 항목이나 규정을 혼동하지 마세요.
        - 여러 문서의 내용이 충돌하면 임의로 판단하지 말고 충돌 사실을 알려주세요.
        - 근거가 부족하면 "제공된 문서만으로는 확인하기 어렵습니다."라고 답변하세요.
        - 핵심 내용을 먼저 간결하게 설명하세요.
        각 검색 문서는 다음 형식으로 제공됩니다.

        [검색 문서 N | chunk_id: 문서명_번호]

        답변을 작성할 때 실제 판단 근거로 사용한 검색 문서의
        chunk_id만 used_chunk_ids에 포함하세요.

        단순히 Context에 존재한다는 이유로 사용하지 않은 chunk_id를
        included_chunk_ids에 넣지 마세요.

        반드시 다음 JSON 형식으로만 답변하세요.

        {{
            "answer": "사용자에게 보여줄 최종 답변",
            "used_chunk_ids": ["실제로 답변 근거로 사용한 chunk_id"]
        }}
        """,
            ),
            (
                "human",
                """
	다음 검색된 사내 규정을 참고하여 질문에 답변하세요.
				
	[검색된 규정]
	{context}
				
	[사용자 질문]
	{question}
	""",
            ),
        ]
    )

    # 3. 출력 parser
    parser = JsonOutputParser()

    # 4. Chain 연결
    chain = prompt | llm | parser

    # 5. 반환
    return chain
