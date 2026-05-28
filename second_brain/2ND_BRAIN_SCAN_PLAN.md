# 2nd Brain Scan Plan

## Goal

Create a safe, high-level map of the user's 2nd brain so LPSF can use it as knowledge substrate without leaking or damaging it.

## Step 1 — Locate

Look for configuration in this order:

1. `SECOND_BRAIN_DIR` env var.
2. `.env.local` key `SECOND_BRAIN_DIR`.
3. `config/second_brain.*`.
4. User-provided path in Codex thread.
5. Common Obsidian vault locations only after permission.

Do not guess and scan home directories broadly.

## Step 2 — Identify Format

Detect:

- markdown vault;
- Obsidian frontmatter;
- tags;
- backlinks;
- attachments;
- folder taxonomy;
- Dataview fields;
- index/MOC notes.

## Step 3 — Build Safe Inventory

Inventory only metadata first:

```text
path
title
tags
frontmatter keys
last modified
word count
sensitivity guess
```

## Step 4 — Exclusion Rules

Exclude or mask by default:

```text
/private
/diary
/journal
/people
/finance
/medical
/secrets
/passwords
```

Also exclude notes with tags:

```text
#private
#sensitive
#secret
#diary
#medical
#finance
```

## Step 5 — Relevance Clustering

Identify clusters related to:

- LPSF;
- state-space landscape plasticity;
- RAG;
- 2nd brain;
- LLM architecture;
- cognition;
- epigenetics;
- memory;
- semantic field;
- world model;
- 4DGS if relevant;
- Codex workflows.

## Step 6 — Draft Summary

Write:

```text
second_brain_drafts/lpsf/2ND_BRAIN_INVENTORY_SUMMARY.md
```

Do not include raw private content.

## Step 7 — Build Index

Create a local private index if repo structure permits:

```text
.data/lpsf/second_brain_index.jsonl
.data/lpsf/second_brain_sources.sqlite
```

Do not commit `.data/` unless the user explicitly wants it.

## Step 8 — Write Draft Notes

Only under:

```text
<SECOND_BRAIN_DIR>/00_Inbox/LPSF/Codex-Drafts/
```

Draft files:

```text
YYYY-MM-DD LPSF Project Context.md
YYYY-MM-DD LPSF Research Queue.md
YYYY-MM-DD LPSF Experiment Results.md
YYYY-MM-DD LPSF Reconsolidation Suggestions.md
```

