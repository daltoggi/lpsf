# Safe Workflow

## Default Mode

Work locally, inspectably, and reversibly.

## Before Writing Code

- Read AGENTS.md.
- Read PLANS.md.
- Inspect repo.
- Identify tests.
- Identify safe write paths.
- Identify secrets and exclude them.
- Identify 2nd brain access status.

## Before Reading 2nd Brain

- Confirm path.
- Check exclusion rules.
- Start metadata-only.
- Avoid raw private content.

## Before Writing 2nd Brain

- Write only to draft folder.
- Do not modify existing notes.
- Prefer summaries and links.
- Mark generated notes as draft.

## Before Running Commands

Pause if command:

- installs packages;
- accesses network;
- deploys;
- deletes/moves files;
- modifies home directory broadly;
- touches secrets.

## Before Committing

Check:

```bash
git status
```

Review for:

- raw private notes;
- secrets;
- large generated data;
- accidental `.env`;
- private 2nd brain paths;
- unsupported claims.

