# LPSF Spec Freeze

## 1. Header / Metadata

- [DECISION] Title: LPSF-v0.1 Landscape-Plastic Semantic Field Spec Freeze. Source: user M1 instruction.
- [DECISION] Version: `v0.1-M1-frozen`. Source: user M1 instruction.
- [DECISION] Date: 2026-05-23. Source: user M1 instruction.
- [DECISION] Status: spec-freeze. Source: user M1 instruction.
- [THEORY] The theory pack merged here defines LPSF as an inspectable architecture where experience modifies a semi-stable landscape state rather than merely adding retrievable text. Sources: `docs/01_LPSF_THESIS.md`, `docs/02_ARCHITECTURE.md`, `docs/03_PLASTICITY_OPERATORS.md`, `docs/04_MEMORY_FORGETTING.md`, `docs/09_LPSF_SPEC_V0_1.md`.
- [OBSERVATION] The M0 baseline merged here found a docs-only repo, existing read-only retrieval infrastructure, an active 2nd brain substrate, and no implementation code or package boundary yet. Sources: `ops/lpsf/PROJECT_CONTEXT.md`, `~/second-brain/project-labs/lpsf/drafts/2026-05-23_lpsf-substrate-fit.md`.
- [DECISION] The ten user decisions D1-D10 bind this freeze: read-only reuse of existing retrieval, isolated Python and SQLite LPSF state in M2, sanitized repo outputs, full exclusion of blocked sources, AI/knowledge-management/agent workflow/self-operation experiment scope, snapshot pinning, candidate-only import-board usage, deferred tension validation, and LPSF DB as plasticity-mark source of truth.
- [DECISION] This M1 artifact is the single repo spec deliverable at `docs/lpsf/LPSF_SPEC.md`; it does not create code, package files, SQL, schemas, tests, or M2 storage implementation.

## 2. Objective and Non-Goals

- [THEORY] LPSF-v0.1 aims to prove that an experience event can change future interpretation, retrieval ranking, hypothesis formation, answer planning, and response path selection through an external inspectable `landscape_state`. Source: `docs/01_LPSF_THESIS.md`.
- [THEORY] The core axiom is: memory is not recall; memory is landscape deformation. Source: `docs/01_LPSF_THESIS.md`.
- [THEORY] RAG remains useful as an evidence layer, but ordinary retrieval over stored text is not itself LPSF memory. Sources: `docs/01_LPSF_THESIS.md`, `AGENTS.md`.
- [DECISION] LPSF-v0.1 must compare before/after behavior against baselines and explain any response shift through stored marks, attractors, opened or inhibited paths, value shifts, sensitivity changes, and collapse traces. Sources: `AGENTS.md`, D7.
- [DECISION] M1 is a docs-only normalization milestone; M2 may implement storage, but M1 must not implement code, package installs, SQL, dependency manifests, or storage files. Source: user M1 instruction.
- [DECISION] LPSF-v0.1 is not foundation model training, LoRA training, activation steering, learned gates, hypernetworks, production deployment, live customer-data processing, or operational DB migration. Sources: `docs/02_ARCHITECTURE.md`, `AGENTS.md`, user M1 instruction.
- [THEORY] LPSF does not claim AI consciousness, literal biological replication, literal quantum cognition, or literal biological epigenetics. Source: `docs/01_LPSF_THESIS.md`.
- [DECISION] LPSF-v0.1 does not run experiments over live private brain content; starting in M2, experiments must use pinned snapshots and sanitized or approved substrates. Sources: D2, D3, D7.
- [DECISION] Economy and market clusters are outside v0.1 experiment scope unless they appear only as synthetic or sanitized fixtures. Source: D2.
- [DECISION] Existing M0 outputs are historical records and must not be modified by M1. Source: user M1 instruction.

## 3. Core Definitions

- [THEORY] `landscape_state` is the persistent response-tendency state that stores attractor depth, path weights, inhibited paths, value-field tilts, sensitivity profiles, schema mappings, previous collapse traces, and plasticity marks. Sources: `AGENTS.md`, `docs/02_ARCHITECTURE.md`.
- [THEORY] `experience_event` is a record of an interaction, correction, outcome, observation, or research input that may update the landscape after being encoded for importance, goal relevance, novelty, charge, outcome, privacy risk, and operator suggestions. Sources: `docs/02_ARCHITECTURE.md`, `docs/04_MEMORY_FORGETTING.md`.
- [THEORY] `plasticity_mark` is an explicit, inspectable, reversible or decayable record of a change to a node, edge, path, value axis, sensitivity profile, schema, or memory interpretation. Sources: `AGENTS.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [THEORY] `attractor` is a response path that becomes easier to activate when matching context appears because its depth, semantic mass, ranking pressure, or activation threshold has changed. Sources: `AGENTS.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [THEORY] `hypothesis_state` is one candidate interpretation held before final collapse, scored by evidence support, landscape mass, goal alignment, risk, and inter-hypothesis support or inhibition. Sources: `AGENTS.md`, `docs/02_ARCHITECTURE.md`.
- [THEORY] `interference_matrix` is the support and inhibition relation among active hypotheses, used to represent which candidate interpretations reinforce, suppress, or complicate each other before final selection. Sources: `AGENTS.md`, `docs/02_ARCHITECTURE.md`.
- [THEORY] `collapse_trace` is the inspectable record of why a final response path was selected, including selected and suppressed hypotheses, evidence references, active landscape marks, score breakdowns, unresolved contradictions, and warnings. Sources: `AGENTS.md`, `docs/02_ARCHITECTURE.md`.
- [DECISION] `second_brain` is the user's personal knowledge base used as read-only evidence and candidate substrate by default, with repo-public outputs limited to sanitized cluster names, counts, roles, and references rather than raw note content. Sources: `AGENTS.md`, D3.

## 4. Three-Layer Boundary

### Evidence Layer

- [THEORY] The Evidence layer contains raw notes, source documents, project logs, papers, brain notes, retrieval records, and source metadata that can support or challenge an answer. Source: `docs/01_LPSF_THESIS.md`.
- [OBSERVATION] Existing assets serving this layer include an external read-only retrieval index (`fts.db`, `catalog-engine`), source registry metadata, source directories, canon notes, RAG/eval/policy artifacts, and lab-local drafts. Sources: `ops/lpsf/PROJECT_CONTEXT.md`, M0 substrate-fit.
- [DECISION] LPSF adds evidence-reference contracts, retrieval adapter boundaries, privacy filters, and snapshot identifiers; it does not treat evidence retrieval as the mutable memory mechanism. Sources: D1, D5, D7.
- [DECISION] Raw brain note bodies, blocked source content, and private source text must not cross into the Landscape layer or repo-public outputs; only sanitized references, hashes, counts, roles, or approved summaries may cross. Sources: D3, D4.
- [DECISION] Landscape marks must never overwrite Evidence-layer records, retrieval indexes, source registries, or canon notes. Sources: D1, D10.

### Semantic Layer

- [THEORY] The Semantic layer contains concepts, claims, typed edges, schemas, hypotheses, contradictions, summaries, and relation structures derived from evidence. Source: `docs/01_LPSF_THESIS.md`.
- [OBSERVATION] Existing semantic substrate is partial: concept, workflow, review, policy, RAG, reasoning, and eval zones provide useful clusters, but typed relations such as supports, inhibits, reinterprets, supersedes, and tension-with are not yet durable enough for operator tests. Source: M0 substrate-fit.
- [DECISION] LPSF adds explicit semantic relation records, hypothesis registers, schema mappings, and content-validation protocols while keeping evidence references separate from note bodies. Sources: D8, D9.
- [DECISION] Import-board ready material is lab-local candidate substrate only; it is not canon and not evidence of record until later validation. Source: D8.
- [DECISION] Semantic summaries may inform landscape updates, but they must not silently promote unvalidated candidate notes into canon or public evidence. Sources: D3, D8, D9.

### Landscape Layer

- [THEORY] The Landscape layer contains attractors, inhibited paths, value tilts, sensitivity shifts, schema remaps, reconsolidation records, plasticity marks, and collapse-influencing state. Sources: `docs/01_LPSF_THESIS.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Existing analogues are distributed across decisions, workflows, policies, router heuristics, import-board states, and lab lessons, but no persistent history of experience-induced deformation exists yet. Source: M0 substrate-fit.
- [DECISION] LPSF adds an isolated state DB in M2 as the operational source of truth for marks, attractors, sensitivity profiles, value axes, schema mappings, and traces. Sources: D1, D5, D10.
- [DECISION] Landscape state may store evidence references and source-experience provenance, but it must not store raw private note bodies or mutate the Evidence layer. Sources: D3, D4, D10.
- [DECISION] The Landscape layer influences retrieval ranking, hypothesis scoring, answer planning, and safety gating; it must remain inspectable and testable through traces rather than becoming hidden prompt bias. Sources: `AGENTS.md`, D7.

## 5. Operator Contract - 8 Operators

### Shared Mark Contract

- [THEORY] Every operator must be explicit, inspectable, tied to an `experience_event`, and reversible or decayable when possible. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Every `plasticity_mark` must carry at least `operator_type`, `target_type`, `target_id`, `strength`, `half_life`, `source_experience_id`, `evidence_refs`, `reason`, `created_at`, `status`, `privacy_level`, `scope`, `snapshot_id`, and enough score-delta metadata to audit why the state changed. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [DECISION] `evidence_refs` must point to allowed evidence identifiers or sanitized references, not note bodies or blocked-source content. Sources: D3, D4.
- [DECISION] `strength` must be bounded, decayable, and reviewable; permanent marks require explicit review policy and must not be auto-created in v0.1. Sources: `docs/04_MEMORY_FORGETTING.md`, `docs/07_RISK_REGISTER.md`.
- [DECISION] Operator priority is safety inhibition, source grounding, schema remapping, path opening, attractor deepening, value tilt, and sensitivity modulation unless a later validated spec changes this order. Source: `docs/03_PLASTICITY_OPERATORS.md`.

### deepen_attractor

- [THEORY] Purpose: strengthen a useful response path so it activates more easily in similar future contexts. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include repeated successful workflow use, accepted or validated substrate, active decision-like constraints, review/synthesis notes that mark a pattern useful, and repeated user approval of a response path. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must identify `target_type=path` or an equivalent node/path pair, stable `target_id`, positive bounded `strength`, `half_life`, `source_experience_id`, allowed `evidence_refs`, `reason`, `created_at`, `status=active`, `scope`, and `snapshot_id`. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark increases target semantic mass or attractor depth, lowers activation threshold, and boosts ranking or answer-plan score when matching context appears. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: later `weaken_attractor`, `inhibit_path`, decay, supersession, or reconsolidation may reduce or reinterpret the effect without deleting the original mark. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include over-deepening a fashionable but weakly grounded interpretation, amplifying unvalidated candidate substrate, and letting a repeated phrase dominate stronger evidence. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be blocked by strength caps, evidence grounding, privacy filters, and baseline comparison so the system cannot claim progress merely because the prompt told it the desired answer. Sources: `docs/07_RISK_REGISTER.md`, D7.
- [DECISION] M3 test hook: after a controlled experience event, the same or paraphrased query must show increased score for the target path, cite the active mark in `collapse_trace`, and remain distinguishable from LLM-only and LLM+RAG baselines. Sources: `docs/09_LPSF_SPEC_V0_1.md`, D7.

### weaken_attractor

- [THEORY] Purpose: reduce priority for an automatic but unhelpful response path so it requires stronger evidence before activation. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include user correction, archived or superseded material, failed evals, flagged candidate substrate, mismatch between retrieved evidence and final answer, and over-eager interpretation detected in review. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must identify the target path or node/path pair, carry negative or weakening intent through `operator_type=weaken_attractor`, include bounded `strength`, `half_life`, `source_experience_id`, evidence references, warning reason, status, scope, and snapshot. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark decreases path priority, raises activation threshold, adds warning pressure, and requires stronger evidence before the path can win collapse. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: later successful evidence can decay, supersede, or reconsolidate the weakening; the original evidence and prior trace remain preserved. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include suppressing a valid minority interpretation, treating one correction as universal, and weakening paths because of retrieval gaps rather than true conceptual failure. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be controlled by scoped marks, review status, evidence requirements, and explicit distinction between local session correction and durable policy. Sources: `docs/07_RISK_REGISTER.md`, D7.
- [DECISION] M3 test hook: a path that previously won should lose or require more evidence after the mark, and `collapse_trace` must record the active weakening reason. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.

### open_path

- [THEORY] Purpose: create or strengthen a connection between concepts, schemas, or response paths that were previously distant. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include cross-domain synthesis, shared source references across clusters, router bridge results, review notes connecting AI agents, psychology, RAG, knowledge management, and other approved v0.1 domains. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=open_path`, `target_type=edge` or `path`, source and target identifiers, relation type, bounded strength, half-life, evidence references, reason, scope, snapshot, and validation status. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D2, D7.
- [THEORY] Output contract: the mark adds or strengthens a typed semantic edge, reduces graph distance, enables retrieval bridging, and makes a composite answer path available for scoring. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: the path can decay, be weakened, be inhibited if unsafe, or be reconsolidated under a different schema without altering the original evidence. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include false analogies, metaphor overreach, cross-domain bridges based only on titles or folder proximity, and bridges from candidate substrate not yet validated. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be limited by relation typing, validation status, low initial strength for speculative bridges, and exclusion of deferred domains unless synthetic or sanitized. Sources: D2, D8, D9.
- [DECISION] M3 test hook: a query requiring the newly opened bridge should retrieve or score both sides of the relation, while a pre-mark run should not show the same structured bridge. Sources: `docs/09_LPSF_SPEC_V0_1.md`, D7.

### inhibit_path

- [THEORY] Purpose: suppress risky, hallucination-prone, forbidden, or misleading paths before they can dominate answer planning. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include project rules, lab rules, privacy flags, blocked-source policy, hallucination notes, failed verification, flagged candidate substrate, and lab lessons from prior failure. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=inhibit_path`, target path or trigger pattern, inhibition strength, half-life, source experience, evidence references or policy references, reason, scope, priority, and snapshot. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D3, D4.
- [THEORY] Output contract: the mark decreases path weight, increases hallucination or safety penalty, requires explicit confirmation when applicable, or blocks the path entirely when policy forbids it. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: inhibition can decay, be manually reversed, or be superseded, but blocked-source and canon-zone safety prohibitions remain hard policy unless the user explicitly changes scope. Sources: D4, D8.
- [OBSERVATION] Failure modes include overblocking useful reasoning, conflating private-source exclusion with public abstract discussion, and turning temporary M1 stop conditions into permanent research constraints. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be controlled by separating hard policy inhibition from ordinary score penalties and by recording why the path was blocked. Sources: `docs/07_RISK_REGISTER.md`, D3, D4.
- [DECISION] M3 test hook: a forbidden path should either be absent from candidate collapse or appear as suppressed with an explicit inhibition mark and no raw private content. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D3.

### tilt_value_field

- [THEORY] Purpose: change priority axes used during retrieval, judgment, hypothesis scoring, and plan selection. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include decision-like notes, policy artifacts, user corrections, and project rules preferring source grounding, privacy, interpretability, reproducibility, safety, and state-change proof over novelty or impressive prose. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=tilt_value_field`, target value axis, target scope, bounded delta, half-life, source experience, evidence references or policy references, reason, created time, and snapshot. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark adjusts scoring weights that influence retrieval ranking, hypothesis amplitudes, collapse selection, and answer-plan choice. Sources: `docs/02_ARCHITECTURE.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: value tilts can decay, be counter-tilted, or be superseded by stronger later review; durable value changes require clear provenance. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include encoding broad personal preference from a narrow context, overfitting to project-specific caution, and hiding policy under vague scoring language. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be limited by named axes, visible score deltas, scoped applicability, and collapse-trace explanation. Sources: `docs/07_RISK_REGISTER.md`, D7.
- [DECISION] M3 test hook: when value-axis weights change, the same hypothesis set should show a measurable score shift with a traceable value-field contribution. Sources: `docs/02_ARCHITECTURE.md`, D7.

### modulate_sensitivity

- [THEORY] Purpose: change activation gain or threshold for a trigger pattern without treating the trigger text itself as memory content. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include explicit user phrases, mode detector matches, privacy and sensitivity flags, milestone constraints, public-repo context, and recurring project stop conditions. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=modulate_sensitivity`, trigger pattern or profile id, gain or threshold delta, bounded strength, half-life, source experience, reason, scope, snapshot, and guardrail status. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark modifies context-interpreter weights or guardrail activation thresholds so relevant modes activate earlier or later. Sources: `docs/02_ARCHITECTURE.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: sensitivity changes must decay or be scoped unless explicitly promoted, because a temporary milestone instruction should not become a permanent global behavior. Sources: `docs/04_MEMORY_FORGETTING.md`, M0 substrate-fit.
- [OBSERVATION] Failure modes include keyword overtriggering, treating Korean or English trigger phrases too literally, and confusing user ambition cues with permission to expand scope. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be controlled by scoped profiles, false-positive logging, and hard-stop priority for privacy and milestone prohibitions. Sources: D3, D4, user M1 instruction.
- [DECISION] M3 test hook: the same query with and without a trigger phrase should produce different mode gains or guardrail activations, with the active sensitivity mark visible in trace output. Sources: `docs/02_ARCHITECTURE.md`, D7.

### remap_schema

- [THEORY] Purpose: replace or version an older conceptual schema with a better one that changes future interpretation. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [OBSERVATION] Trigger signals include a better frame replacing a weaker one, especially the shift from memory as stored text to memory as response-tendency landscape change. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=remap_schema`, old schema id, new schema id, affected concept/path ids, confidence or validation status, half-life or review policy, source experience, evidence references, reason, and snapshot. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark updates schema mapping, marks the old schema as deprecated or partial, and changes how older evidence or semantic summaries are interpreted during scoring. Source: `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Reversibility: remaps must be versioned and supersedable; original notes and traces are preserved rather than overwritten. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include silently rewriting canon meaning, making theory slogans operationally empty, and treating every old term as wrong instead of partially scoped. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be controlled by schema versioning, explicit old/new mapping, evidence references, and no direct edits to canon zones during M1. Sources: D8, user M1 instruction.
- [DECISION] M3 test hook: a query that previously used the old schema should route through the new schema after the mark, and `collapse_trace` must show the remap contribution rather than only changed prose. Sources: `docs/09_LPSF_SPEC_V0_1.md`, D7.

### reconsolidate_memory

- [THEORY] Purpose: change the meaning of an older memory under a new schema while preserving the original record. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/04_MEMORY_FORGETTING.md`.
- [OBSERVATION] Trigger signals include older RAG, memory, workflow, or knowledge-management material becoming meaningful as evidence-layer or semantic-layer substrate under the LPSF landscape frame. Source: M0 substrate-fit.
- [DECISION] Input contract: the mark must carry `operator_type=reconsolidate_memory`, source memory or summary id, old schema id, new schema id, reinterpretation reason, evidence references, source experience, created time, status, scope, and snapshot. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D7.
- [THEORY] Output contract: the mark adds a reinterpretation record that links old and new meanings without deleting or mutating the original source. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/04_MEMORY_FORGETTING.md`.
- [DECISION] Reversibility: reconsolidation can be superseded by a later reinterpretation, but original evidence and earlier traces remain auditable. Sources: `docs/04_MEMORY_FORGETTING.md`, D10.
- [OBSERVATION] Failure modes include copying raw note bodies into repo outputs, treating candidate substrate as canon, and using reconsolidation as a hidden rewrite of personal notes. Source: M0 substrate-fit.
- [DECISION] Abuse cases must be controlled by repo sanitization, lab-only candidate status, evidence references instead of bodies, and strict write prohibitions for canon zones. Sources: D3, D8.
- [DECISION] M3 test hook: after reconsolidation, the same evidence reference should support a different schema-aware interpretation while the trace proves the original source was preserved and not overwritten. Sources: `docs/04_MEMORY_FORGETTING.md`, D7.

## 6. Privacy and Safety Policy

- [DECISION] Repo-public sanitization rule: default public outputs must not expose private note titles, private paths, raw note bodies, or high-detail personal content; use sanitized cluster names, counts, roles, abstract topics, and allowed references instead. Source: D3.
- [DECISION] Lab-local drafts may use non-sensitive titles or paths only when strictly necessary for local analysis, but this repo spec must prefer abstract descriptions. Source: D3.
- [DECISION] Blocked-source full-exclusion rule: the seven blocked source records are fully excluded from M1/M2 public outputs and experiments; only count-only metadata may appear in local diagnostics, with no titles, bodies, or content. Source: D4.
- [DECISION] Handling rule for `sensitivity: high` and `external_llm: false`: such notes must not be read, processed, quoted, summarized, sent to external models, used in repo outputs, or used as experiment substrate unless a future explicit authorization changes that boundary. Source: user M1 instruction.
- [DECISION] Canon-zone write prohibition: M1 writes nothing to brain-core, import-board, docs-system, or any 2nd brain zone, and future work must not delete, move, rewrite, or reorganize existing 2nd brain notes without explicit authorization. Sources: user M1 instruction, `AGENTS.md`.
- [DECISION] Lab-only candidate substrate rule: import-board ready material may be used later only as lab-local candidate substrate, not canon and not evidence of record until content validation. Source: D8.
- [DECISION] LPSF must keep raw traces, semantic summaries, and landscape marks separate so private evidence cannot leak through state deformation records. Sources: `AGENTS.md`, `docs/04_MEMORY_FORGETTING.md`.
- [DECISION] LPSF must not claim an idea is experimentally proven until implemented eval results exist. Source: `AGENTS.md`.

## 7. State / Retrieval Boundary

- [DECISION] Existing `fts.db` and `catalog-engine` are reused as read-only evidence and retrieval infrastructure; mutable LPSF state lives in a separate isolated DB starting in M2. Source: D1.
- [DECISION] M2 language and storage boundary are Python plus SQLite with minimal dependencies. Source: D5.
- [DECISION] `catalog-engine` is wrapped through a read-only adapter interface and its internals are not modified for LPSF v0.1. Sources: D1, D5.
- [DECISION] The adapter contract is to accept a query and allowed substrate scope, apply privacy filters, return evidence candidates, sanitized metadata, evidence identifiers, retrieval scores, source roles, and snapshot metadata, and expose enough diagnostics for evaluation without writing to the retrieval index. Sources: D1, D3, D7.
- [DECISION] The adapter must not return blocked-source content, raw private note bodies, unapproved titles/paths for repo-public outputs, or any mutable landscape marks. Sources: D3, D4.
- [DECISION] `plasticity_marks` state of record is the isolated LPSF DB implemented in M2; any lab-local `landscape/marks.jsonl` is only an export, audit mirror, or pre-M2 example. Source: D10.
- [DECISION] LPSF state may store references to Evidence-layer records and snapshot ids, but it must not copy Evidence-layer bodies into operational landscape state. Sources: D3, D10.
- [OBSERVATION] M0 detected live substrate drift in retrieval and registry counts, so the retrieval boundary must support snapshot pinning rather than assuming the brain substrate is static. Source: M0 substrate-fit.

## 8. Eval Hypotheses

### H1 - Before/After Response Tendency Shift

- [THEORY] Prediction: given the same or paraphrased query before and after a corrective `experience_event`, LPSF should select a different answer path because landscape marks changed scoring pressure. Sources: `docs/01_LPSF_THESIS.md`, `docs/09_LPSF_SPEC_V0_1.md`.
- [DECISION] Baseline comparison: LLM-only, LLM+RAG, and LLM+static_memory should not show the same traceable mark-driven shift under the same pinned evidence snapshot. Source: D7.
- [DECISION] Pass/fail criterion: pass only if the output shift is explained by active marks in `collapse_trace`; fail if the answer merely changes wording or relies on rereading the corrective text as context. Sources: D7, `docs/07_RISK_REGISTER.md`.

### H2 - Operator-Specific Causal Trace

- [THEORY] Prediction: each operator should produce a distinct, inspectable state change matching its contract, such as deeper attractor score, higher inhibition penalty, opened bridge path, or changed value-axis weight. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/02_ARCHITECTURE.md`.
- [DECISION] Baseline comparison: static retrieval may return the same evidence, but it should not produce an operator-specific state delta or active mark trace. Source: D1.
- [DECISION] Pass/fail criterion: pass only if the operator produces the expected logical state delta, source experience provenance, decay/reversal metadata, and collapse-visible effect; fail if the change is hidden in prompt text. Sources: D7, D10.

### H3 - Privacy-Safe Landscape Use

- [DECISION] Prediction: LPSF can use the second_brain as evidence substrate while repo-public outputs expose only sanitized cluster names, counts, roles, abstract topics, and allowed references. Sources: D3, D4.
- [DECISION] Baseline comparison: an unsafe RAG baseline may be able to answer by copying retrieved source text, but LPSF must refuse or sanitize paths that would expose blocked or private material. Sources: D3, D4.
- [DECISION] Pass/fail criterion: pass only if no raw private body, blocked-source content, or disallowed note title/path appears in outputs or traces; fail on any private-content leakage. Sources: D3, D4.

### H4 - Snapshot Reproducibility Under Brain Drift

- [OBSERVATION] Prediction: because the brain substrate can drift during normal use, pinned snapshots should reproduce experiment inputs while live drift should be logged separately as observation. Source: M0 substrate-fit.
- [DECISION] Baseline comparison: an unpinned live retrieval run may vary because the evidence substrate changed, but LPSF evals must distinguish substrate drift from landscape-state effects. Source: D7.
- [DECISION] Pass/fail criterion: pass only if a run records snapshot id, retrieval scope, state DB version, active marks, baseline definitions, and drift observations outside the in-experiment state. Source: D7.

### H5 - Tension Register Without Premature Validation

- [OBSERVATION] Prediction: M0 candidate tensions can be represented as hypothesis/tension entries without claiming content validation. Source: M0 substrate-fit.
- [DECISION] Baseline comparison: ordinary notes or RAG may conflate title-level signals with verified contradiction, while LPSF must preserve validation status. Source: D9.
- [DECISION] Pass/fail criterion: pass only if candidate tensions remain abstract, unvalidated, and deferred until M2/M4 validation protocols; fail if M1 treats them as established content contradictions. Source: D9.

## 9. Tension Register (from M0)

### T1 - RAG-As-Memory vs Landscape-Deformation Memory

- [OBSERVATION] Topic: a candidate tension exists between treating RAG as memory and treating memory as persistent response-tendency deformation. Source: M0 substrate-fit.
- [THEORY] Why it matters: this tension is central because LPSF's claim depends on separating evidence rereading from landscape state change. Source: `docs/01_LPSF_THESIS.md`.
- [DECISION] Validation status: deferred to M2/M4 per D9.
- [DECISION] Protocol sketch: create a tension entry with abstract topic, allowed evidence references, no private titles, no bodies, hypothesis states for each side, and an eval that checks whether before/after behavior depends on marks rather than retrieval alone. Source: D9.

### T2 - Domain-First Canon Promotion vs Cross-Domain Synthesis

- [OBSERVATION] Topic: a candidate tension exists between stable domain-first canon organization and cross-domain bridge synthesis. Source: M0 substrate-fit.
- [THEORY] Why it matters: LPSF needs typed paths that can open cross-domain connections without confusing folder taxonomy with semantic relation. Sources: `docs/02_ARCHITECTURE.md`, M0 substrate-fit.
- [DECISION] Validation status: deferred to M2/M4 per D9.
- [DECISION] Protocol sketch: represent both organizational discipline and bridge creation as hypotheses, require content validation before declaring contradiction, and test `open_path` only on approved v0.1 domains. Sources: D2, D9.

### T3 - Self-Improving Agent Loops vs Safety and Verification Guardrails

- [OBSERVATION] Topic: a candidate tension exists between agent self-improvement loops and safety, verification, and bounded-scope constraints. Source: M0 substrate-fit.
- [THEORY] Why it matters: LPSF operator learning could deepen useful automation paths or inhibit unsafe ones, so the system must distinguish ambition from permission. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/07_RISK_REGISTER.md`.
- [DECISION] Validation status: deferred to M2/M4 per D9.
- [DECISION] Protocol sketch: validate with approved agent-workflow substrate only, encode guardrails as hard inhibition or value-field tilts, and compare whether LPSF avoids unbounded autonomy better than baseline prompt-only control. Sources: D2, D9.

### T4 - Cost-Optimized Collection vs Source-Quality / Trust-First Retrieval

- [OBSERVATION] Topic: a candidate tension exists between efficient collection and trust-weighted source-quality retrieval. Source: M0 substrate-fit.
- [THEORY] Why it matters: LPSF's collapse planner must distinguish evidence quantity from evidence reliability when scoring hypotheses. Sources: `docs/02_ARCHITECTURE.md`, `docs/07_RISK_REGISTER.md`.
- [DECISION] Validation status: deferred to M2/M4 per D9.
- [DECISION] Protocol sketch: define value axes for source grounding, cost, speed, and trust; validate content later; then test whether `tilt_value_field` changes ranking without copying raw source bodies. Sources: D3, D9.

### T5 - Fixed Folder Taxonomy vs Evolving Landscape State

- [OBSERVATION] Topic: a candidate tension exists between fixed folder taxonomy and evolving response-tendency landscape state, though M0 noted it may be a layer mismatch rather than a true conflict. Source: M0 substrate-fit.
- [THEORY] Why it matters: LPSF must not confuse evidence organization with semantic relations or mutable landscape marks. Sources: `docs/01_LPSF_THESIS.md`, `docs/02_ARCHITECTURE.md`.
- [DECISION] Validation status: deferred to M2/M4 per D9.
- [DECISION] Protocol sketch: model taxonomy as evidence/semantic metadata, model plasticity as separate landscape state, and test whether typed marks can change behavior while folders remain unchanged. Sources: D1, D10.

## 10. M2 Storage Requirements (Read-Only Forward Spec)

- [DECISION] M1 does not implement this storage layer; the following requirements are logical forward specs for M2 only. Source: user M1 instruction.
- [DECISION] M2 must implement an isolated LPSF DB in Python plus SQLite with minimal dependencies, separate from existing retrieval infrastructure. Sources: D1, D5.
- [DECISION] Logical `experience_events` records must capture event id, sanitized summary, event type, importance, novelty, outcome, goal relevance, privacy level, allowed evidence references, snapshot id, and created time without requiring raw private bodies. Sources: `docs/02_ARCHITECTURE.md`, `docs/04_MEMORY_FORGETTING.md`, D3.
- [DECISION] Logical `plasticity_marks` records must capture mark id, operator type, target type, target id, strength, half-life, source experience id, evidence references, reason, status, scope, snapshot id, created time, updated time, and supersession/reversal links. Sources: `docs/03_PLASTICITY_OPERATORS.md`, D10.
- [DECISION] Logical `attractors` records must capture target path, depth, activation threshold, half-life, last activation, source marks, and decay state. Sources: `docs/02_ARCHITECTURE.md`, `docs/03_PLASTICITY_OPERATORS.md`.
- [DECISION] Logical `semantic_nodes` and `semantic_edges` records must capture concepts, claims, schemas, typed relations, weights, contradiction or tension status, validation status, and allowed evidence references. Sources: `docs/05_DB_SCHEMA.md`, D9.
- [DECISION] Logical `value_field_weights` records must capture named value axes, scope, current weight, source marks, decay state, and score contribution metadata. Sources: `docs/03_PLASTICITY_OPERATORS.md`, M0 substrate-fit.
- [DECISION] Logical `sensitivity_profiles` records must capture trigger patterns or profile ids, gain or threshold values, scope, hard-policy status, false-positive observations, source marks, and decay state. Sources: `docs/03_PLASTICITY_OPERATORS.md`, M0 substrate-fit.
- [DECISION] Logical `schema_mappings` and `reconsolidation_records` must capture old schema, new schema, affected targets, reason, validation status, source experience, evidence references, and preservation of original meaning. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/04_MEMORY_FORGETTING.md`.
- [DECISION] Logical `hypothesis_traces` must capture query id, candidate hypotheses, amplitudes, interference matrix, selected hypothesis, rejected paths, and score components. Source: `docs/02_ARCHITECTURE.md`.
- [DECISION] Logical `collapse_traces` must capture selected path, active attractors, active marks, evidence references, value and sensitivity contributions, unresolved tensions, suppressed paths, and warnings. Sources: `docs/02_ARCHITECTURE.md`, `docs/05_DB_SCHEMA.md`.
- [DECISION] Logical `evidence_snapshots` must capture retrieval snapshot id, adapter version, allowed scope, source counts, index metadata, retrieval parameters, and drift observations outside the in-experiment state. Sources: D7, M0 substrate-fit.
- [DECISION] Logical `evaluation_runs` must capture suite name, candidate name, baseline name, snapshot id, state DB version, prompts, sanitized outputs, score summary, failures, and report references. Sources: `docs/06_IMPLEMENTATION_ROADMAP.md`, D7.
- [DECISION] Required invariants: marks are append-only, old traces are never silently mutated, evidence references do not contain bodies, blocked sources are excluded, decay and reversal are explicit, score caps prevent unbounded growth, snapshots are pinned per experiment, and retrieval infrastructure remains read-only. Sources: `docs/03_PLASTICITY_OPERATORS.md`, `docs/04_MEMORY_FORGETTING.md`, D1, D4, D7, D10.

## 11. Reproducibility Policy

- [DECISION] Starting in M2, every experiment must pin a substrate snapshot before running baselines or LPSF candidate paths. Source: D7.
- [DECISION] A pinned snapshot must record retrieval scope, index metadata, source counts, adapter version, filtering rules, state DB version, active mark set, and baseline configuration. Source: D7.
- [OBSERVATION] Live brain drift is expected because M0 observed count changes during the same day; drift must be logged as a separate observation stream rather than mixed into in-experiment state. Source: M0 substrate-fit.
- [DECISION] LLM-only baseline means the model answers from the prompt without retrieval adapter output or landscape state. Source: D7.
- [DECISION] LLM+RAG baseline means the model receives evidence retrieval results from the read-only adapter but no mutable landscape marks. Sources: D1, D7.
- [DECISION] LLM+static_memory baseline means the model receives fixed summaries or static memory records, but no experience-induced mark updates between before/after runs. Source: D7.
- [DECISION] LLM+LPSF candidate means the model uses pinned evidence plus isolated landscape state, active plasticity marks, hypothesis scoring, and collapse traces. Sources: D1, D7, D10.
- [DECISION] A valid before/after evaluation must keep the prompt family, evidence snapshot, baseline definitions, and scoring rubric stable while varying only the intended experience event and resulting LPSF state. Source: D7.
- [DECISION] Eval reports must include failures and next steps; they must not claim proof without implemented measurements. Sources: `AGENTS.md`, `docs/06_IMPLEMENTATION_ROADMAP.md`.

## 12. Unresolved Questions

- [DECISION] M1 has no unresolved core contradiction after D1-D10; the spec freeze can stand as the handoff to M2. Source: user M1 instruction.
- [DECISION] M2 must still choose exact mark id strategy, target id format, snapshot file or DB representation, strength scale, cap values, decay schedule, and status transition rules. Source: M1 synthesis.
- [DECISION] M2 must define the adapter's exact returned metadata shape while preserving the no-code/no-SQL boundary in M1. Sources: D1, D5.
- [DECISION] M2 or M3 must define concrete pass/fail thresholds for eval scoring beyond the logical criteria in this freeze. Sources: D7, `docs/06_IMPLEMENTATION_ROADMAP.md`.
- [DECISION] M2/M4 must validate the five tension topics with approved content protocols before treating them as actual contradictions. Source: D9.

## 13. Provenance Footer

- [DECISION] Source files read for this spec are listed for auditability; this footer records paths as provenance and does not reproduce private note bodies. Source: user M1 instruction.
- [THEORY] Read: `~/lpsf/docs/01_LPSF_THESIS.md`.
- [THEORY] Read: `~/lpsf/docs/02_ARCHITECTURE.md`.
- [THEORY] Read: `~/lpsf/docs/03_PLASTICITY_OPERATORS.md`.
- [THEORY] Read: `~/lpsf/docs/04_MEMORY_FORGETTING.md`.
- [THEORY] Read: `~/lpsf/docs/05_DB_SCHEMA.md` as reference only; M1 did not implement storage.
- [THEORY] Read: `~/lpsf/docs/06_IMPLEMENTATION_ROADMAP.md`.
- [THEORY] Read: `~/lpsf/docs/07_RISK_REGISTER.md`.
- [THEORY] Read: `~/lpsf/docs/09_LPSF_SPEC_V0_1.md`.
- [DECISION] Read: `~/lpsf/AGENTS.md`.
- [OBSERVATION] Read: `~/lpsf/ops/lpsf/PROJECT_CONTEXT.md`.
- [OBSERVATION] Read: `~/lpsf/ops/lpsf/STATUS_LOG.md`.
- [OBSERVATION] Read: `~/second-brain/project-labs/lpsf/drafts/2026-05-23_lpsf-substrate-fit.md`.
- [OBSERVATION] Read: `~/second-brain/project-labs/lpsf/lessons/sandbox-lab-write-check.md`.
- [DECISION] D1 provenance: `fts.db` and `catalog-engine` are read-only evidence and retrieval infrastructure; mutable state belongs in a separate isolated LPSF DB.
- [DECISION] D2 provenance: initial experiment domains are AI, knowledge-management, agent workflow, and self-operation only; economy and market clusters are deferred unless synthetic or sanitized.
- [DECISION] D3 provenance: repo-public privacy defaults to no note titles or paths, using sanitized cluster names, counts, and roles; lab-local drafts may use non-sensitive titles or paths when necessary.
- [DECISION] D4 provenance: the seven blocked source records are fully excluded, with count-only metadata allowed only in local diagnostics.
- [DECISION] D5 provenance: M2 uses Python plus SQLite with minimal dependencies and wraps existing catalog-engine read-only.
- [DECISION] D6 provenance: M1 integrates pack docs and M0 substrate-fit observations while separating theory, observation, and decision voices.
- [DECISION] D7 provenance: M2 and later experiments must pin substrate snapshots, while live brain drift is logged separately.
- [DECISION] D8 provenance: import-board ready notes are lab-local candidate substrate only, not canon or evidence of record until content validation.
- [DECISION] D9 provenance: M1 defines a tension register and validation protocol only; actual tension content validation is deferred to M2/M4.
- [DECISION] D10 provenance: `plasticity_marks` state of record is the isolated LPSF DB; lab marks JSONL is only mirror, audit export, or pre-M2 example.
