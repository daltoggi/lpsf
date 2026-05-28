# Codex Goal Setup for LPSF

## Purpose

Use Codex Goal mode to let Codex work through setup, repo analysis, 2nd brain inventory, implementation, experiments, evaluation, and documentation without needing a new instruction after every step.

## Enable Goals

If `/goal` is not available, enable it in Codex config:

```toml
[features]
goals = true
```

Or run:

```bash
codex features enable goals
```

## Recommended Startup Sequence

### 1. Open Project

Open the repo/project folder in Codex.

### 2. Ask for Plan First

Paste:

```text
/plan Read README.md, AGENTS.md, PLANS.md, and docs/lpsf if present. Inspect the repo structure and identify the safest plan for implementing LPSF-v0.1. Do not modify files yet except a draft plan/status note if needed.
```

### 3. Confirm Safe Boundaries

Ensure Codex has identified:

- repo structure;
- build/test commands;
- writable folders;
- 2nd brain path status;
- do-not-touch paths;
- sensitive data boundaries.

### 4. Start Goal

Use `GOAL_LPSF_V0_1.md`.

## Goal Mode Rules

A good goal must include:

1. One durable objective.
2. Verifiable stopping condition.
3. Files to read first.
4. Commands/artifacts that prove progress.
5. Safety constraints.
6. Checkpoint logging requirement.

## Progress Log Requirement

Codex must update:

```text
ops/lpsf/STATUS_LOG.md
```

After each checkpoint.

## Stop or Pause Conditions

Codex must pause if:

- it needs to install packages;
- it needs to access private/sensitive notes;
- it is about to write outside approved paths;
- it detects secrets;
- it wants to delete/move existing files;
- it cannot verify progress.

