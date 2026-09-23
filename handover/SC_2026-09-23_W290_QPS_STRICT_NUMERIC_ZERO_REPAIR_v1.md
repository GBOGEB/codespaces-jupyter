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

## Decimal underflow follow-up

Final review of serialized head 67c36db447c4405c8afd0712fbb11222fcac07f5
raised P2 finding 4080883031: ordinary json.loads can underflow a tiny nonzero
token such as 1e-400 to 0.0 before the zero-credit predicate sees it.

Commit 5843fbf8993eaa2d4e080ebc89fcdab7d2f21b94 now parses JSON floating
tokens with Decimal and accepts credit zero only when the value is exact int 0
or a finite Decimal equal to zero. Programmatic float values are deliberately
not trusted for the credit gate. Commit
10a481a94a53a9e585f31436683e224c18139244 extends the negative probe to
reject both Decimal("1e-400") and an untrusted float 0.0.

Run 35842664433 / job 107121212081 on 10a481a94a53a9e585f31436683e224c18139244
passed with 17 rejected unsafe mutations, 3+3 executed notebook cells, the same
stable notebook output digest, unchanged workbook/CSV semantic digests, and
artifact 10742360391 with ZIP SHA-256
6218cc54386c2dc42a73cd0ff67d51d2aadb501beec9108671dc8462e7774d2e.

Because this handover and recursive patch are updated after that run, one final
exact-head recertification is still required.

## Accepted Decimal zero normalization follow-up

Codex review of final head b4d9df3618ac4833b9c6ae6b863f03df490f1f8d
raised P2 finding 4080944466: exact-zero JSON spellings such as 0.0 and 0e0 are
parsed as Decimal and pass the exact-zero predicate, but copying those Decimal
objects directly into the JSON receipt would make json.dumps fail.

Commit 79995769cecb0f71016698a21175ddbf6cb922a8 canonicalizes every accepted
credit zero to integer 0 before it enters guard_validation or the top-level
receipt. Commit ad16863a045305d71b3fb58cb266b87c78867480 extends the negative
probe to prove that Decimal zero spellings 0.0, 0e0, and -0.0 are accepted,
canonicalized to int 0, and JSON-serializable while all unsafe mutations remain
rejected.

Run 35843383431 / job 107123565425 on ad16863a045305d71b3fb58cb266b87c78867480
passed with 17 rejected unsafe mutations, 3+3 notebook cells, stable notebook
output digest, unchanged workbook/CSV semantic digests, and artifact 10742481457
with ZIP SHA-256 edd1baa889639f2e16ea632b41f31ba3487c3d528f506f43d3b078547f581ea4.

This candidate proof precedes the refreshed governance surfaces, so a final
exact-head recertification remains required.

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
