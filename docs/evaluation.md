# Evaluation workflow

The seven `evals/evals.json` files contain behavioral prompts and six activation
queries each. GitHub Actions has eleven behavioral cases, including six-job routing,
prepare/tag separation, maintenance isolation, qualification evidence and advisory
security failures and needs-based runtime selection; other
skills have four initial cases each. Inline scenarios need no additional files unless the case explicitly
asks for a disposable fixture. Prepare those fixtures before running either arm;
give both arms identical copies. Record the resulting task prompt separately from
fixture setup instructions, especially for Git tests.

## Current status

These initial cases have been syntax-checked, not run as a model benchmark.
No activation rate or output-quality improvement is claimed. Structural validation
and validator unit tests are independent evidence described in the review report.

## Run a comparison

1. Snapshot the old skill from Git history and the new skill into separate test
   environments. Keep model/client/version/tool access and input fixtures identical.
   Ensure the normal installed copy does not contaminate either run.
2. Execute every behavioral prompt in fresh contexts against each version, or use
   no skill as the baseline. Use disposable repositories/home directories for
   mutable tasks. Never aim release fixtures at a real registry or cluster.
3. Save traces, diffs/artifacts, checks, and timing/token data where available under
   an external `<skill>-workspace/iteration-N/<case>/<configuration>/` directory.
4. Inspect outputs and turn expected_output into concrete assertions, each graded
   with PASS/FAIL and artifact/trace evidence. Retain human feedback and investigate
   both failures and unnecessary work. Do not grade only the agent's summary.
5. Revise underlying instructions and rerun affected cases plus passing regressions.
   Report actual pass counts, costs, unresolved failures, and skipped cases.

## Optimize activation separately

Run trigger_queries without forcing skill activation. Count success only when traces
show the expected loading/non-loading. Expand the six-query starter sets to about
20 realistic queries per skill before tuning: varied phrasing, implicit intent,
and strong near-misses. Fix a stratified 60/40 train/validation split and repeat
each query three times. Use train failures for changes; compare held-out validation
rates to select versions. Keep fresh final queries to check generalization.

The `commit` skill owns Git mutation; `conventionalcommits` owns message semantics.
A client may load both for a task that genuinely combines them. Assess each query
against its requested scope, not keyword overlap alone.

The commit workflow now requires loading conventionalcommits, proactive commits
for implementation work, and a why-body. Its fixtures must install both skills
except the explicit missing-companion case. GitHub Actions policy cases exercise
the user's catalog conventions, not just GitHub syntax; acceptance of another
abstraction in an unrelated repository is not permission to replace that contract.

See [the portable protocol](../skill/references/evaluation.md) for details and
[the official guide](https://agentskills.io/skill-creation/evaluating-skills).
