# GPT Pro Consultation Packet — LPSF

Use this packet when asking GPT Pro to review Codex progress or help with architecture decisions.

## 1. 목표

사용자가 달성하려는 최종 상태:

```text
LPSF-v0.1을 구현한다. LPSF는 단순 RAG가 아니라 경험 이후 반응 가능성의 지형이 달라지는 시스템이다. 목표는 외부 2nd brain/RAG를 evidence layer로 활용하면서, persistent landscape state와 plasticity operators를 통해 같은 입력도 경험 전후 다르게 해석/판단하게 만드는 prototype이다.
```

## 2. 현재 로컬 맥락

Codex가 채워야 함:

```text
- repo 구조:
- 주요 파일:
- 언어/프레임워크:
- 기존 테스트 명령:
- 기존 빌드 명령:
- 기존 RAG/DB/vector code:
- 기존 AGENTS.md 규칙:
- 안전하게 쓸 수 있는 폴더:
- 건드리면 안 되는 폴더:
```

## 3. 2nd brain 맥락

Codex가 민감 정보 제외 후 채워야 함:

```text
- 2nd brain 위치/access mode:
- 관련 노트 클러스터:
- 관련 결정/선호:
- 과거 실패/주의점:
- 프로젝트 운영 규칙:
- 외부 사용 금지 내용:
- LPSF와 직접 연결되는 개념:
```

## 4. 제약

기본 제약:

```text
- 기존 2nd brain 원문 노트 수정 금지.
- raw private content 외부 공유/커밋 금지.
- env/secrets 접근/출력 금지.
- production DB/배포 금지.
- 기존 API/테스트가 있으면 깨지지 않게 유지.
- 양자/후성유전/중력 표현은 작동 정의 없이 과장 금지.
- RAG 구현만 하고 LPSF라고 부르지 말 것.
```

## 5. GPT Pro에게 요청

```text
다음을 검토해 주세요.

1. 전체 접근 전략이 LPSF의 핵심인 "경험 이후 상태공간 지형 변화"를 제대로 구현하는가?
2. 작업 분해가 안전하고 검증 가능한가?
3. 오케스트레이터 역할과 subagent 분리가 적절한가?
4. 각 에이전트의 입력/출력/파일 소유권이 안전한가?
5. 위험한 결정 지점은 무엇인가?
6. 먼저 확인해야 할 질문은 무엇인가?
7. AGENTS.md 또는 작업 규칙에서 빠진 것은 무엇인가?
8. 실험 설계가 RAG baseline과 구분되는가?
9. 환각/과잉은유를 막는 장치가 충분한가?
10. 2nd brain을 지식 전수/RAG/landscape state로 사용하는 방식이 안전한가?
```

## 6. 원하는 출력 형식

```text
- 실행 계획
- 병렬화 계획
- 검증 계획
- Codex용 작업 지시문
- 위험/중단 조건
- AGENTS.md 패치 초안
- 추가로 필요한 문서/테스트 목록
```

