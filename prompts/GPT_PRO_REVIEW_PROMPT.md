# GPT Pro Review Prompt

Use this when asking GPT Pro to review Codex work.

```text
아래 Codex 산출물을 LPSF 관점에서 검토해 주세요.

중심 기준:
- 단순 RAG 구현으로 축소되지 않았는가?
- 경험 이후 상태공간 지형이 달라지는 구조가 실제로 있는가?
- plasticity operator가 명확한가?
- 2nd brain을 안전하게 다루는가?
- baseline 비교와 실험 설계가 충분한가?
- 환각/과잉은유를 막는 장치가 있는가?
- Codex가 다음에 할 작업이 명확한가?

원하는 출력:
1. 잘된 점
2. 틀린 방향 또는 빠진 점
3. 아키텍처 수정 제안
4. 실험 수정 제안
5. AGENTS.md/GOAL 수정안
6. 바로 Codex에 붙일 수 있는 다음 지시문
```

