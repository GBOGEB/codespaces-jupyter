# W290 lossless handover - strict numeric-zero post-merge repair

Repository: GBOGEB/codespaces-jupyter
PR: #7

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
- keep that negative probe from writing bytecode before the exact-source check;
- re-run the real QPS notebook twice through the governed runtime harness;
- require equal notebook output digest, >0 executed code cells on each run,
  source-backed guard validation, Excel semantic digest, normalized CSV digest,
  and exact-head artifacts;
- bind the workflow to the actual 2026-09-23 W290 handover filename.

The QPS count calculation is unchanged. This does not regenerate the exact
v0.5 workbook binary and cannot promote the expected v0.6 state.

## Execution history

The first PR-head run, 35841827953 at
aafb70de3c1ee0c29fded66e73f8dc66bfa4c946, failed before mutation testing
because direct script execution could not import scripts.qps_rtm_workload.
Commit fc4bbd74127a013246a15fe819e1b04b70670222 made the probe import-safe.

Run 35841901158 at that repaired head then passed the negative guard probe but
failed the notebook exact-source precheck because importing the workload wrote
scripts/__pycache__/qps_rtm_workload.cpython-311.pyc. Commit
05ba30e279055e31483cc08c1b1f51e5136577ce runs the negative probe with
PYTHONDONTWRITEBYTECODE=1.

Run 35842012607 / job 107119065381 at
05ba30e279055e31483cc08c1b1f51e5136577ce passed:

- negative guard probe: PASS_GUARDS_FAIL_CLOSED;
- rejected unsafe mutations: 15;
- notebook executed code cells: 3 and 3;
- equal notebook output digest:
  a1f2a771bf4dbaa69a133ef793fd15d8e4755c17fbd4cf5133066fe1479c6c2a;
- workload receipt:
  PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION;
- Excel semantic SHA-256:
  fb9be281accf5760fc0dd64e69d600356fc0ef0e1c1d467c73f173de9318edcc;
- normalized CSV SHA-256:
  78ac78cbf4ac875c7039d6015a715062754442a800be8a3d4627b851e421923a;
- artifact ID 10740834822;
- artifact ZIP SHA-256:
  c63b80d0e203492133347be593613b11665b3716d64c6d6357134d2e6d961d84.

This proof is candidate evidence only because governance serialization and a
review repair followed it.

## Review disposition

Codex review of aafb70de3c raised two material findings.

P1 4080848699, direct-execution import failure, is repaired by
fc4bbd74127a013246a15fe819e1b04b70670222 and demonstrated repaired by the
subsequent successful negative probe.

P2 4080848709, the workflow referenced a 2026-09-22 W290 handover path while
the committed file is dated 2026-09-23, is repaired by
35e3dbc592115aa2856b072329e19c52c395dd8a.

## Exact next gate

Obtain one final exact-head qps-project-workload-proof after this handover and
the recursive patch are refreshed. Then request/await Codex review of that exact
final head. Require:

- exact candidate SHA checkout and clean source tree;
- PASS_GUARDS_FAIL_CLOSED with all 15 mutations rejected;
- >0 notebook code cells on both runs;
- equal complete notebook output digest;
- source-backed non-compensating guard validation;
- PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION;
- uploaded Excel/CSV/receipt artifacts bound to the exact final SHA;
- no unresolved material review findings.

Only then merge PR #7, verify merged main, and record the MissionControl closure
receipt.

No authority transfer. Formal, engineering, negotiation, and compliance credit
deltas remain numeric zero.
