# Codex Config Example

This is a markdown note, not a config file. Copy relevant snippets into Codex config only if appropriate.

## Enable Goals

```toml
[features]
goals = true
```

Alternatively:

```bash
codex features enable goals
```

## Suggested Project Memory Files

Keep durable project memory in markdown:

```text
AGENTS.md
PLANS.md
ops/lpsf/STATUS_LOG.md
ops/lpsf/PROJECT_CONTEXT.md
docs/lpsf/LPSF_SPEC.md
experiments/lpsf/EVALUATION_REPORT.md
```

## Suggested Local Environment Variables

Use `.env.local` or your shell. Do not commit it.

```bash
SECOND_BRAIN_DIR="/path/to/your/obsidian/vault"
LPSF_DATA_DIR=".data/lpsf"
LPSF_DRAFT_DIR="second_brain_drafts/lpsf"
```

## Do Not Commit

```text
.env
.env.local
.data/
*.sqlite
*.db
raw_private_notes/
```

