# QPS RTM real-workload reproducibility contract

## Purpose

This workload advances the Jupyter proof from a synthetic two-cell runtime test
to a bounded project calculation tied to current QPS/RTM review control.

The source snapshot is derived from:

- GBOGEB/cryoplant-project at commit 339a1682236d5dc0ccae5cf6d6df26d9f510d6b8
- controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V05_VALIDATION_RECEIPT_20260922.json
  blob 7de067615cedd805207f480bdc018638c56180c4
- controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V06_RECENSUS_CONTROL_20260922.yaml
  blob 084f7f515cd5fd27e10bca820533c052a70dd48e

The five exact bidder-native bindings are the currently controlled
TEC_ID_034 / 205 / 206 / 207 / 144 set.

## What the notebook does

notebooks/qps_rtm_partial_relax_workload.ipynb:

1. loads the v0.5 validation receipt snapshot and five exact bindings;
2. validates uniqueness and exact target/queue binding;
3. calculates the expected v0.6 review counts;
4. compares those counts to the source-backed expected control;
5. writes a structured Excel workbook with formula-driven calculated cells;
6. exports normalized CSV and reloads the workbook for a semantic digest;
7. emits a workload receipt with explicit non-authority guards.

The generic exact-head notebook harness then executes this notebook twice and
requires the complete notebook output digest to match.

## Expected calculation

Starting from v0.5:

- atomic rows: 295 -> 300
- BOTH_CHALLENGE_SAME_ATOM: 75 -> 78
- ALAT_ONLY: 80 -> 80
- LKT_ONLY: 47 -> 49
- PROTECTED_REMAINDER: 93 -> 93
- ATOMIZED_SOURCE_BACKED: 88 -> 93
- LKT_SECTION_FAMILY_ALIGNMENT_PENDING: 55 -> 50
- LKT_SCOPE_INTERPRETATION_BOUND: 5 -> 5
- SOURCE_EXTRACTION_REQUIRED: 574 -> 574

These are reproduced expected values only. The cryoplant control explicitly
keeps them uncredited until the exact v0.5 workbook binary is regenerated and
its emitted receipt passes.

## Contract

cryoplant control snapshot
-> checked-in bounded fixture
-> exact Git SHA
-> Jupyter notebook
-> RTM calculation + Excel workbook + normalized CSV + semantic digest
-> second independent notebook execution
-> equal complete output digest plus more than zero executed cells
-> human RYG and uploaded artifact receipt
-> MissionControl receipt

A green workload proof means the bounded calculation is reproducible at that
source SHA. It is not engineering validation, contractual acceptance, bidder
compliance, or promotion of the expected v0.6 counts.
