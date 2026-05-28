# LPSF Codex Markdown Pack (원본 운영 패키지 — 한국어)

> 이 문서는 프로젝트 초기의 "Codex 운영 패키지" 인트로입니다. 프로젝트가
> 실제 구현 + 실험 단계로 넘어가면서 front-door는 영문 [`README.md`](../README.md)로
> 옮겨졌습니다. 아래는 원래 비전과 운영 규칙의 기록입니다.

이 문서 묶음은 **LPSF: Landscape-Plastic Semantic Field / 지형가소성 의미장 모델**을 Codex가 장기 목표(`/goal`)로 실행할 수 있게 만들기 위한 프로젝트 운영 패키지였습니다.

핵심 목표는 단순 RAG를 넘어서, 사용자의 2nd brain을 읽고 다시 프롬프트에 넣는 시스템이 아니라 **경험 이후 반응 가능성의 지형이 달라지는 시스템**을 실험하는 것입니다.

> ⚠ **현재 구현은 이 비전보다 더 좁고 구체적입니다.** 정직한 현재 포지셔닝은
> [`docs/lpsf/CURRENT_STATUS.md`](lpsf/CURRENT_STATUS.md)를 보세요. 요약: LPSF v0.1은
> "LLM 내부 가소성"이 아니라 **retrieval 후보 위의 memory-conditioned reranking layer**입니다.

## 이 팩의 목적

1. LPSF 아이디어를 실행 가능한 기술 명세로 고정합니다.
2. Codex가 세팅, repo 파악, 2nd brain 파악, 문헌 리서치, 구현, 실험, 평가, 기록을 반복 수행할 수 있게 합니다.
3. 사용자의 2nd brain을 원문 저장소가 아니라 **지식 전수/RAG/지형가소성 실험의 기반**으로 다루게 합니다.
4. 민감 정보 유출, 무분별한 원문 복사, 기존 노트 훼손, 환각성 연구 정리를 방지합니다.

## 핵심 원칙

- 기억은 원문 재독이 아니라 **상태 변화**입니다.
- 2nd brain은 사용자의 지식 유전체입니다. 에이전트는 이를 무단 수정하지 않고, 새 노트/요약/링크/상태 변형 로그를 안전한 위치에 작성합니다.
- LPSF-v0.1은 새 foundation model이 아니라 **외부 지형 상태 + LLM decoder + plasticity operator + eval loop**로 시작합니다.
- 양자/중력/후성유전 같은 표현은 초기 구현에서 은유로 쓰지 말고, 각각 `hypothesis superposition`, `attractor/energy scoring`, `expression gating/plasticity mark`로 작동 정의합니다.
- 모든 실험은 baseline과 비교해야 합니다: `LLM only`, `LLM + RAG`, `LLM + static memory`, `LLM + LPSF`.

## 원래 문서 구조 (theory pack)

```text
docs/01_LPSF_THESIS.md … 09_LPSF_SPEC_V0_1.md   이론·아키텍처·로드맵
docs/lpsf/LPSF_SPEC.md                           동결된 v0.1 스펙
docs/lpsf/CURRENT_STATUS.md                       정직한 현재 포지셔닝 (정본)
second_brain/                                     2nd brain 프로토콜·스캔 계획
research/                                         리서치 큐·논문 읽기 규칙
ops/                                              상태 로그·안전 워크플로
```
