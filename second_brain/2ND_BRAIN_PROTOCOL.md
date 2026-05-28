# 2nd Brain Protocol for LPSF

## Definition

The user's 2nd brain is not just a document folder. In this project, it is treated as:

```text
personal knowledge substrate + evidence corpus + concept graph seed + long-term knowledge transmission medium
```

The goal is not to scrape it. The goal is to let LPSF learn from it safely.

## Operating Principle

```text
Read broadly.
Summarize safely.
Write narrowly.
Never destroy.
```

## Access Modes

### Mode 0 — No Access

If no 2nd brain path is available:

- create a placeholder inventory;
- ask for path/config only if necessary;
- continue with repo/docs-only prototype.

### Mode 1 — Read-Only Access

Allowed:

- scan filenames;
- scan tags/frontmatter;
- summarize high-level structure;
- build local private index;
- create sanitized project context.

Not allowed:

- modify notes;
- export raw notes;
- commit raw content.

### Mode 2 — Draft Write Access

Allowed only under:

```text
<SECOND_BRAIN_DIR>/00_Inbox/LPSF/Codex-Drafts/
```

Allowed writes:

- research note drafts;
- concept note drafts;
- decision logs;
- experiment summaries;
- reconsolidation suggestions.

### Mode 3 — Managed Write Access

Requires explicit user approval.

Allowed:

- update selected notes;
- add backlinks;
- move from drafts to permanent folders.

## Required Inventory Summary

Codex should create:

```text
second_brain_drafts/lpsf/2ND_BRAIN_INVENTORY_SUMMARY.md
```

Include:

```text
- detected root path
- note count by folder
- dominant tags
- LPSF-relevant clusters
- likely sensitive areas excluded
- candidate source notes
- missing context
- safe draft location
```

## Sensitive Content Policy

Do not include in project docs unless explicitly authorized:

- personal identifiers;
- private relationships;
- financial/private assets;
- medical/mental health details;
- passwords/API keys;
- raw diary-like entries;
- third-party private information.

Use abstract summaries instead.

## Note Writing Policy

When writing to 2nd brain, use these note types.

### Source Note

For papers, articles, official docs.

```markdown
# Source — <Title>

## Metadata
- Author:
- Year:
- URL/DOI:
- Source quality:
- Read status:

## Core Claims

## Evidence

## What LPSF Can Use

## What Not To Overclaim

## Links
```

### Concept Note

```markdown
# Concept — <Name>

## Definition

## Why It Matters To LPSF

## Related Concepts

## Open Questions

## Evidence Links
```

### Landscape Mark Note

```markdown
# Landscape Mark — <Short Name>

## Trigger

## Operator

## Target

## Strength

## Half-Life

## Reason

## Evidence

## Review Status
```

### Reconsolidation Note

```markdown
# Reconsolidation — <Old Idea> → <New Idea>

## Original Interpretation

## New Interpretation

## Why It Changed

## Source/Evidence

## Action
```

## 2nd Brain as RAG Input

Use 2nd brain as evidence, not authority. Retrieve it, but also judge:

```text
Is this current?
Is this private?
Is this a draft?
Is this contradicted by later notes?
Is this a stable belief or exploratory thought?
```

## 2nd Brain as LPSF Input

Extract:

```text
- recurring concepts
- unresolved contradictions
- user goals
- repeated failures
- preferred reasoning patterns
- project constraints
- stable value axes
- source-backed claims
```

Convert them into:

```text
concept_nodes
semantic_edges
value_axes
attractors
inhibited_paths
plasticity_marks
```

