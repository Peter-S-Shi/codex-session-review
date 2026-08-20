# Report Template

## Purpose

This document defines the stable V1 report structure for `codex-session-review`.

The report is designed to support:

- one-session reviews;
- selected multi-session reviews;
- entire-project session reviews;
- longitudinal comparison against a previous review;
- repeatable observation of AI coding workflow quality over time.

Unless the user explicitly requests another language, the final report must be written in **English**.

The report should remain concise enough to be useful, but detailed enough to preserve the evidence behind important conclusions.

---

# 1. Report Length Modes

V1 supports three output lengths:

```text
Brief
Standard
Deep
```

The analytical dimensions remain the same.

Only the amount of evidence, explanation, and secondary findings changes.

## Brief

Use when the user wants a fast retrospective.

Recommended characteristics:

- short executive summary;
- only the most important workflow reconstruction;
- compact token summary;
- 2–3 major findings;
- 2–3 recommendations;
- concise candidate principles;
- minimal appendix.

## Standard

Default mode.

Recommended characteristics:

- clear scope;
- concise workflow reconstruction;
- useful token breakdown;
- all seven analysis dimensions considered;
- 3–5 priority findings;
- practical recommendations;
- previous-report comparison when available;
- manifest appendix.

## Deep

Use when the user explicitly wants a detailed audit.

Recommended characteristics:

- more complete evidence;
- finer workflow reconstruction;
- session-by-session comparison;
- deeper cross-dimension interpretation;
- secondary findings;
- more detailed token discussion;
- expanded previous-report comparison;
- richer appendix.

Do not inflate the report merely because `Deep` was selected.

Additional length should provide additional evidence or insight.

---

# 2. Report Writing Rules

## 2.1 Evidence Discipline

Important findings should follow:

```text
Evidence
→ Interpretation
→ Impact
→ Recommendation
```

Not every paragraph must mechanically use these four labels, but the logic should remain visible.

## 2.2 Distinguish Fact From Interpretation

Use language such as:

```text
Observed
The session ran the same full verification command repeatedly.

Interpretation
Several runs appear broader than necessary for the immediately preceding change.
```

Avoid presenting uncertain explanations as proven fact.

## 2.3 Avoid Personality Judgments

Do not describe the agent as:

```text
lazy
careless
confused
bad
```

Describe workflow behavior instead.

## 2.4 Preserve Necessary Iteration

Do not classify all debugging or retry behavior as waste.

Distinguish:

```text
necessary iteration
avoidable rework
```

## 2.5 Token Usage Is Contextual

Do not equate:

```text
more tokens
```

with:

```text
worse performance
```

Interpret token usage together with task scale and observed workflow behavior.

---

# 3. Stable V1 Report Structure

Use the following sections in this order.

Sections may be shorter in Brief mode, but the structure should remain recognizable.

---

# Codex Session Efficiency Review

## 1. Analysis Scope

Record the analysis boundary.

Include:

```text
Analysis Name:
Analysis Scope:
Requested Session / Project Labels:
Resolved Session IDs:
Session Count:
Session Date Range:
Analysis Date:
Report Length:
Report Language:
Previous Report:
Special Focus:
```

Use `None`, `Not supplied`, or `Unavailable` when appropriate.

Do not omit resolved Session IDs from the report when they are available.

### Example

```text
Analysis Name: Project Alpha · Iteration Review 01
Analysis Scope: Selected Sessions
Requested Labels:
- Session Alpha
- Session Beta

Resolved Session IDs:
- <session-id-1>
- <session-id-2>

Session Count: 2
Session Date Range: <start> to <end>
Analysis Date: <date>
Report Length: Standard
Report Language: English
Previous Report: None
Special Focus: Context efficiency and token consumption
```

---

## 2. Executive Summary

Summarize the most important findings.

Recommended structure:

```text
Overall assessment:
<one short paragraph>

Most important findings:
1. ...
2. ...
3. ...

Highest-value next change:
...
```

For Brief mode, this section may carry most of the report's value.

For Standard and Deep modes, keep it concise and let later sections provide evidence.

---

## 3. Workflow Reconstruction

Reconstruct the observable development path.

Do not invent phases that are not visible in the session evidence.

Possible form:

```text
Task Definition
→ Context Inspection
→ Planning
→ Implementation
→ Targeted Verification
→ Failure / Retry
→ Correction
→ Full Verification
→ Completion
```

For multiple sessions, prefer session-level grouping where helpful.

Example:

```text
Session A
Purpose: architecture and implementation
Main flow:
...

Session B
Purpose: defect correction
Main flow:
...

Session C
Purpose: closure verification
Main flow:
...
```

Highlight:

- important loops;
- user-agent handoffs;
- replanning;
- major retries;
- verification gates;
- completion points.

---

## 4. Token Usage Summary

Summarize programmatically extracted token evidence.

Use only fields that are reliably available.

### Suggested table

| Session | Input | Cached Input | Cache Write | Output | Reasoning | Total / Cumulative | Coverage |
|---|---:|---:|---:|---:|---:|---:|---|
| <session-id-1> | ... | ... | ... | ... | ... | ... | Complete / Partial |
| <session-id-2> | ... | ... | ... | ... | ... | ... | Complete / Partial |
| Combined | ... | ... | ... | ... | ... | ... | ... |

If some token fields are unavailable, show:

```text
Unavailable
```

Do not estimate missing numbers.

### Interpretation

After the table, explain only the meaningful patterns.

Possible questions:

- Which session consumed the most tokens?
- Was that session also the largest or most complex?
- Did high usage coincide with repeated context loading?
- Did it coincide with repeated verification?
- Did it coincide with failed or repeated loops?
- Did later sessions become more efficient after earlier context was established?

Do not over-interpret raw totals.

---

## 5. Efficiency Assessment

Review all seven V1 dimensions.

For each dimension, use:

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Allowed status labels:

```text
Strong
Acceptable
Needs Improvement
Significant Concern
Insufficient Evidence
```

### 5.1 Task Framing

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- task clarity;
- scope stability;
- non-goals;
- definition of done;
- whether misunderstanding caused rework.

### 5.2 Context Efficiency

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- repeated file reads;
- repeated project rediscovery;
- overly broad inspection;
- repeated background explanation;
- use of durable project context.

### 5.3 Execution Efficiency

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- movement from understanding to useful action;
- repeated planning;
- tool calls that did not advance state;
- batching;
- autonomy.

### 5.4 Interaction Overhead

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- unnecessary user confirmations;
- repeated "continue" prompts;
- ordinary decisions escalated unnecessarily;
- user acting as message relay;
- fragmented task execution.

### 5.5 Verification Efficiency

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- targeted tests;
- repeated full-suite runs;
- duplicate verification;
- whether each rerun answered a new question;
- appropriate final gates.

### 5.6 Rework & Failure

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Where useful, classify observed rework as:

```text
Necessary Discovery
Avoidable Misunderstanding
Avoidable Execution Error
Avoidable Verification Loop
Scope Change
External / Environmental Failure
```

### 5.7 Token Consumption

```text
Status:
Evidence:
Assessment:
Impact:
Recommendation:
```

Focus on:

- high-consumption phases;
- concentration across sessions;
- relationship with context loading;
- relationship with interaction loops;
- relationship with verification;
- relationship with rework;
- whether usage appears proportionate to work performed.

---

## 6. Main Efficiency Losses

List only the highest-priority losses.

For a Standard report, prefer 3–5 findings.

Suggested structure:

### Finding 1 — <short title>

```text
Evidence:
...

Why it matters:
...

Likely upstream cause:
...

Recommended change:
...
```

Repeat as needed.

Prioritize findings that are:

- repeated;
- high-impact;
- well supported;
- actionable;
- likely to recur.

Do not turn this section into a list of every minor imperfection.

---

## 7. What Worked Well

Preserve successful workflow behavior.

Possible categories:

- clear initial framing;
- good milestone boundaries;
- efficient targeted search;
- strong autonomy;
- coherent batching;
- appropriate regression strategy;
- effective self-correction;
- disciplined scope control;
- strong completion verification.

Use evidence.

Suggested format:

```text
1. <successful behavior>
   Evidence:
   Why it should be retained:

2. ...
```

The report should help the user preserve good habits, not merely identify defects.

---

## 8. Recommended Changes

Convert findings into a small number of practical workflow changes.

Recommendations should be:

```text
specific
evidence-based
actionable
small enough to apply
```

Prefer:

```text
For narrow fixes, run the directly affected tests first and reserve the full suite for the batch completion gate.
```

Avoid:

```text
Use fewer tokens.
Be more efficient.
Plan better.
```

### Recommended format

| Priority | Change | Expected Benefit | Evidence Basis |
|---|---|---|---|
| High | ... | ... | ... |
| Medium | ... | ... | ... |
| Low | ... | ... | ... |

For Brief mode, this may be a short numbered list instead.

---

## 9. Comparison With Previous Review

If a previous report was supplied, compare the current review against it.

Allowed labels:

```text
Improved
Unchanged
Regressed
Newly Observed
Not Comparable
```

### Suggested table

| Dimension | Previous | Current | Trend | Evidence |
|---|---|---|---|---|
| Task Framing | ... | ... | Improved | ... |
| Context Efficiency | ... | ... | ... | ... |
| Execution Efficiency | ... | ... | ... | ... |
| Interaction Overhead | ... | ... | ... | ... |
| Verification Efficiency | ... | ... | ... | ... |
| Rework & Failure | ... | ... | ... | ... |
| Token Consumption | ... | ... | ... | ... |

Do not force a comparison when the task types differ too much.

Use `Not Comparable` when appropriate.

If no previous report was supplied, write:

```text
No previous review was supplied. This report becomes the baseline for future comparison.
```

---

## 10. Candidate Development Principles

List reusable principles that are supported strongly enough to consider keeping.

These are proposals only.

Suggested format:

### Candidate 1

```text
Principle:
<concise reusable rule>

Evidence:
<why this review supports it>

Expected future benefit:
<what problem it should reduce>

Status:
Proposed — requires explicit user approval
```

Repeat as needed.

Do not automatically convert candidates into permanent memory, project policy, or workflow rules.

---

## 11. Appendix / Analysis Manifest

Summarize the durable analysis metadata.

Suggested structure:

```text
Analysis Name:
Analysis Scope:
Requested Labels:
Resolved Session IDs:
Session Dates:
Analysis Date:
Analyzer / Skill Version:
Report Length:
Report Language:
Previous Report Reference:
Special Focus:
Cleaner Outputs:
Token Coverage:
Known Limitations:
```

The appendix should agree with:

```text
analysis-manifest.json
```

Do not place raw transcript content in the manifest appendix unless directly needed as evidence.

---

# 4. Multi-Session Reporting Rules

When more than one session is analyzed, the report should preserve both:

```text
session-level differences
+
combined project-level patterns
```

Do not collapse everything into one aggregate.

At minimum, identify:

- each resolved Session ID;
- each session's apparent purpose;
- token usage per session where available;
- notable workflow differences;
- repeated patterns across sessions;
- whether later sessions reused or rebuilt context.

For an Entire Project analysis, the report should explain the resolved project session set before presenting conclusions.

---

# 5. Entire Project Reporting Rules

For `Entire Project` scope:

1. state the project/session-group label supplied by the user;
2. note the canonical Codex project assignment when available;
3. list the resolved Session IDs;
4. note any candidates that were excluded because of ambiguity;
5. reconstruct project-level workflow across sessions;
6. identify repeated patterns rather than treating every session as unrelated;
7. provide combined token usage where supported;
8. preserve session-level outliers.

Do not silently include every similarly named session.

---

# 6. Brief Mode Skeleton

```text
# Codex Session Efficiency Review

## 1. Analysis Scope
...

## 2. Executive Summary
...

## 3. Workflow Reconstruction
...

## 4. Token Usage Summary
...

## 5. Efficiency Assessment
- Task Framing:
- Context Efficiency:
- Execution Efficiency:
- Interaction Overhead:
- Verification Efficiency:
- Rework & Failure:
- Token Consumption:

## 6. Main Efficiency Losses
1. ...
2. ...
3. ...

## 7. What Worked Well
...

## 8. Recommended Changes
1. ...
2. ...
3. ...

## 9. Comparison With Previous Review
...

## 10. Candidate Development Principles
...

## 11. Appendix / Analysis Manifest
...
```

---

# 7. Standard Mode Skeleton

```text
# Codex Session Efficiency Review

## 1. Analysis Scope

## 2. Executive Summary

## 3. Workflow Reconstruction

## 4. Token Usage Summary

## 5. Efficiency Assessment

### 5.1 Task Framing
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.2 Context Efficiency
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.3 Execution Efficiency
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.4 Interaction Overhead
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.5 Verification Efficiency
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.6 Rework & Failure
Status:
Evidence:
Assessment:
Impact:
Recommendation:

### 5.7 Token Consumption
Status:
Evidence:
Assessment:
Impact:
Recommendation:

## 6. Main Efficiency Losses

## 7. What Worked Well

## 8. Recommended Changes

## 9. Comparison With Previous Review

## 10. Candidate Development Principles

## 11. Appendix / Analysis Manifest
```

---

# 8. Deep Mode Additions

Deep mode keeps the Standard structure and may add:

- more detailed workflow timeline;
- session-by-session evidence;
- token concentration analysis;
- repeated command/test patterns;
- cross-dimension causal chains;
- secondary findings;
- longer previous-report comparison;
- more detailed known limitations.

Do not add new analytical dimensions merely because the report is Deep.

---

# 9. Known Limitations Section

When material limitations affect confidence, add a short subsection under the relevant section or appendix.

Examples:

```text
Known Limitation:
Token reasoning usage was unavailable for two sessions.

Known Limitation:
One requested session could not be resolved unambiguously and was excluded.

Known Limitation:
The cleaned transcript omitted unsupported record types.
```

Do not bury limitations.

---

# 10. Final Quality Check

Before writing the report to disk, verify:

- [ ] The report uses the user-defined Analysis Name.
- [ ] The correct Analysis Scope is stated.
- [ ] Resolved Session IDs are included.
- [ ] The report language follows the user's request; otherwise English is used.
- [ ] Report length matches Brief / Standard / Deep.
- [ ] Token values are programmatically sourced or marked unavailable.
- [ ] All seven V1 dimensions were considered.
- [ ] Important judgments distinguish evidence from interpretation.
- [ ] Necessary iteration is not mislabeled as waste.
- [ ] Main findings are prioritized rather than exhaustive.
- [ ] Successful workflow behavior is preserved.
- [ ] Recommendations are concrete and evidence-based.
- [ ] Previous-report comparison is included when applicable.
- [ ] Candidate Development Principles are marked as proposals.
- [ ] The appendix agrees with `analysis-manifest.json`.
- [ ] Known limitations are visible.
