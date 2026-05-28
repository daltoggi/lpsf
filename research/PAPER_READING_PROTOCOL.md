# Paper Reading Protocol

## Purpose

Prevent hallucinated research summaries and convert papers into LPSF implementation decisions.

## Reading Levels

### Level 0 — Metadata Only

Use when source is queued but not read.

Required:

```text
title
authors
year
URL/DOI
why queued
```

### Level 1 — Abstract + Skim

Required:

```text
main claim
method
why relevant
uncertainty
```

### Level 2 — Implementation Extraction

Required:

```text
operator implication
architecture implication
eval implication
risks
```

### Level 3 — Deep Review

Required:

```text
formalism
assumptions
failure cases
comparison to LPSF
pseudo-implementation
```

## Claim Discipline

Separate:

```text
Paper says:
I infer:
LPSF can use:
LPSF must not claim:
```

## Anti-Hallucination Rule

Never cite a source that was not opened/read. If source details are missing, mark as:

```text
status: unverified
```

## Output Template

Use `templates/RESEARCH_NOTE.md`.

