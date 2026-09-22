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

A real candidate proof already passed on
5b27886ad1630edaa18f4e8a24625291a23ff8b9 using workflow 35757514347.
Both notebook passes executed 3 code cells and produced the same notebook output
digest 8f6fd9a684e797fdecf402cf460cdf450734fbe443068e15a9049f821c04b8a1.
The workload receipt was
PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION.
The generated workbook semantic digest was
fb9be281accf5760fc0dd64e69d600356fc0ef0e1c1d467c73f173de9318edcc
and normalized CSV digest was
78ac78cbf4ac875c7039d6015a715062754442a800be8a3d4627b851e421923a.
Artifact 10708798126 had ZIP SHA-256
c735f11f228b572df3db6b7fe3043cd69789a439d5c2297db2cd5abc16c1eaa9.

Because this handover and recursive patch are serialized after that run, obtain
one final exact-head recertification after the serialization commit. Then require
the same gates: more than zero cells on both runs, equal notebook output digests,
the workload receipt PASS status, and uploaded evidence bound to the final
candidate SHA.

No authority transfer; all credit deltas remain zero.
