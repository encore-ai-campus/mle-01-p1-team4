from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
        당신은 회사 규정 및 사내 문서에 근거하여 답변하는 AI 어시스턴트입니다.

        답변 규칙:
        1. 이전 대화를 참고한다.
        2. 현재 질문을 독립적으로 이해 가능한 질문으로 바꾼다.
        3. 답변은 하지 않는다.
        4. 검색용 질문만 반환한다.
        
        예:
            이전 대화:
            사용자: 국내 출장 숙박비 알려줘
            챗봇: ...
            현재 질문: 그럼 해외는?
            결과: 국외 출장 숙박비 지급 기준은 무엇인가?
        """,
            ),
            (
            "human",
            """
            이전 대화:
            {chat_history}

            현재 질문:
            {question}

            위 내용을 바탕으로 검색에 사용할 독립적인 질문만 반환하세요.
            """,
        ),
        ]
    )

def rewrite_query(question, chat_history):

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    chain = prompt | llm | StrOutputParser()

    search_question = chain.invoke({
        "question": question,
        "chat_history": chat_history
    })

    return search_question

def format_chat_history(messages):

    history = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "user":
            history.append(f"사용자: {content}")

        elif role == "assistant":
            history.append(f"챗봇: {content}")

    return "\n".join(history)