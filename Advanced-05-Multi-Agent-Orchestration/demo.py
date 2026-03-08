import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def main():
    # .env 로드
    load_dotenv()

    # 필수 환경변수 체크
    required_vars = [
        "OPENAI_API_KEY",
        "LANGSMITH_API_KEY",
        "LANGSMITH_TRACING",
        "LANGSMITH_PROJECT",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(
            f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}"
        )

    print("환경변수 확인 완료")
    print(f"LANGSMITH_PROJECT = {os.getenv('LANGSMITH_PROJECT')}")
    print(f"LANGSMITH_TRACING = {os.getenv('LANGSMITH_TRACING')}")
    print("-" * 50)

    # 1. 프롬프트 템플릿
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 초보 개발자에게 친절하게 설명하는 AI 튜터입니다."),
            ("human", "{topic}에 대해 3문장으로 설명해줘."),
        ]
    )

    # 2. LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
    )

    # 3. 출력 파서
    parser = StrOutputParser()

    # 4. LangChain LCEL 파이프라인
    chain = prompt | llm | parser

    # 실행 입력
    user_input = {
        "topic": "LangChain과 LangSmith의 차이점"
    }

    print("체인 실행 시작")
    print(f"입력값: {user_input}")
    print("-" * 50)

    # 실행
    result = chain.invoke(user_input)

    print("실행 결과")
    print(result)
    print("-" * 50)

    print("이제 LangSmith 사이트에서 trace를 확인해보세요.")
    print("보통 prompt -> model -> parser 단계가 실행 흐름으로 보입니다.")


if __name__ == "__main__":
    main()