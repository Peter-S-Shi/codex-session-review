# Codex Session Review

A lightweight Skill for reviewing Codex development sessions, reconstructing how work was performed, extracting token usage, identifying avoidable inefficiencies, and producing repeatable reports that can be compared over time.

> **Recommended: use the included `usage/prompt-generator.html` before running this Skill.**  
> It helps define the analysis name, analysis scope, Codex session location, session/project selection, output location, report depth, previous report, and optional special focus with less ambiguity and less agent-side discovery work.

## What This Skill Is For

`codex-session-review` turns one or more Codex session records into a structured engineering review.

The V1 goal is deliberately simple:

> Convert Codex session history into reliable evidence, then answer four practical questions:
>
> 1. How was the work actually carried out?
> 2. Where were time, context, interaction, or token costs concentrated?
> 3. Which parts of the workflow were effective and worth keeping?
> 4. What should change in the next development cycle?

The Skill is designed for iterative AI-assisted development, including milestone-based workflows, hardening work, debugging, verification, and project-level retrospective analysis.

## Current Scope

### Sessions that can be analyzed

V1 analyzes **Codex sessions only**.

The agent executing this Skill does **not** need to be Codex. Any compatible agent capable of using the Skill and accessing the required local files may execute the workflow.

Future versions may add support for additional agent-session formats. Provider expansion is intentionally outside the V1 scope.

### Supported analysis units

The Skill supports three analysis scopes:

1. **Single Session**  
   Review one named Codex session.

2. **Selected Sessions**  
   Review a user-selected set of sessions that may be non-contiguous.

3. **Entire Project**  
   Resolve the Codex sessions associated with one project/session group and review them together.

Names are used to locate candidates. **The resolved Codex thread/rollout ID tied to the named session is the authoritative V1 analysis identity.** Raw Codex metadata may also expose a root `session_id`; preserve both when present. Ambiguous matches must not be silently guessed.

## Recommended Workflow

For the fastest and least ambiguous use:

1. Open **`usage/prompt-generator.html`**.
2. Give the analysis a name.
3. Choose the analysis scope.
4. Specify the session or project names you want reviewed.
5. Declare whether the Codex session storage path is unchanged or customized.
6. Choose one output root directory.
7. Optionally choose report length, previous report, report language, or special focus.
8. Generate the prompt and give it to the agent running this Skill.

If you prefer to write the request manually, see **`usage/demo-prompt.md`**.

### Why declare paths in advance?

The Skill recommends that users state whether the Codex session storage location has been changed.

- If it has **not** been changed, the agent should use the standard Codex session location without spending effort rediscovering it.
- If it **has** been changed, the user should provide the custom location before analysis.

The same principle applies to analysis output. Users are encouraged to provide one output root directory in advance so the Skill does not need to infer where cleaned data and reports should be stored.

## Required Analysis Inputs

A normal V1 analysis should establish:

- **Analysis Name**
- **Analysis Scope**
  - Single Session
  - Selected Sessions
  - Entire Project
- **Session or Project Selection**
- **Codex Session Storage**
  - default location, or
  - explicit custom location
- **Analysis Output Root**

Optional inputs include:

- Report length: `Brief`, `Standard`, or `Deep`
- Previous report for comparison
- Report language
- Special focus

Unless the user explicitly requests otherwise, the final analysis report is written in **English**.

## Output Structure

The user provides one analysis output root. The Skill organizes derived files under it.

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

### Analysis manifest

The manifest provides a stable record of what was actually analyzed. It should preserve metadata such as:

```text
analysis_name
analysis_scope
user-provided session/project labels
resolved_session_ids
session dates where available
analysis date
skill/analyzer version
report length
previous report reference
```

This makes later comparisons more reliable and prevents a report title from becoming a substitute for the real underlying Session IDs.

## Session Resolution Rules

Session names are useful for discovery, but they are not durable identity.

For V1, the ID resolved through Codex naming/index metadata and tied to the rollout file is the authoritative record identity. The cleaner may additionally preserve a root `session_id` from raw session metadata when Codex provides one.

The expected resolution flow is:

```text
User-provided name
→ candidate session discovery
→ metadata check / disambiguation
→ resolved Codex Session ID (thread/rollout ID)
→ final analysis scope
```

For an Entire Project review:

```text
Project/session-group label
→ candidate sessions
→ resolve ambiguities
→ unique Session ID set
→ analysis manifest
→ cleaning
→ analysis
```

When the local Codex state exposes a canonical project assignment, prefer that project name/ID relationship for candidate grouping. For older or unassigned sessions, fall back to available naming, working-directory, and session metadata as discovery evidence.

The Skill must not silently include an ambiguous session simply because its name looks related.

## Session Cleaning

V1 includes a batch-cleaning script:

```text
scripts/clean_codex_sessions.py
```

Its purpose is to transform raw Codex session records into a smaller, analysis-friendly representation.

The cleaning layer should preserve useful evidence such as:

- timestamps
- user messages
- assistant messages
- meaningful tool or command activity
- important tool-result summaries
- errors
- retries
- relevant session metadata
- token-usage evidence

It should filter low-value machine noise that does not materially help the review.

The raw Codex session files remain **read-only inputs**.

## Token Usage

Token consumption is a first-class V1 analysis dimension.

The cleaner/parser should automatically extract and calculate token usage whenever the source records provide reliable evidence.

Where available, the review may include:

- input tokens
- cached-input or cache-related usage
- cache-write input usage, when exposed
- output tokens
- reasoning usage
- cumulative or total usage
- per-session usage
- combined usage across selected sessions

Fields that cannot be derived reliably must be reported as unavailable rather than estimated.

Token numbers are not treated as meaningful in isolation. The review should connect token usage with observable workflow behavior, such as:

- repeated context loading
- repeated repository exploration
- unnecessary interaction loops
- failed or repeated execution
- repeated verification
- avoidable rework

## V1 Analysis Framework

The first version intentionally uses a small, general framework rather than a complicated software-engineering maturity model.

The core dimensions are:

1. **Task Framing**
2. **Context Efficiency**
3. **Execution Efficiency**
4. **Interaction Overhead**
5. **Verification Efficiency**
6. **Rework & Failure**
7. **Token Consumption**

The detailed rules live in:

```text
references/analysis-framework.md
```

The framework can become more sophisticated in future versions without requiring the entire Skill to be redesigned.

## Report Structure

Reports follow a consistent structure so that multiple reviews can be compared over time.

A standard report includes:

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

Each important judgment should distinguish:

```text
Evidence
→ Interpretation
→ Impact
→ Recommendation
```

This keeps observed session facts separate from analytical conclusions.

The detailed report contract lives in:

```text
references/report-template.md
```

## Longitudinal Review

A review may optionally reference a previous report.

When a previous report is supplied, the new analysis should distinguish:

- improved
- unchanged
- regressed
- newly observed

This turns the Skill from a one-time session summarizer into a lightweight development-habit tracking system.

## Candidate Development Principles

A report may propose reusable development principles when the evidence supports them.

These are **candidates**, not automatic rules.

For example:

```text
Candidate Development Principle:
Use targeted regression checks before repeating the full test suite when the change scope is narrow.
```

A candidate becomes a long-term principle only after explicit user approval.

The Skill must not automatically convert one session observation into a permanent development rule.

## Privacy and Safety

V1 follows several strict boundaries:

- Raw Codex session files are read-only.
- The Skill does not modify, rename, move, truncate, or delete source session records.
- Ambiguous session identity is reported rather than guessed.
- Cleaned records and reports are written only to the user-designated output location.
- Examples in this repository use neutral placeholders instead of personal project names or private filesystem layouts.
- Unavailable token or metadata fields are not fabricated.
- Analytical interpretation must remain distinguishable from source evidence.

Because cleaned session files and reports may contain development conversation content, users should treat the output directory as potentially private.

## Repository Structure

```text
codex-session-review/
├── README.md
├── SKILL.md
├── scripts/
│   └── clean_codex_sessions.py
├── references/
│   ├── analysis-framework.md
│   └── report-template.md
└── usage/
    ├── demo-prompt.md
    └── prompt-generator.html
```

### File responsibilities

- `README.md` — human-facing overview and recommended usage
- `SKILL.md` — agent-facing workflow contract
- `scripts/clean_codex_sessions.py` — session resolution support, batch cleaning, and token extraction
- `references/analysis-framework.md` — V1 efficiency-analysis criteria
- `references/report-template.md` — stable report structure and comparison contract
- `usage/demo-prompt.md` — privacy-neutral manual prompt example
- `usage/prompt-generator.html` — **recommended** offline prompt-generation interface

## Design Principles

V1 is intentionally small.

It should:

- solve the full minimum useful workflow
- avoid unnecessary databases or services
- keep source evidence immutable
- separate data cleaning from analytical judgment
- prefer explicit user-provided scope over agent rediscovery
- use stable Session IDs after name-based discovery
- support one session, selected sessions, and project-level analysis
- produce reports that remain useful in later comparisons
- allow the analysis framework to evolve without rebuilding the entire Skill

It should not become a general agent-observability platform in V1.

## Planned Evolution

Possible future versions may add:

- additional agent-session providers
- richer workflow metrics
- more advanced context-engineering analysis
- stronger loop-engineering diagnostics
- more sophisticated token-efficiency attribution
- automated cross-project comparisons
- richer longitudinal trend analysis

These are future extensions, not V1 requirements.

---

**Recommended first step:** open `usage/prompt-generator.html`, define the analysis clearly, and let the Skill handle the rest.
