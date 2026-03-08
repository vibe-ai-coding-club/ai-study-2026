# ai-study-2026
2026 AI Study Advanced Track 실습 코드 저장소입니다.

# LangSmith + LangChain Demo

간단한 LangChain 체인을 실행하고, 그 실행 과정을 LangSmith에서 trace로 확인하는 예제입니다.

## 1. 패키지 설치
```bash
pip install -r requirements.txt
```

## 2. 환경변수 설정
.env.example 파일을 복사해서 .env 파일을 만든 뒤, 아래 값을 입력합니다

## 3. 실행
python demo.py

## 4. 확인 포인트

실행이 끝나면 LangSmith에서 아래 항목을 확인할 수 있습니다.

입력값

프롬프트

모델 호출 결과

전체 실행 trace

## 참고

OPENAI_API_KEY: OpenAI 호출용 키

LANGSMITH_API_KEY: LangSmith 추적용 키

LANGSMITH_TRACING=true: tracing 활성화

LANGSMITH_PROJECT: LangSmith 프로젝트 이름