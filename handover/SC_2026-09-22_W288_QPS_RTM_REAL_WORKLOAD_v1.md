# W288 lossless handover - QPS RTM real-workload reproducibility

Repository: GBOGEB/codespaces-jupyter

Source authority remains in GBOGEB/cryoplant-project; this runtime repository
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

3PR and MIP are materialized. 3PC Prepare is complete. Continue by obtaining one
fresh exact-head run of the dedicated project-workload workflow. Require both
notebook passes to execute more than zero code cells, equal complete notebook
output digests, a workload receipt status of
PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION, and uploaded artifacts
bound to the exact candidate SHA. Then merge only if review is clean or all
material findings are repaired.

No authority transfer; all credit deltas remain zero.
