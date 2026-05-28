# Codex Session Runbook

## Starting a New Thread

1. Open the project.
2. Check current repo state.
3. Run `/plan` before `/goal`.
4. Ask Codex to read `AGENTS.md` and this pack.
5. Start the goal only after it identifies safe boundaries.

## Required First Message

```text
Read AGENTS.md and PLANS.md. Treat this project as LPSF-v0.1: a state-space landscape plasticity prototype. Do not reduce it to ordinary RAG. Before writing code, inspect the repo and propose a plan with safety boundaries, validation steps, and 2nd brain handling.
```

## Checkpoint Review

At every checkpoint, Codex must show:

```text
Checkpoint:
Files changed:
Commands run:
Evidence of progress:
Risks:
Next:
Need permission?: yes/no
```

## When Codex Should Ask

Ask or pause when:

- 2nd brain path is ambiguous;
- existing notes would be modified;
- package installation is needed;
- external API calls are needed;
- secrets are detected;
- deployment is proposed;
- repo build/test commands are missing.

## When Codex Should Continue Without Asking

Continue when:

- writing docs under approved LPSF folders;
- creating test fixtures with synthetic data;
- implementing local-only modules;
- adding safe unit tests;
- updating status logs;
- creating draft notes under approved draft folder.

## Review Checklist

Before accepting Codex output:

- Did it preserve the LPSF distinction from RAG?
- Did it write/update status?
- Did it test or define how to test?
- Did it avoid raw private 2nd brain leakage?
- Did it explain failures?
- Did it compare baseline vs LPSF?

