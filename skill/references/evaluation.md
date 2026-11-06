# Evaluate activation and output separately

## Trigger accuracy

Store realistic queries labeled with `should_trigger`. Start with near-miss pairs,
then expand to about 20 queries (8–10 positive and 8–10 negative): explicit/implicit
intent, terse/detailed requests, casual phrasing, and adjacent domains.

Fix a stratified roughly 60/40 train/validation split before tuning descriptions.
Use only train failures to revise wording; reserve validation results for selecting
iterations. Add fresh held-out queries for a final generalization check.

Run each query in a fresh session with the skill discoverable, normally three times.
Count activation only when traces show the skill's SKILL.md was loaded. Do not force
load it in activation tests. Record client/model/version, query, run, and trace path.
Report trigger rates and false positives/negatives; a majority threshold is a useful
starting point, not a universal quality guarantee.

## Task quality

Author 2–3 realistic cases initially in `evals/evals.json` (expand with regressions):
prompt, expected_output, optional input file paths. Include a meaningful edge case.
Compare the new skill with a snapshot of the previous skill or no skill, using
identical tasks, inputs, model, tool access, and fresh workspaces/contexts. Install
only the intended skill version to prevent contamination by other copies.

Write results outside the installed skill directory:

```text
<skill>-workspace/iteration-1/<case>/
  with_skill/outputs/
  old_skill/outputs/
  grading.json
  timing.json
  feedback.json
```

Capture tool traces, generated artifacts, checks, tokens/duration when available,
and human feedback. Mark unavailable metrics as unavailable rather than inventing
them. Use disposable local fixtures for changes to Git, homes, releases, or registries.

After inspecting first outputs, add/refine assertions that distinguish good behavior
from the baseline. Grade each with PASS/FAIL and concrete artifact/trace evidence.
Use deterministic checks for mechanical properties; human review for usefulness.
Potential assertions authored before execution are provisional, not measured results.

Inspect failures *and* successes. Remove checks that always pass without the skill;
investigate shared failures and timing outliers. Improve the underlying procedure
rather than memorizing a fixture. Rerun affected and previously passing cases after
each change. Aggregate pass counts/rates, cost, and variance only when repeated runs
justify it. Blind version comparisons can reduce preference for the newer draft.

## Report honestly

Distinguish structural validation, authored test cases, observed activation, task
quality, and external runtime qualification. A JSON parser or frontmatter validator
does not establish any behavioral success. Keep unresolved failures visible.
