# Analysis Framework

## Purpose

This document defines the V1 analysis framework for `codex-session-review`.

The framework is intentionally simple, general, and evidence-based.

Its purpose is not to judge whether an AI coding workflow is theoretically optimal. Its purpose is to identify practical improvement opportunities from real Codex session evidence.

The V1 review asks:

1. Was the task framed clearly enough before execution?
2. Was context used efficiently?
3. Did execution progress directly toward the goal?
4. Was human-agent interaction more frequent than necessary?
5. Was verification proportionate and well targeted?
6. How much avoidable rework occurred?
7. How were tokens consumed, and what observable workflow behavior helps explain that consumption?

The framework should remain useful even as future versions adopt more advanced ideas from software engineering, context engineering, loop engineering, agent observability, or evaluation research.

---

# 1. General Analysis Rules

## 1.1 Evidence First

Do not begin with a judgment.

Begin with observable session evidence.

Preferred reasoning structure:

```text
Evidence
→ Interpretation
→ Impact
→ Recommendation
```

Example:

```text
Evidence:
The same repository files were inspected repeatedly within a short span without an intervening change.

Interpretation:
Some context gathering appears redundant.

Impact:
This may have increased execution time and token consumption without materially improving task understanding.

Recommendation:
Reuse the already established repository map or inspect only files affected by the current change.
```

Avoid unsupported wording such as:

```text
The agent wasted tokens.
```

High token usage is evidence.

Waste is an interpretation that requires supporting workflow evidence.

---

## 1.2 Separate Facts From Inference

Use three confidence levels when useful:

```text
Directly Observed
Strongly Supported
Possible
```

Examples:

```text
Directly Observed:
The full test suite ran five times.

Strongly Supported:
Several of those runs appear broader than necessary for the narrow fixes immediately preceding them.

Possible:
Repeated full-suite execution contributed materially to the session's token and execution cost.
```

Do not present a possibility as a proven cause.

---

## 1.3 Analyze the Work, Not the Agent's Personality

Do not use language such as:

```text
lazy
confused
careless
bad at coding
```

Analyze observable workflow behavior instead:

```text
scope drift
repeated exploration
unnecessary interaction
duplicate verification
failed execution
avoidable rework
```

The goal is process improvement.

---

## 1.4 Preserve Necessary Iteration

Iteration is normal.

Do not classify every:

```text
test failure
debugging cycle
clarification
retry
revision
```

as inefficiency.

The review should distinguish:

```text
Necessary Iteration
vs.
Avoidable Rework
```

A failed test that reveals an unknown defect may be useful.

Repeatedly triggering the same known failure without changing the relevant conditions may indicate avoidable rework.

---

## 1.5 Consider Task Difficulty

Do not compare raw counts without context.

A large hardening milestone may legitimately consume more:

```text
tokens
tool calls
tests
messages
time
```

than a small documentation edit.

The key question is not:

> Was the session large?

It is:

> Was the resource use proportionate to the work and the uncertainty involved?

---

# 2. Workflow Reconstruction

Before scoring or recommending changes, reconstruct the major observable workflow.

Possible phases include:

```text
Task Definition
Repository / Context Inspection
Planning
Implementation
Targeted Verification
Broad Verification
Failure / Retry
Correction
Documentation
Completion
```

Do not force every session into this exact sequence.

Instead, identify:

- major phases;
- repeated loops;
- interruptions;
- user-agent handoffs;
- resets or replanning;
- verification gates;
- visible completion points.

For multiple sessions or an Entire Project review, also identify how work moved across sessions.

Example:

```text
Session A
→ architecture and implementation

Session B
→ defect correction

Session C
→ verification and closure
```

This reconstruction provides the context for all later judgments.

---

# 3. V1 Analysis Dimensions

V1 uses seven dimensions.

Each dimension should include:

```text
Observed Evidence
Assessment
Impact
Recommendation
```

Use qualitative judgment rather than pretending to calculate a mathematically precise score.

If a concise status label is useful, prefer:

```text
Strong
Acceptable
Needs Improvement
Significant Concern
Insufficient Evidence
```

---

# 4. Task Framing

## Core Question

> Did the agent have a sufficiently clear definition of the task, scope, constraints, and completion condition before substantial work began?

## Look For

Positive evidence:

- clear goal;
- explicit milestone or task boundary;
- explicit non-goals;
- clear acceptance criteria;
- known files or areas of focus;
- explicit permission boundaries;
- stable definition of done.

Potential inefficiency:

- substantial implementation begins before the goal is clear;
- repeated clarification of the same objective;
- major scope changes inside the session;
- user repeatedly corrects what the task was supposed to be;
- the agent solves adjacent problems not required by the task;
- completion criteria are invented late.

## Questions

Ask:

1. Was the objective clear before execution?
2. Was scope stable?
3. Did the agent know what not to do?
4. Was "done" recognizable?
5. Did misunderstanding create later rework?

## Typical Recommendation Patterns

Possible recommendations include:

- define milestone scope before execution;
- include explicit non-goals;
- specify the desired completion gate;
- provide acceptance criteria earlier;
- separate discovery work from implementation when uncertainty is high.

Do not recommend larger prompts merely because framing was weak.

Prefer the smallest additional information that would have prevented the ambiguity.

---

# 5. Context Efficiency

## Core Question

> Did the workflow use only the context needed to make reliable decisions?

## Look For

Positive evidence:

- targeted file reads;
- reuse of already established facts;
- reference to existing project documentation;
- narrow searches;
- progressive discovery based on uncertainty.

Potential inefficiency:

- repeated reading of unchanged files;
- repeatedly rebuilding the same repository map;
- reading large amounts of unrelated material;
- restating the same project background in multiple user prompts;
- repeatedly rediscovering known paths, commands, or constraints;
- loading full documents when a small relevant section would suffice.

## Questions

Ask:

1. What context was actually necessary?
2. What context was repeatedly reloaded?
3. Could stable project facts have been reused?
4. Could the search have been narrower?
5. Did context gathering meaningfully reduce uncertainty?

## Important Boundary

Do not treat repository inspection itself as waste.

Exploration is justified when the agent lacks reliable evidence.

The concern is:

```text
Repeated or overly broad exploration
without a corresponding information need.
```

## Typical Recommendation Patterns

Possible recommendations include:

- reuse stable repository maps or project status documents;
- provide known paths in advance;
- point the agent to the relevant milestone prompt;
- prefer targeted search over repeated full-repository exploration;
- avoid restating background already available in durable project files.

---

# 6. Execution Efficiency

## Core Question

> Once the task was understood, did execution move directly toward changing or validating the intended product state?

## Look For

Positive evidence:

- inspect → implement → verify;
- coherent batches of related edits;
- appropriate autonomy;
- successful use of existing project structure;
- limited unnecessary replanning.

Potential inefficiency:

- long tool sequences with little progress;
- repeated inspection without implementation;
- repeated planning of already-decided work;
- frequent stopping for ordinary engineering decisions;
- repeated commands that do not change information or state;
- excessive switching between unrelated task areas.

## Questions

Ask:

1. How quickly did the session move from understanding to useful action?
2. Were tool calls advancing the task?
3. Did the agent repeatedly reopen settled decisions?
4. Was work batched coherently?
5. Were ordinary engineering choices handled autonomously when permitted?

## Typical Recommendation Patterns

Possible recommendations include:

- authorize ordinary in-scope engineering decisions;
- batch related fixes;
- establish a clear autonomous execution loop;
- reduce unnecessary replanning;
- use narrower inspection after the initial repository understanding is established.

---

# 7. Interaction Overhead

## Core Question

> How much user-agent interaction was necessary to move the work forward?

## Look For

Positive evidence:

- one clear task handoff;
- agent proceeds autonomously within scope;
- user intervention occurs at meaningful decision gates;
- agent reports only when a real choice or blocker exists.

Potential inefficiency:

- frequent pauses for minor decisions;
- repeated user confirmation for routine operations;
- the user acts as a message relay between agents unnecessarily;
- repeated prompts merely instruct the agent to continue;
- the agent asks questions that available project evidence could answer;
- the session fragments one coherent task into many conversational turns.

## Questions

Ask:

1. Which user interventions were genuinely necessary?
2. Which could have been handled by the agent under the existing scope?
3. Did the user need to repeatedly say "continue"?
4. Did the agent stop at normal implementation decisions?
5. Were escalation points meaningful?

## Typical Recommendation Patterns

Possible recommendations include:

- define autonomy boundaries at task start;
- reserve user confirmation for scope, risk, or irreversible choices;
- allow the agent to complete ordinary fix-and-verify loops independently;
- reduce conversational checkpoints inside one coherent milestone.

---

# 8. Verification Efficiency

## Core Question

> Did the workflow gather enough evidence to trust the result without unnecessary repeated verification?

## Look For

Positive evidence:

- targeted checks immediately after narrow changes;
- regression tests matched to the affected area;
- full-suite execution at meaningful gates;
- validation expands as risk increases;
- failures lead to relevant corrective action.

Potential inefficiency:

- repeated full-suite execution after trivial changes;
- rerunning the same failing command without changing conditions;
- broad validation before narrow failures are understood;
- verifying unrelated parts of the product repeatedly;
- duplicating equivalent validation without a clear reason.

## Questions

Ask:

1. Was the first verification step proportional to the change?
2. Were targeted tests used?
3. When was the full suite appropriate?
4. Did each repeated verification run answer a new question?
5. Did failures narrow subsequent investigation?

## Important Boundary

Do not recommend reducing verification merely to save tokens.

Reliability remains more important than token minimization.

The preferred pattern is:

```text
Targeted Verification
→ Relevant Regression
→ Full Gate When Appropriate
```

rather than:

```text
Skip Verification
```

## Typical Recommendation Patterns

Possible recommendations include:

- run narrow tests first;
- define full-suite gates;
- avoid repeating unchanged checks;
- tie regression scope to changed behavior;
- use failure evidence to narrow the next verification step.

---

# 9. Rework & Failure

## Core Question

> How much work had to be repeated because of misunderstanding, incorrect implementation, preventable failure, or poorly sequenced decisions?

## Look For

Examples:

- incorrect task interpretation;
- implementation later reverted;
- user correction causes major rewrite;
- repeated command failure;
- repeated test failure with the same cause;
- changes made before reading required constraints;
- duplicate implementation;
- unnecessary rollback;
- substantial rework caused by earlier scope ambiguity.

## Classify Rework

When useful, classify rework as:

```text
Necessary Discovery
Avoidable Misunderstanding
Avoidable Execution Error
Avoidable Verification Loop
Scope Change
External / Environmental Failure
```

## Questions

Ask:

1. Why did work need to be repeated?
2. Was the cause knowable earlier?
3. Did the agent learn from the first failure?
4. Did rework come from task framing, context, implementation, or verification?
5. Could a small earlier check have prevented a large later rewrite?

## Typical Recommendation Patterns

Possible recommendations include:

- inspect the relevant contract before implementation;
- validate assumptions earlier;
- reproduce before fixing;
- test the narrow behavior before expanding;
- separate new scope from defect correction.

---

# 10. Token Consumption

## Core Question

> How many tokens were consumed, where were they concentrated, and what observable workflow behavior helps explain the usage?

Token consumption is a V1 metric, not a standalone verdict.

## Required Principle

Use programmatically extracted token evidence whenever available.

Do not ask the user to manually transcribe token counts when the source records can supply them.

Do not estimate missing fields.

## Useful Token Views

Where supported, inspect:

```text
Per Session
Combined Selected Scope
Input
Cached Input / Cache-Related Usage
Cache-Write Input Usage, when exposed
Output
Reasoning Usage
Total / Cumulative Usage
```

Only use fields that can be derived reliably.

## Questions

Ask:

1. Which session consumed the most tokens?
2. Was that session also the largest or most complex?
3. Did high usage coincide with repeated context loading?
4. Did it coincide with repeated tool loops?
5. Did it coincide with failed or repeated verification?
6. Did it coincide with heavy user-agent interaction?
7. Did later sessions become more efficient after prior context was established?

## Interpretation Rules

Avoid:

```text
More tokens = worse.
```

Prefer:

```text
High usage + proportionate complex work
→ may be reasonable.

High usage + repeated unchanged context
→ possible context inefficiency.

High usage + repeated failed loops
→ possible rework cost.

High usage + repeated full verification
→ possible verification overhead.
```

## Multi-Session Analysis

For multiple sessions, compare:

- absolute token usage;
- share of total usage;
- workflow purpose;
- notable repeated behavior;
- whether later sessions benefited from earlier work;
- whether repeated background loading persisted across sessions.

Example structure:

```text
Session A
Tokens: high
Purpose: architecture + implementation
Interpretation: largely expected

Session B
Tokens: medium
Purpose: narrow defect correction
Interpretation: relatively expensive for scope because repeated repository inspection dominated

Session C
Tokens: low
Purpose: final verification
Interpretation: efficient closure
```

Do not make such judgments without evidence.

---

# 11. Cross-Dimension Analysis

The seven dimensions are not independent.

Look for causal relationships.

Examples:

```text
Weak Task Framing
→ repeated clarification
→ rework
→ higher token usage
```

```text
Repeated Context Loading
→ higher input-token usage
→ longer execution
```

```text
Too Many User Checkpoints
→ fragmented sessions
→ repeated context rebuilding
→ interaction overhead
```

```text
Poor Verification Sequencing
→ repeated full-suite runs
→ execution overhead
→ token overhead
```

The most useful recommendation often addresses the upstream cause, not the visible downstream symptom.

---

# 12. Finding Priority

Not every observation deserves a recommendation.

Prioritize findings that are:

```text
Repeated
High Impact
Clearly Supported
Actionable
Likely to Recur
```

For a Standard report, prefer the most meaningful 3–5 efficiency losses rather than listing every small imperfection.

For a Brief report, focus on the highest-impact findings.

For a Deep report, include more evidence and secondary findings, but preserve prioritization.

---

# 13. What Worked Well

Every review should explicitly preserve successful behavior.

Examples may include:

- clear milestone prompt;
- correct autonomy level;
- efficient targeted search;
- good batching;
- appropriate test sequencing;
- successful self-correction;
- disciplined scope control;
- strong completion verification.

Do not treat the report as a defect list.

The goal is:

```text
Keep what works
+
Change what repeatedly costs too much
```

---

# 14. Recommendation Quality

Recommendations should be:

```text
Specific
Evidence-Based
Small Enough to Apply
Relevant to the Observed Workflow
```

Avoid vague advice such as:

```text
Use fewer tokens.
Be more efficient.
Plan better.
```

Prefer:

```text
For narrow fixes, run the directly affected tests first and reserve the full suite for the batch completion gate.
```

or:

```text
When the session storage path is unchanged, state that explicitly in the prompt so the executing agent does not rediscover it.
```

---

# 15. Previous-Report Comparison

When a previous report is supplied, compare the same seven dimensions where meaningful.

Allowed V1 trend labels:

```text
Improved
Unchanged
Regressed
Newly Observed
Not Comparable
```

Use `Not Comparable` when task type or scale differs too much for a fair conclusion.

Do not infer progress from token reduction alone.

A lower-token session may simply contain less work.

Look for process evidence such as:

- fewer repeated reads;
- fewer clarification loops;
- better verification sequencing;
- less avoidable rework;
- more autonomous execution;
- stronger task framing.

---

# 16. Candidate Development Principles

A repeated, well-supported lesson may become a candidate reusable principle.

A candidate should be:

- broader than one isolated incident;
- directly supported by the review;
- useful in future AI coding work;
- concise enough to remember;
- actionable.

Example:

```text
Candidate Development Principle:
Reserve user intervention for meaningful scope, risk, or irreversible decisions; allow ordinary in-scope engineering choices to stay inside the active execution loop.
```

Do not automatically convert candidates into permanent rules.

User approval is required.

---

# 17. V1 Limitations

This framework does not attempt to measure:

- code quality directly;
- developer productivity as an absolute score;
- monetary cost unless reliable pricing data is explicitly introduced;
- model intelligence;
- software-engineering maturity;
- causal token attribution with scientific precision;
- agent performance across unsupported providers;
- human productivity outside the observed sessions.

V1 produces a practical engineering retrospective, not a formal research-grade benchmark.

---

# 18. Framework Evolution

Future versions may extend this framework with concepts such as:

- context engineering;
- loop engineering;
- agent observability;
- software delivery metrics;
- defect escape analysis;
- evaluation design;
- task decomposition quality;
- autonomy calibration;
- cross-agent comparison.

Do not add those dimensions to V1 automatically.

The current framework should remain the stable baseline until a deliberate versioned revision is made.

---

# 19. V1 Analysis Checklist

Before finalizing a review, verify:

- [ ] The observable workflow was reconstructed before judging it.
- [ ] Task Framing was considered.
- [ ] Context Efficiency was considered.
- [ ] Execution Efficiency was considered.
- [ ] Interaction Overhead was considered.
- [ ] Verification Efficiency was considered.
- [ ] Rework & Failure was considered.
- [ ] Token Consumption was considered.
- [ ] Token values came from reliable programmatic evidence or were marked unavailable.
- [ ] Necessary iteration was not automatically labeled inefficient.
- [ ] Important findings distinguish evidence from interpretation.
- [ ] Recommendations address likely upstream causes where possible.
- [ ] Successful workflow behavior is preserved explicitly.
- [ ] Previous-report trends are included when a valid baseline exists.
- [ ] Candidate Development Principles remain proposals pending user approval.
