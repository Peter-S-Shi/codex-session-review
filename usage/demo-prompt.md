# Demo Prompt

## Recommended Use

This file provides privacy-neutral prompt examples for `codex-session-review`.

For most users, the preferred entry point is:

```text
usage/prompt-generator.html
```

The generator helps define the required fields consistently and reduces unnecessary agent-side discovery work.

Use this file when you prefer to write the request manually.

---

# 1. What to Decide Before Running the Skill

A normal request should define:

```text
Analysis Name
Analysis Scope
Session / Project Selection
Codex Session Storage
Analysis Output Root
```

Optional settings:

```text
Report Length
Previous Report
Report Language
Special Focus
```

Default report language:

```text
English
```

Default report length:

```text
Standard
```

---

# 2. Analysis Scope Options

Choose exactly one:

```text
Single Session
Selected Sessions
Entire Project
```

## Single Session

Use when reviewing one Codex session.

## Selected Sessions

Use when reviewing several specific sessions that may be non-contiguous.

## Entire Project

Use when reviewing all Codex sessions associated with one project/session group.

For Entire Project analysis, the project/session-group label is used only to discover candidates.

The Skill should resolve the final analysis scope to real Codex Session IDs (the named thread/rollout IDs used by V1) before cleaning or analysis.

---

# 3. Codex Session Storage

If you have not changed the Codex session storage location, say so explicitly.

Recommended wording:

```text
Codex session storage:
Default location. I have not changed it.
```

This avoids unnecessary rediscovery.

If you use a custom location:

```text
Codex session storage:
Custom location:
<codex-session-directory>
```

Use your real path only in your local prompt.

Do not replace it with a public example when running the Skill.

---

# 4. Analysis Output Root

Provide one root directory.

Recommended wording:

```text
Analysis output root:
<analysis-output-directory>
```

The Skill may create:

```text
<analysis-output-root>/
├── analysis-manifest.json
├── cleaned/
└── reports/
```

Cleaned session records and reports may contain private development conversation content.

Choose an appropriate private local directory.

---

# 5. Demo — Single Session

```text
Use the codex-session-review Skill.

Analysis Name:
Iteration Review 01

Analysis Scope:
Single Session

Session Selection:
Session Alpha

Codex Session Storage:
Default location. I have not changed it.

Analysis Output Root:
<analysis-output-directory>

Report Length:
Standard

Previous Report:
None

Report Language:
English

Special Focus:
Context efficiency and token consumption.

Resolve the real Codex Session ID before analysis.
Do not rely on the display name as final identity.

Clean the session record, extract reliable token usage programmatically, reconstruct the workflow, apply the V1 analysis framework, and generate the final report.
```

---

# 6. Demo — Selected Sessions

```text
Use the codex-session-review Skill.

Analysis Name:
Milestone Review 02

Analysis Scope:
Selected Sessions

Session Selection:
- Session Alpha
- Session Gamma
- Session Delta

Codex Session Storage:
Default location. I have not changed it.

Analysis Output Root:
<analysis-output-directory>

Report Length:
Standard

Previous Report:
<previous-report-path>

Report Language:
English

Special Focus:
Interaction overhead, repeated verification, and rework.

Resolve each requested session to its real Codex Session ID.
Deduplicate the final Session ID set before cleaning or analysis.

Clean all selected sessions, extract reliable token usage programmatically, compare session-level behavior, reconstruct the combined workflow, compare against the previous report where meaningful, and generate the final report.
```

---

# 7. Demo — Entire Project

```text
Use the codex-session-review Skill.

Analysis Name:
Project Alpha · Development Review

Analysis Scope:
Entire Project

Project / Session Group:
Project Alpha

Codex Session Storage:
Default location. I have not changed it.

Analysis Output Root:
<analysis-output-directory>

Report Length:
Deep

Previous Report:
None

Report Language:
English

Special Focus:
Project-level workflow efficiency, context reuse across sessions, token concentration, verification strategy, and avoidable rework.

First resolve the candidate Codex sessions associated with this project/session group.

Do not silently include ambiguous sessions.
Use resolved Codex Session IDs (the named thread/rollout IDs used by V1) as the final analysis scope.

After resolving the project session set:
1. clean the selected sessions;
2. extract reliable token usage programmatically;
3. reconstruct the project-level workflow across sessions;
4. preserve meaningful session-level differences;
5. apply the V1 analysis framework;
6. generate the final report;
7. propose Candidate Development Principles only when supported by evidence.

Do not convert Candidate Development Principles into long-term rules without explicit user approval.
```

---

# 8. Demo — Custom Codex Session Location

```text
Use the codex-session-review Skill.

Analysis Name:
Iteration Review 03

Analysis Scope:
Single Session

Session Selection:
Session Beta

Codex Session Storage:
Custom location:
<codex-session-directory>

Analysis Output Root:
<analysis-output-directory>

Report Length:
Brief

Previous Report:
None

Report Language:
English

Special Focus:
Token consumption and execution efficiency.

Use the supplied Codex session directory directly.
Do not spend time rediscovering the default Codex session location.

Resolve the real Session ID, clean the session, extract token usage, and generate a Brief report.
```

---

# 9. Minimal Prompt

Experienced users may use a shorter prompt.

```text
Use codex-session-review.

Analysis Name:
Iteration Review 04

Scope:
Selected Sessions

Sessions:
- Session Alpha
- Session Beta

Codex session storage:
Default and unchanged.

Output:
<analysis-output-directory>

Standard English report.

Focus:
Context efficiency and token consumption.
```

The Skill should infer the standard workflow from `SKILL.md`.

The user should not need to describe JSONL parsing details.

---

# 10. Prompt With Previous-Report Comparison

```text
Use the codex-session-review Skill.

Analysis Name:
Iteration Review 05

Analysis Scope:
Selected Sessions

Session Selection:
- Session Epsilon
- Session Zeta

Codex Session Storage:
Default location. I have not changed it.

Analysis Output Root:
<analysis-output-directory>

Report Length:
Standard

Previous Report:
<previous-report-path>

Report Language:
English

Special Focus:
Whether the workflow improved after the previous review.

Use the previous report as a comparison baseline.

For each V1 dimension, distinguish where meaningful:
- Improved
- Unchanged
- Regressed
- Newly Observed
- Not Comparable

Do not treat lower token usage alone as proof of improvement.
```

---

# 11. Prompt With User-Approved Memory Follow-Up

The initial review should only propose Candidate Development Principles.

Example review request:

```text
Use codex-session-review.

Analysis Name:
Iteration Review 06

Analysis Scope:
Single Session

Session Selection:
Session Theta

Codex Session Storage:
Default location. I have not changed it.

Analysis Output Root:
<analysis-output-directory>

Report Length:
Standard

Report Language:
English

At the end of the report, propose Candidate Development Principles when strongly supported by evidence.

Do not save or apply them automatically.
```

After reading the report, the user may separately approve specific candidates.

Example follow-up:

```text
I approve Candidate Development Principles 1 and 3.
Use them as long-term development principles where the current environment supports user-approved memory.
```

Approval should remain explicit and selective.

---

# 12. Recommended Prompt Style

Prefer prompts that are:

```text
short
explicit
scope-aware
path-aware
identity-safe
```

Good:

```text
Codex session storage:
Default and unchanged.
```

Less efficient:

```text
Please search my computer and figure out where Codex might store everything.
```

Good:

```text
Analysis Scope:
Selected Sessions

Sessions:
- Session Alpha
- Session Beta
```

Less reliable:

```text
Analyze some sessions that seem related.
```

Good:

```text
Analysis Name:
Milestone Review 02
```

Less useful:

```text
Just save the report somewhere sensible.
```

---

# 13. Privacy-Friendly Examples

Repository examples should use neutral placeholders such as:

```text
Project Alpha
Session Alpha
Session Beta
Iteration Review 01
<codex-session-directory>
<analysis-output-directory>
<previous-report-path>
```

Do not publish examples containing:

```text
real project names
private repository names
usernames
personal filesystem layouts
real Session IDs
```

Local users should replace placeholders with their own values when running the Skill.

---

# 14. Quick Checklist

Before sending your prompt, confirm:

- [ ] Analysis Name is present.
- [ ] Analysis Scope is one of the three supported values.
- [ ] Session or Project Selection is present.
- [ ] Codex session storage is declared as default/unchanged or custom.
- [ ] Analysis Output Root is provided.
- [ ] Report Length is set or allowed to default to Standard.
- [ ] Report Language is set or allowed to default to English.
- [ ] Previous Report is supplied when comparison is desired.
- [ ] Special Focus is optional and does not replace the standard V1 framework.
- [ ] Entire Project prompts require candidate resolution before analysis.
- [ ] Session names are discovery labels; real Session IDs remain authoritative.
