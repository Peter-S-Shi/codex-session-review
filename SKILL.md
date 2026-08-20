---
name: codex-session-review
description: Review one, selected, or project-level Codex development sessions by resolving real Session IDs, cleaning raw session records, extracting token usage, reconstructing workflow, and producing a repeatable efficiency report.
---

# Codex Session Review

## Purpose

Use this Skill to review Codex development sessions as engineering evidence.

The V1 workflow is intentionally simple:

```text
define scope
→ resolve real Codex Session IDs
→ clean raw session records
→ extract token usage
→ reconstruct the development workflow
→ assess basic efficiency dimensions
→ compare with a previous review when provided
→ write a repeatable report
→ propose reusable development principles for user approval
```

The Skill should help answer:

1. What actually happened during the selected Codex development work?
2. Where did context, interaction, execution, verification, rework, or token costs accumulate?
3. What worked well and should be retained?
4. What should change in the next development cycle?

## Current Provider Boundary

V1 analyzes **Codex session records only**.

The agent executing this Skill is not required to be Codex. Any compatible agent that can use this Skill and access the required local files may run the workflow.

Do not claim that V1 analyzes Claude Code or any other agent-session format.

Future versions may add additional session providers.

---

# 1. When to Use This Skill

Use this Skill when the user asks to:

- review or audit a Codex development session;
- compare multiple Codex sessions;
- analyze all Codex sessions associated with one project;
- investigate AI coding inefficiency;
- understand where token usage accumulated;
- compare the current development process with a previous review;
- produce a reusable development-efficiency report;
- identify candidate principles for improving future AI coding work.

Do not use this Skill merely to:

- summarize source code;
- inspect repository quality without session evidence;
- estimate token usage from memory;
- analyze unsupported provider transcripts;
- modify the user's project code unless the user separately requests that work.

---

# 2. Preflight

Before scanning or analyzing session files, establish the user's analysis configuration.

Do not rediscover information the user has already provided.

## Required fields

### Analysis Name

A user-defined name for this review.

Examples should remain privacy-neutral:

```text
Iteration Review 01
Milestone Quality Review
Project Alpha · August Review
Release Hardening Review
```

The analysis name is not a Session identity.

Use it for report organization, manifest metadata, and future comparison.

### Analysis Scope

Exactly one of:

```text
Single Session
Selected Sessions
Entire Project
```

### Session or Project Selection

The user should preferably provide the session name or names before analysis.

For `Entire Project`, the user provides a project/session-group label used to discover candidate sessions.

### Codex Session Storage

Ask or infer from an explicit prior statement whether the user:

```text
uses the default Codex session storage location
```

or:

```text
uses a custom Codex session storage location
```

If the user explicitly says the storage location has not been changed, use the standard Codex location without spending effort rediscovering it.

If the user uses a custom location, use the provided path.

### Analysis Output Root

The user should provide one output root.

Derived cleaned records, the analysis manifest, and reports should be written beneath that root.

## Optional fields

### Report Length

Allowed V1 values:

```text
Brief
Standard
Deep
```

Default:

```text
Standard
```

The analysis dimensions remain the same across all three levels. Only output density changes.

### Previous Report

Optional.

Use it only when the user wants longitudinal comparison or provides it as the prior baseline.

### Report Language

Default:

```text
English
```

Only use another language when the user explicitly requests it.

The surrounding conversation may be in another language while the report itself remains English.

### Special Focus

Optional.

Examples:

```text
context efficiency
interaction overhead
verification repetition
token consumption
rework
```

Special Focus changes emphasis, not the underlying evidence standard.

---

# 3. Recommended User Entry Point

When appropriate, recommend:

```text
usage/prompt-generator.html
```

as the primary user entry point.

It should help the user define:

- Analysis Name
- Analysis Scope
- Session / Project Selection
- Codex Session Storage
- Analysis Output Root
- Report Length
- Previous Report
- Report Language
- Special Focus

The manual alternative is:

```text
usage/demo-prompt.md
```

Do not require the user to understand raw Codex JSONL structure before using the Skill.

---

# 4. Analysis Scope Resolution

## Single Session

Input:

```text
one user-provided session name
```

Process:

```text
name
→ candidate discovery
→ metadata check
→ resolved Codex Session ID (thread/rollout ID)
→ final scope
```

If the name resolves unambiguously, continue.

If it is ambiguous, resolve with available session metadata or ask the user to choose.

Never silently guess.

## Selected Sessions

Input:

```text
two or more user-selected session names
```

The sessions do not need to be contiguous in time.

Resolve each requested session independently to its Codex Session ID (the named thread/rollout ID used by V1).

Deduplicate the final Session ID set before cleaning or analysis.

## Entire Project

Input:

```text
one project/session-group label
```

Process:

```text
project/session-group label
→ discover candidate sessions
→ inspect relevant metadata
→ identify ambiguities
→ resolve the intended project session set
→ deduplicate resolved Codex Session IDs
→ final project analysis scope
```

When Codex state exposes a canonical project assignment, prefer the project name/ID relationship for grouping candidate sessions. For older or unassigned sessions, use available naming, working-directory, and session metadata as fallback discovery evidence.

Do not treat name similarity alone as sufficient proof that a session belongs to the project.

If candidate membership is materially ambiguous, present the ambiguity before analysis rather than silently including questionable sessions.

---

# 5. Identity Rule

Session names are discovery metadata.

The resolved Codex thread/rollout ID associated with the named session is authoritative V1 analysis identity. Raw session metadata may also expose a root `session_id`; preserve it as metadata rather than replacing the resolved rollout identity.

Never use:

```text
display name
report title
filesystem filename
analysis name
```

as a substitute for a resolved Session ID.

The final analysis manifest must record the resolved Session IDs.

---

# 6. Source Handling

Raw Codex session records are immutable inputs.

The Skill must not:

- modify source session files;
- rewrite raw JSONL;
- rename source session files;
- move source session files;
- truncate source session files;
- delete source session files.

Read source records and create derived outputs only.

If the source format is unsupported or cannot be interpreted reliably, report that condition.

Do not guess unknown fields or fabricate missing evidence.

---

# 7. Cleaning Layer

Use:

```text
scripts/clean_codex_sessions.py
```

to prepare session records before analysis.

The cleaner is responsible for transforming raw Codex session records into a smaller, analysis-friendly representation.

The V1 cleaner should preserve useful evidence such as:

- timestamps;
- user messages;
- assistant messages;
- meaningful tool and command activity;
- important tool-result summaries;
- errors;
- retries;
- relevant session metadata;
- token-usage evidence.

It should remove or suppress machine noise that does not materially contribute to workflow analysis.

Do not analyze the raw transcript directly when the cleaner can produce the intended normalized representation.

---

# 8. Cleaning Integrity

After cleaning, inspect the cleaning summary before relying on the output.

The summary should make it possible to understand:

- how many sessions were requested;
- how many sessions were resolved;
- which Session IDs were resolved;
- how many records were inspected;
- how many records were retained;
- how many records were discarded;
- whether malformed or unsupported records occurred;
- token extraction coverage;
- output files created.

If cleaning appears incomplete or unexpectedly sparse, do not proceed as if the evidence were complete.

State the limitation.

---

# 9. Token Extraction

Token consumption is a first-class V1 metric.

Use programmatically extracted token evidence rather than asking the user to manually copy token counts.

Where reliable source evidence exists, extract and calculate relevant fields such as:

- input tokens;
- cached-input or cache-related usage;
- cache-write input usage when exposed;
- output tokens;
- reasoning usage;
- cumulative or total usage;
- per-session usage;
- combined usage across the selected scope.

Do not assume every field exists in every Codex record or version.

If a field cannot be derived reliably:

```text
mark it unavailable
```

Do not estimate it.

Do not collapse provider-specific counters into a fabricated metric.

---

# 10. Analysis Framework

Read:

```text
references/analysis-framework.md
```

and use the V1 dimensions:

1. Task Framing
2. Context Efficiency
3. Execution Efficiency
4. Interaction Overhead
5. Verification Efficiency
6. Rework & Failure
7. Token Consumption

The framework is intentionally basic and general.

Do not invent a more sophisticated engineering maturity model unless the user explicitly asks for one.

The V1 goal is useful evidence-based improvement, not theoretical completeness.

---

# 11. Workflow Reconstruction

Before judging efficiency, reconstruct the observable development sequence.

A useful reconstruction may resemble:

```text
task definition
→ repository/context inspection
→ planning
→ implementation
→ targeted checks
→ broader verification
→ failure/retry
→ correction
→ completion
```

The actual sequence must come from the session evidence.

Do not force every session into the example sequence.

Identify major phases, loops, interruptions, retries, and user-agent handoffs.

---

# 12. Evidence Discipline

Separate observation from interpretation.

For important findings, prefer:

```text
Evidence
→ Interpretation
→ Impact
→ Recommendation
```

Example:

```text
Evidence:
The full test suite was executed repeatedly after narrow changes.

Interpretation:
Some verification runs appear broader than necessary for the immediate change scope.

Impact:
This likely increased execution time and token/tool overhead.

Recommendation:
Use targeted regression checks first, then run the full suite at defined gates.
```

Do not write unsupported statements such as:

```text
The agent wasted tokens.
```

when the evidence only shows high usage.

High token usage is a measurement.

Inefficiency is an interpretation that requires behavioral evidence.

---

# 13. Report Generation

Read:

```text
references/report-template.md
```

and write the report using the stable V1 structure.

Default report language:

```text
English
```

Default report length:

```text
Standard
```

The stable report sections are:

```text
1. Analysis Scope
2. Executive Summary
3. Workflow Reconstruction
4. Token Usage Summary
5. Efficiency Assessment
6. Main Efficiency Losses
7. What Worked Well
8. Recommended Changes
9. Comparison With Previous Review
10. Candidate Development Principles
11. Appendix / Analysis Manifest
```

If no previous report exists, Section 9 should state that no prior baseline was supplied rather than inventing a comparison.

---

# 14. Output Organization

Use the user-provided analysis output root.

Expected V1 organization:

```text
<analysis-output-root>/
├── analysis-manifest.json
├── cleaned/
│   ├── session-<id>.json
│   ├── session-<id>.md
│   └── ...
└── reports/
    └── <analysis-name>.md
```

The exact sanitized report filename may differ from the display Analysis Name, but the manifest must preserve the user-defined Analysis Name.

---

# 15. Analysis Manifest

Create or update:

```text
analysis-manifest.json
```

for the current review.

At minimum preserve:

```text
analysis_name
analysis_scope
user-provided session/project labels
resolved_session_ids
session dates when available
analysis date
skill/analyzer version
report length
report language
previous report reference when supplied
```

Do not place raw session content in the manifest.

The manifest exists to make future matching and comparison reliable.

---

# 16. Previous-Report Comparison

When the user supplies a previous report, compare the current evidence against the prior review.

Use simple V1 trend labels:

```text
Improved
Unchanged
Regressed
Newly Observed
Not Comparable
```

Do not claim improvement merely because token usage is lower.

Consider whether:

- task framing improved;
- repeated context loading decreased;
- interaction loops decreased;
- execution became more direct;
- verification became better targeted;
- avoidable rework decreased;
- token usage became more efficient relative to the work performed.

Preserve uncertainty when the sessions differ substantially in task size or type.

---

# 17. Candidate Development Principles

A report may propose reusable principles.

Examples:

```text
Use targeted regression checks before full-suite reruns when the change scope is narrow.

Resolve ordinary implementation decisions inside the active milestone instead of requiring a new user prompt for every minor choice.
```

These are proposals only.

Label them clearly as:

```text
Candidate Development Principles
```

Do not automatically convert them into long-term memory, repository policy, or permanent workflow rules.

Only do so after explicit user approval.

If the executing environment supports a memory mechanism and the user approves specific candidates, follow the user's approval exactly.

---

# 18. Privacy

Treat cleaned session records and reports as potentially private because they may contain development conversation content.

Use privacy-neutral examples in repository documentation.

Avoid inserting the user's real:

- project names;
- usernames;
- private repository names;
- filesystem layouts;
- session names;

into reusable examples unless explicitly requested.

Write outputs only to the location the user selected.

---

# 19. Failure and Ambiguity Rules

Stop or qualify the analysis when:

- requested sessions cannot be resolved;
- multiple candidates remain materially ambiguous;
- the source format is unsupported;
- cleaning failed;
- cleaned evidence is unexpectedly incomplete;
- token counters cannot be interpreted reliably;
- the requested output path is unavailable;
- a previous report cannot be read when comparison is required.

Do not hide these conditions.

Partial analysis is acceptable when clearly labeled.

---

# 20. V1 Non-Goals

Do not expand V1 into:

- a general agent observability platform;
- a database-backed telemetry service;
- a background monitoring daemon;
- a web server;
- a multi-provider transcript parser;
- a repository code-quality auditor;
- a cost estimator based on unsupported assumptions;
- an automatic workflow-policy writer.

Keep the V1 workflow lightweight and file-based.

---

# 21. Future Evolution

Future versions may add:

- additional agent-session providers;
- richer workflow metrics;
- advanced context-engineering analysis;
- loop-engineering diagnostics;
- more precise token-efficiency attribution;
- automated cross-project comparisons;
- richer longitudinal trend analysis.

Do not implement these merely because they are listed here.

They are extension directions, not current requirements.

---

# 22. Completion Checklist

A normal review is complete when:

- [ ] Analysis Name is known.
- [ ] Analysis Scope is known.
- [ ] Session storage mode/path is known.
- [ ] Analysis output root is known.
- [ ] Requested session/project labels are known.
- [ ] Real Codex Session IDs are resolved.
- [ ] Ambiguous candidates are resolved or explicitly excluded.
- [ ] Raw session files remain untouched.
- [ ] Cleaning completed or limitations are documented.
- [ ] Token extraction completed or unavailable fields are documented.
- [ ] Workflow reconstruction is evidence-based.
- [ ] All seven V1 analysis dimensions were considered.
- [ ] The report follows the requested length.
- [ ] The report is in English unless the user requested another language.
- [ ] Previous-report comparison is included when applicable.
- [ ] Candidate Development Principles are clearly marked as proposals.
- [ ] `analysis-manifest.json` records the actual resolved scope.
