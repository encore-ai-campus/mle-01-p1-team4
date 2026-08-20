from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
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
        - 제공된 Context에 명시된 내용만 근거로 답변하세요.
        - Context에 없는 내용은 추측하거나 만들어내지 마세요.
        - 질문과 직접 관련된 규정을 우선하여 답변하세요.
        - 서로 다른 급여 항목이나 규정을 혼동하지 마세요.
        - 여러 문서의 내용이 충돌하면 임의로 판단하지 말고 충돌 사실을 알려주세요.
        - 근거가 부족하면 "제공된 문서만으로는 확인하기 어렵습니다."라고 답변하세요.
        - 핵심 내용을 먼저 간결하게 설명하세요.

        답변 형식:
        답변:
        사용자의 질문에 대한 핵심 내용을 설명합니다.

        근거:
        - 문서명 / 조항 또는 별표
        - 해당 판단의 근거가 된 내용을 간단히 설명합니다.
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
    parser = StrOutputParser()

    # 4. Chain 연결
    chain = prompt | llm | parser

    # 5. 반환
    return chain
