# LPSF Codex Markdown Pack

![tests](https://img.shields.io/badge/tests-206%20passing-brightgreen)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![cost](https://img.shields.io/badge/total%20experimental%20cost-%240.74-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![status](https://img.shields.io/badge/status-research%20mid--result-yellow)

> **CI:** the GitHub Actions workflow is shipped at `ci/github-actions-test.yml`
> (kept outside `.github/workflows/` so it can be pushed without the OAuth
> `workflow` scope). To activate it:
> `gh auth refresh -h github.com -s workflow` then
> `mkdir -p .github/workflows && git mv ci/github-actions-test.yml .github/workflows/test.yml`.
> It runs the full 206-test suite on Python 3.9/3.11/3.12.

이 문서 묶음은 **LPSF: Landscape-Plastic Semantic Field / 지형가소성 의미장 모델**을 Codex가 장기 목표(`/goal`)로 실행할 수 있게 만들기 위한 프로젝트 운영 패키지입니다.

핵심 목표는 단순 RAG를 넘어서, 사용자의 2nd brain을 읽고 다시 프롬프트에 넣는 시스템이 아니라 **경험 이후 반응 가능성의 지형이 달라지는 시스템**을 실험하는 것입니다.

---

## ⚠ 현재 구현 상태 (As of 2026-05-26 — 정직한 요약)

위 문장은 **원래의 연구 비전**입니다. 지금 코드가 실제로 하는 일은 그것보다 더 좁고 더 구체적입니다.

**현재 LPSF v0.1이 실제로 구현한 것:**

> Retrieval 후보 위에 경험 기반 persistent prior를 누적해서, candidate selection 단계의 ranking을 결정론적으로 수정하는 **memory-conditioned reranking layer**.

핵심 선택식:
```
c* = argmax_c [ r(c) + a(c) ]
   r(c) = retrieval (RAG) score for candidate c
   a(c) = accumulated attractor depth from past operator calls
```

**증명된 것 (controllability)**:
- LPSF attractor가 RAG 점수 순위를 *인과적으로 뒤집을 수 있음* (H6 adversarial, 10/10).
- 동일 (snapshot, seed) → 동일 selected_path (H4, 80/80 across claude-sonnet-4-5 + gpt-4o).
- LLMPlusRAG 베이스라인은 LPSF 상태와 무관하게 RAG 순위만 따름 → falsifiable 분리.

**아직 증명 안 된 것 / 과장 금지 영역**:
- ❌ **LLM 내부 추론을 plastic하게 바꾼다** — 현재 path selection은 LLM 출력 텍스트를 사용하지 않음. Temperature 변화가 path에 영향 없는 것은 "attractor dominance"가 아니라 **architectural decoupling**이 정확한 설명.
- ❌ **실제 사용자/지식베이스 일반화** — 모든 실험은 synthetic fixture.
- ❌ **신경과학적 의미의 plasticity** — 8개 operator는 "여러 학습 규칙"이 아니라 단일 prior field에 대한 여러 update policy로 읽어야 정확.

**👉 처음 보는 분은 [`LPSF_PROJECT_SUMMARY.md`](LPSF_PROJECT_SUMMARY.md)부터** — 무엇을 만들었고 무엇이 입증됐는지 한 페이지 요약.

상세 진행/실험 결과: `docs/lpsf/CURRENT_STATUS.md` (정본 포지셔닝), `ops/lpsf/STATUS_LOG.md`, `ops/lpsf/EVALUATION_REPORT.md`, `ops/lpsf/ADVERSARIAL_RESULTS.md`, `ops/lpsf/RANK_FLIP_FRONTIER.md`, `ops/lpsf/FRONTIER_PLOT.md`.

**라이선스**: MIT (`LICENSE`).

---

## 이 팩의 목적

1. LPSF 아이디어를 실행 가능한 기술 명세로 고정합니다.
2. Codex가 세팅, repo 파악, 2nd brain 파악, 문헌 리서치, 구현, 실험, 평가, 기록을 반복 수행할 수 있게 합니다.
3. 사용자의 2nd brain을 원문 저장소가 아니라 **지식 전수/RAG/지형가소성 실험의 기반**으로 다루게 합니다.
4. 민감 정보 유출, 무분별한 원문 복사, 기존 노트 훼손, 환각성 연구 정리를 방지합니다.

## 빠른 사용법

1. 이 폴더를 프로젝트 repo 안의 `docs/lpsf/` 또는 repo 루트에 복사합니다.
2. repo 루트에 `AGENTS.md`가 없다면 이 팩의 `AGENTS.md`를 루트에 배치합니다.
3. Codex에서 프로젝트 폴더를 엽니다.
4. `/plan`으로 먼저 repo와 2nd brain 연결 가능성을 점검시킵니다.
5. `codex/GOAL_LPSF_V0_1.md`의 `/goal` 문구를 Codex에 붙여 넣습니다.
6. Codex가 작업 중 남기는 산출물은 `ops/STATUS_LOG_TEMPLATE.md` 형식으로 기록하게 합니다.

## 문서 구조

```text
README.md
AGENTS.md
PLANS.md
codex/
  CODEX_GOAL_SETUP.md
  GOAL_LPSF_V0_1.md
  CODEX_SESSION_RUNBOOK.md
  SUBAGENT_ORCHESTRATION.md
  GPT_PRO_CONSULT_PACKET.md
docs/
  01_LPSF_THESIS.md
  02_ARCHITECTURE.md
  03_PLASTICITY_OPERATORS.md
  04_MEMORY_FORGETTING.md
  05_DB_SCHEMA.md
  06_IMPLEMENTATION_ROADMAP.md
  07_RISK_REGISTER.md
second_brain/
  2ND_BRAIN_PROTOCOL.md
  2ND_BRAIN_SCAN_PLAN.md
  2ND_BRAIN_NOTE_TEMPLATES.md
research/
  RESEARCH_QUEUE.md
  PAPER_READING_PROTOCOL.md
  SOURCE_QUALITY_RULES.md
experiments/
  EXPERIMENT_PLAN.md
  EVALS_AND_BENCHMARKS.md
prompts/
  CODEX_PLAN_PROMPT.md
  CODEX_GOAL_PROMPT.md
  GPT_PRO_REVIEW_PROMPT.md
templates/
  PROJECT_STATUS.md
  EXPERIMENT_REPORT.md
  RESEARCH_NOTE.md
ops/
  STATUS_LOG_TEMPLATE.md
  SAFE_WORKFLOW.md
```

## 핵심 원칙

- 기억은 원문 재독이 아니라 **상태 변화**입니다.
- 2nd brain은 사용자의 지식 유전체입니다. Codex는 이를 무단 수정하지 않고, 새 노트/요약/링크/상태 변형 로그를 안전한 위치에 작성합니다.
- LPSF-v0.1은 새 foundation model이 아니라 **외부 지형 상태 + LLM decoder + plasticity operator + eval loop**로 시작합니다.
- 양자/중력/후성유전 같은 표현은 초기 구현에서 은유로 쓰지 말고, 각각 `hypothesis superposition`, `attractor/energy scoring`, `expression gating/plasticity mark`로 작동 정의합니다.
- 모든 실험은 baseline과 비교해야 합니다: `LLM only`, `LLM + RAG`, `LLM + static memory`, `LLM + LPSF`.

