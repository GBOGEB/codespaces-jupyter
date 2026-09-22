# W288 lossless handover - QPS RTM real-workload reproducibility

Repository: GBOGEB/codespaces-jupyter

Source authority remains in GBOGEB/cryoplant-project. This runtime repository
contains only a bounded, source-bound calculation fixture.

Read in order:

1. triage/W288_QPS_RTM_REAL_WORKLOAD_3PSTAR_MIP.yaml
2. docs/QPS_RTM_REAL_WORKLOAD_PROOF.md
3. data/qps_rtm_partial_relax_v06/baseline_v05.json
4. data/qps_rtm_partial_relax_v06/bindings.csv
5. data/qps_rtm_partial_relax_v06/expected_v06.json
6. scripts/qps_rtm_workload.py
7. notebooks/qps_rtm_partial_relax_workload.ipynb

The workload reproduces the expected v0.6 partial-relaxation calculation,
creates and reloads an Excel workbook, exports normalized CSV, and emits a
semantic workbook digest.

The exact v0.5 workbook binary is not present here. Therefore a green W288 run
does not promote the expected v0.6 counts and does not satisfy the separate
cryoplant exact-binary regeneration gate.

## Review repair

The final serialized pre-review head e23965cd1ee9485eeff1168a2b3d98fb6c4b603f
passed workflow 35757662766 with 3 code cells in both runs and equal notebook
output digest 8f6fd9a684e797fdecf402cf460cdf450734fbe443068e15a9049f821c04b8a1.
Its workload receipt also matched the expected v0.6 calculation.

Codex then raised P1 review finding 4074272043: the receipt hard-coded
no-authority and zero-credit values instead of validating them from the
source-backed fixtures. That proof is therefore historical evidence, not the
final 3PC proof.

The repair now fails closed unless:
- baseline authority_transfer is false;
- baseline formal_credit_delta is zero and baseline status is PASS;
- expected state is EXPECTED_NOT_YET_CREDITED;
- expected authority_transfer is false;
- formal, engineering, negotiation and compliance credit deltas are all zero;
- the exact-v0.5 regeneration promotion gate remains the controlled
  non-compensating statement.

The receipt emits those authority and credit values from the validated source
fixture, CI rechecks the guard result, and the notebook exposes guard validation
before the calculation.

## Exact next gate

Obtain one fresh exact-head project-workload run after the repair and refreshed
recursive patch. Require:
- clean exact source SHA;
- more than zero code cells on both runs;
- equal complete notebook output digests;
- guard_validation.all_non_compensating_guards_passed = true;
- workload receipt PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION;
- uploaded workbook, CSV and receipts bound to that exact candidate SHA;
- clean final review / resolved material findings.

Only then merge PR #5 and emit the MissionControl closure receipt.

No authority transfer; all credit deltas remain zero.
