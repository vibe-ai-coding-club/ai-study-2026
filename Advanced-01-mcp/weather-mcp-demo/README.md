# 🌤️ MCP 날씨 서버 데모

Function Calling에서 MCP로의 전환을 보여주는 5분 시연용 프로젝트

## 📦 포함된 파일

1. **weather-mcp-server.ts** - MCP 날씨 서버 코드 (TypeScript)
2. **package.json** - 프로젝트 의존성
3. **tsconfig.json** - TypeScript 설정

## ⚡ 빠른 시작

```bash
# 1. 프로젝트 폴더 생성
mkdir weather-mcp-demo
cd weather-mcp-demo

# 2. 파일 복사
# 위 3개 파일(weather-mcp-server.ts, package.json, tsconfig.json)을 이 폴더에 복사

# 3. 패키지 설치
npm install

# 4. 컴파일
npx tsc

# 5. Claude Desktop 설정
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json
```

**claude_desktop_config.json 내용:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "node",
      "args": [
        "/절대/경로/weather-mcp-demo/dist/weather-mcp-server.js"
      ]
    }
  }
}
```

⚠️ **중요**: `/절대/경로/` 부분을 실제 경로로 변경하세요!

## 🎬 시연 방법

### 간단 요약:
1. Claude Desktop에서 🔧 아이콘 확인
2. "서울의 현재 날씨가 어때?" 질문
3. AI가 자동으로 함수 호출하는 모습 시연
4. "도쿄와 뉴욕의 날씨를 화씨로 비교해줘" 복잡한 질문

## 🎯 시연 효과

- ✅ Function Calling이 실제로 작동하는 모습
- ✅ JSON Schema 사용 확인
- ✅ MCP의 표준화 효과 체감
- ✅ 비개발자도 이해 가능한 예시

## 🔍 트러블슈팅

**문제**: 🔧 아이콘이 안 보임
- Claude Desktop 재시작
- config 파일 경로 확인
- dist/ 폴더에 .js 파일 존재 확인

**문제**: 함수 호출 안 됨
- 명확하게 질문 ("서울 날씨 알려줘")
- 🔧 아이콘 클릭해서 서버 연결 확인

**문제**: "Server disconnected" 오류
- 절대 경로 사용 확인 (`~/` 대신 `/Users/사용자명/` 형식)
- JavaScript 파일 존재 확인
- 터미널에서 직접 실행 테스트

## ✅ 빠른 체크리스트

문제가 생겼을 때 순서대로 확인하세요:

```bash
# 1. 파일 존재 확인
ls -la ~/Downloads/01_MCP/mcp_show/weather-mcp-demo/dist/weather-mcp-server.js

# 2. 컴파일 다시 실행
cd ~/Downloads/01_MCP/mcp_show/weather-mcp-demo
npx tsc

# 3. 직접 실행 테스트
node dist/weather-mcp-server.js
# "Weather MCP Server running on stdio" 나오면 정상 → Ctrl+C로 종료

# 4. config 파일 확인
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 5. Claude Desktop 재시작
# Cmd+Q로 완전 종료 후 다시 실행
```

### 💡 가장 흔한 실수 Top 3

1. **상대 경로 사용** ❌
   - `~/Downloads/...` 대신 `/Users/홍길동/Downloads/...` 절대 경로 사용하세요
   
2. **TypeScript 컴파일 안 함** ❌
   - `npx tsc` 실행해서 dist/ 폴더에 .js 파일 생성 필수
   
3. **JSON 문법 오류** ❌
   - claude_desktop_config.json의 쉼표, 중괄호 확인

### 🧪 MCP Inspector로 고급 테스트

더 확실한 디버깅:

```bash
npx @modelcontextprotocol/inspector node dist/weather-mcp-server.js
```

브라우저가 열리고 서버를 시각적으로 테스트할 수 있습니다.

## 📚 더 알아보기

- MCP 공식 문서: https://modelcontextprotocol.io
- GitHub: https://github.com/modelcontextprotocol

---
