# W290 lossless handover - strict numeric-zero post-merge repair

Repository: GBOGEB/codespaces-jupyter

## Context

W288 established the first bounded real QPS/RTM notebook workload and W289
introduced fail-closed authority guards after a P1 review finding. PR #6 merged
as 3902e0edb18230e9236e48acfb36ce65b66732bc before the subsequent P2 review
repair was incorporated into main.

P2 finding 4074342402 identified a Python type-safety edge: False == 0. A JSON
boolean credit value could therefore pass a naive zero comparison.

## W290 repair

The repair is deliberately narrow:

- define numeric zero as int/float, explicitly excluding bool, with value == 0;
- apply that rule to the baseline formal credit and every expected credit delta;
- run a negative mutation probe that must reject unsafe authority, state,
  credit-type/value, and exact-v0.5 promotion-gate mutations;
- re-run the real QPS notebook twice through the governed runtime harness;
- require equal notebook output digest, >0 executed code cells on each run,
  source-backed guard validation, Excel semantic digest, normalized CSV digest,
  and exact-head artifacts.

The QPS count calculation is unchanged. This does not regenerate the exact
v0.5 workbook binary and cannot promote the expected v0.6 state.

## Exact next gate

1. Open W290 PR from w290/qps-strict-numeric-zero-postmerge-repair.
2. Require qps-project-workload-proof and governed-runtime-probe to pass on the
   exact PR head.
3. Confirm the negative probe reports PASS_GUARDS_FAIL_CLOSED and rejects every
   listed mutation.
4. Request/await final Codex review and repair only material findings.
5. Merge only after exact-head proof and review are clean.
6. Verify merged main and record the MissionControl closure receipt.

No authority transfer. Formal, engineering, negotiation, and compliance credit
deltas remain numeric zero.
