# 01 — LPSF Thesis

## Name

**LPSF: Landscape-Plastic Semantic Field**

Korean name:

**지형가소성 의미장 모델**

## One-Line Thesis

LPSF is a language-cognitive architecture in which experience does not merely add retrievable information, but persistently changes the landscape that shapes future interpretation, retrieval, judgment, and action.

한국어:

> LPSF는 과거 정보를 다시 읽는 모델이 아니라, 경험 이후 상태공간 지형을 변형하고, 그 변형된 지형 위에서 해석·판단·행동 경로가 달라지는 모델입니다.

## Core Axiom

```text
Memory is not recall.
Memory is landscape deformation.
```

## Why Existing LLM/RAG Is Not Enough

Existing LLM/RAG systems can store or retrieve past text. That is useful, but it does not necessarily mean the system itself has changed.

LPSF focuses on the middle layer between fixed weights and short-term context:

```text
fixed pretrained weights
↓
semi-stable landscape state shaped by experience
↓
current context and response
```

The missing middle layer is the main research object.

## Dialectical Frame

### Thesis

LLMs are powerful fixed-weight sequence models. RAG improves access to stored knowledge by retrieving relevant external information.

### Antithesis

Human-like memory is not just retrieval. Experience changes tendencies: what feels important, which path activates, which interpretation is suppressed, which value axis tilts, and what becomes intuitive.

### Synthesis

LPSF keeps the LLM as a decoder/reasoner but adds an inspectable landscape state that can be modified by experience through plasticity operators.

## The Three-Layer Model

```text
1. Evidence Layer
   Raw notes, source documents, project logs, papers, 2nd brain notes.

2. Semantic Layer
   Concepts, claims, edges, hypotheses, contradictions, schemas.

3. Landscape Layer
   Attractors, inhibited paths, value tilts, sensitivity shifts, plasticity marks.
```

RAG mostly operates on layers 1 and 2. LPSF requires layer 3.

## What Counts As Real Progress

A system is closer to LPSF if:

1. The same input before/after experience produces a different response tendency.
2. The difference can be explained by stored landscape changes.
3. The model does not need to reread the original raw trace to show the changed tendency.
4. The change can decay, be reinforced, be inhibited, or be reconsolidated.
5. The system can distinguish raw recall from state change.

## What This Does Not Claim

LPSF does not claim:

- current LLMs are useless;
- RAG is useless;
- AI consciousness is solved;
- human brain replication is required;
- biological epigenetics is the literal answer;
- quantum physics is required.

LPSF claims a narrower but stronger point:

> AI systems need durable, inspectable mechanisms by which experience changes future response possibilities.

