# W289 recursive P1/P2 authority-guard repair patch

Base: d589aaad01ddbf37f8020a448cd847539583bb23

----FILE: scripts/qps_rtm_workload.py
#!/usr/bin/env python3
"""Bounded real QPS RTM workload: source-backed control snapshot -> Excel -> semantic receipt.

This intentionally reproduces the expected v0.6 calculation from repository
control data. It does not regenerate the authoritative v0.5 workbook and must
not promote the expected counts into contract, compliance, engineering, or
negotiation authority.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill


BASE = Path("data/qps_rtm_partial_relax_v06")
BASELINE = BASE / "baseline_v05.json"
BINDINGS = BASE / "bindings.csv"
EXPECTED = BASE / "expected_v06.json"
OUT = Path("artifacts/qps_rtm_workload")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_inputs() -> tuple[dict[str, Any], list[dict[str, str]], dict[str, Any]]:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    with BINDINGS.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return baseline, rows, expected


def is_numeric_zero(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0


def validate_authority_guards(
    baseline: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    required_promotion_gate = (
        "exact source v0.5 binary must be regenerated and the emitted receipt must PASS "
        "before these become the current workbook counts"
    )
    failures: list[str] = []

    if baseline.get("authority_transfer") is not False:
        failures.append("baseline authority_transfer must be false")
    if not is_numeric_zero(baseline.get("formal_credit_delta")):
        failures.append("baseline formal_credit_delta must be numeric zero, not bool")
    if baseline.get("status") != "PASS":
        failures.append("baseline validation receipt status must be PASS")

    if expected.get("state") != "EXPECTED_NOT_YET_CREDITED":
        failures.append("expected state must remain EXPECTED_NOT_YET_CREDITED")
    if expected.get("authority_transfer") is not False:
        failures.append("expected authority_transfer must be false")
    for key in (
        "formal_credit_delta",
        "engineering_credit_delta",
        "negotiation_credit_delta",
        "compliance_credit_delta",
    ):
        if not is_numeric_zero(expected.get(key)):
            failures.append(f"{key} must be numeric zero, not bool")
    if expected.get("promotion_gate") != required_promotion_gate:
        failures.append("exact-v0.5 regeneration promotion gate changed or weakened")

    if failures:
        raise ValueError("non-compensating authority guard failure: " + "; ".join(failures))

    return {
        "all_non_compensating_guards_passed": True,
        "baseline_authority_transfer": baseline["authority_transfer"],
        "baseline_formal_credit_delta": baseline["formal_credit_delta"],
        "expected_state": expected["state"],
        "expected_authority_transfer": expected["authority_transfer"],
        "formal_credit_delta": expected["formal_credit_delta"],
        "engineering_credit_delta": expected["engineering_credit_delta"],
        "negotiation_credit_delta": expected["negotiation_credit_delta"],
        "compliance_credit_delta": expected["compliance_credit_delta"],
        "promotion_gate": expected["promotion_gate"],
    }


def validate_bindings(rows: list[dict[str, str]]) -> None:
    if len(rows) != 5:
        raise ValueError(f"expected 5 exact bindings, got {len(rows)}")
    if len({r["native_id"] for r in rows}) != 5:
        raise ValueError("native_id values are not unique")
    if len({r["canonical_target"] for r in rows}) != 5:
        raise ValueError("canonical_target values are not unique")
    if any(r["exact_binding"].strip().lower() != "true" for r in rows):
        raise ValueError("all workload rows must be exact_binding=true")

    required = {
        "TEC_ID_034": ("RTM-138", "LKT_ONLY"),
        "TEC_ID_205": ("RTM-691", "LKT_ONLY"),
        "TEC_ID_206": ("RTM-693", "BOTH_CHALLENGE_SAME_ATOM"),
        "TEC_ID_207": ("RTM-695", "BOTH_CHALLENGE_SAME_ATOM"),
        "TEC_ID_144": ("RTM-521", "BOTH_CHALLENGE_SAME_ATOM"),
    }
    for row in rows:
        target, queue = required[row["native_id"]]
        if row["canonical_target"] != target or row["queue_after_regeneration"] != queue:
            raise ValueError(f"binding mismatch for {row['native_id']}")


def calculate(
    baseline: dict[str, Any],
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    peer = dict(baseline["peer_queues"])
    increments = Counter(r["queue_after_regeneration"] for r in rows)
    for queue, delta in increments.items():
        peer[queue] = peer.get(queue, 0) + delta

    coverage = dict(baseline["coverage_states"])
    coverage["ATOMIZED_SOURCE_BACKED"] += len(rows)
    coverage["LKT_SECTION_FAMILY_ALIGNMENT_PENDING"] -= len(rows)

    return {
        "canonical_rtm_denominator": baseline["rtm_denominator"],
        "atomic_rows": baseline["atomic_rows"] + len(rows),
        "peer_queues": peer,
        "parent_screening": coverage,
        "ranked_v05_family_frontier_remaining": 0,
    }


def assert_expected(calculated: dict[str, Any], expected: dict[str, Any]) -> None:
    compare = {
        "canonical_rtm_denominator": expected["canonical_rtm_denominator"],
        "atomic_rows": expected["atomic_rows"],
        "peer_queues": expected["peer_queues"],
        "parent_screening": expected["parent_screening"],
        "ranked_v05_family_frontier_remaining": expected["ranked_v05_family_frontier_remaining"],
    }
    if calculated != compare:
        raise AssertionError(
            "calculated workload output differs from repository expected control: "
            + json.dumps({"calculated": calculated, "expected": compare}, sort_keys=True)
        )


def style_header(ws) -> None:
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.alignment = Alignment(vertical="top", wrap_text=True)


def write_workbook(
    baseline: dict[str, Any],
    rows: list[dict[str, str]],
    expected: dict[str, Any],
    calculated: dict[str, Any],
    path: Path,
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "BINDINGS"

    binding_headers = list(rows[0].keys())
    ws.append(binding_headers)
    for row in rows:
        ws.append([row[h] for h in binding_headers])
    style_header(ws)
    for col in "ABCDEFGHI":
        ws.column_dimensions[col].width = 22
    ws.column_dimensions["B"].width = 48
    ws.column_dimensions["D"].width = 80
    ws.column_dimensions["E"].width = 34
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    base_ws = wb.create_sheet("BASELINE_V05")
    base_ws.append(["metric", "key", "value"])
    base_rows = [
        ("scalar", "rtm_denominator", baseline["rtm_denominator"]),
        ("scalar", "atomic_rows", baseline["atomic_rows"]),
        ("peer_queue", "ALAT_ONLY", baseline["peer_queues"]["ALAT_ONLY"]),
        ("peer_queue", "BOTH_CHALLENGE_SAME_ATOM", baseline["peer_queues"]["BOTH_CHALLENGE_SAME_ATOM"]),
        ("peer_queue", "LKT_ONLY", baseline["peer_queues"]["LKT_ONLY"]),
        ("peer_queue", "PROTECTED_REMAINDER", baseline["peer_queues"]["PROTECTED_REMAINDER"]),
        ("parent_screening", "ATOMIZED_SOURCE_BACKED", baseline["coverage_states"]["ATOMIZED_SOURCE_BACKED"]),
        ("parent_screening", "LKT_SCOPE_INTERPRETATION_BOUND", baseline["coverage_states"]["LKT_SCOPE_INTERPRETATION_BOUND"]),
        ("parent_screening", "LKT_SECTION_FAMILY_ALIGNMENT_PENDING", baseline["coverage_states"]["LKT_SECTION_FAMILY_ALIGNMENT_PENDING"]),
        ("parent_screening", "SOURCE_EXTRACTION_REQUIRED", baseline["coverage_states"]["SOURCE_EXTRACTION_REQUIRED"]),
    ]
    for row in base_rows:
        base_ws.append(list(row))
    style_header(base_ws)

    calc_ws = wb.create_sheet("CALCULATED_V06")
    calc_ws.append(["metric", "key", "formula", "expected"])
    formula_rows = [
        ("scalar", "canonical_rtm_denominator", "=BASELINE_V05!C2", expected["canonical_rtm_denominator"]),
        ("scalar", "atomic_rows", "=BASELINE_V05!C3+COUNTA(BINDINGS!A2:A6)", expected["atomic_rows"]),
        ("peer_queue", "ALAT_ONLY", '=BASELINE_V05!C4+COUNTIF(BINDINGS!H2:H6,"ALAT_ONLY")', expected["peer_queues"]["ALAT_ONLY"]),
        ("peer_queue", "BOTH_CHALLENGE_SAME_ATOM", '=BASELINE_V05!C5+COUNTIF(BINDINGS!H2:H6,"BOTH_CHALLENGE_SAME_ATOM")', expected["peer_queues"]["BOTH_CHALLENGE_SAME_ATOM"]),
        ("peer_queue", "LKT_ONLY", '=BASELINE_V05!C6+COUNTIF(BINDINGS!H2:H6,"LKT_ONLY")', expected["peer_queues"]["LKT_ONLY"]),
        ("peer_queue", "PROTECTED_REMAINDER", "=BASELINE_V05!C7", expected["peer_queues"]["PROTECTED_REMAINDER"]),
        ("parent_screening", "ATOMIZED_SOURCE_BACKED", "=BASELINE_V05!C8+COUNTA(BINDINGS!A2:A6)", expected["parent_screening"]["ATOMIZED_SOURCE_BACKED"]),
        ("parent_screening", "LKT_SCOPE_INTERPRETATION_BOUND", "=BASELINE_V05!C9", expected["parent_screening"]["LKT_SCOPE_INTERPRETATION_BOUND"]),
        ("parent_screening", "LKT_SECTION_FAMILY_ALIGNMENT_PENDING", "=BASELINE_V05!C10-COUNTA(BINDINGS!A2:A6)", expected["parent_screening"]["LKT_SECTION_FAMILY_ALIGNMENT_PENDING"]),
        ("parent_screening", "SOURCE_EXTRACTION_REQUIRED", "=BASELINE_V05!C11", expected["parent_screening"]["SOURCE_EXTRACTION_REQUIRED"]),
        ("scalar", "ranked_v05_family_frontier_remaining", "=0", expected["ranked_v05_family_frontier_remaining"]),
    ]
    for row in formula_rows:
        calc_ws.append(list(row))
    style_header(calc_ws)
    calc_ws.column_dimensions["B"].width = 42
    calc_ws.column_dimensions["C"].width = 58

    check_ws = wb.create_sheet("PYTHON_CHECK")
    check_ws.append(["metric", "key", "calculated_value"])
    check_ws.append(["scalar", "canonical_rtm_denominator", calculated["canonical_rtm_denominator"]])
    check_ws.append(["scalar", "atomic_rows", calculated["atomic_rows"]])
    for key in ("ALAT_ONLY", "BOTH_CHALLENGE_SAME_ATOM", "LKT_ONLY", "PROTECTED_REMAINDER"):
        check_ws.append(["peer_queue", key, calculated["peer_queues"][key]])
    for key in (
        "ATOMIZED_SOURCE_BACKED",
        "LKT_SCOPE_INTERPRETATION_BOUND",
        "LKT_SECTION_FAMILY_ALIGNMENT_PENDING",
        "SOURCE_EXTRACTION_REQUIRED",
    ):
        check_ws.append(["parent_screening", key, calculated["parent_screening"][key]])
    check_ws.append(["scalar", "ranked_v05_family_frontier_remaining", calculated["ranked_v05_family_frontier_remaining"]])
    style_header(check_ws)

    prov_ws = wb.create_sheet("PROVENANCE")
    prov_ws.append(["field", "value"])
    provenance = [
        ("baseline_source_repository", baseline["source_repository"]),
        ("baseline_source_commit", baseline["source_commit"]),
        ("baseline_source_path", baseline["source_path"]),
        ("baseline_source_blob_sha", baseline["source_blob_sha"]),
        ("baseline_source_url", f"https://github.com/{baseline['source_repository']}/blob/{baseline['source_commit']}/{baseline['source_path']}"),
        ("expected_source_repository", expected["source_repository"]),
        ("expected_source_commit", expected["source_commit"]),
        ("expected_source_path", expected["source_path"]),
        ("expected_source_blob_sha", expected["source_blob_sha"]),
        ("expected_source_url", f"https://github.com/{expected['source_repository']}/blob/{expected['source_commit']}/{expected['source_path']}"),
        ("expected_state", expected["state"]),
        ("promotion_gate", expected["promotion_gate"]),
        ("authority_transfer", str(expected["authority_transfer"]).lower()),
    ]
    for item in provenance:
        prov_ws.append(list(item))
    style_header(prov_ws)
    prov_ws.column_dimensions["A"].width = 34
    prov_ws.column_dimensions["B"].width = 120
    for row in prov_ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    wb.save(path)


def workbook_semantic_digest(path: Path) -> tuple[str, dict[str, list[list[Any]]]]:
    wb = load_workbook(path, data_only=False, read_only=True)
    semantic: dict[str, list[list[Any]]] = {}
    for ws in wb.worksheets:
        values = []
        for row in ws.iter_rows(values_only=True):
            values.append([v for v in row])
        semantic[ws.title] = values
    payload = json.dumps(
        semantic,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256_bytes(payload), semantic


def write_normalized_csv(rows: list[dict[str, str]], path: Path) -> None:
    headers = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run() -> dict[str, Any]:
    baseline, rows, expected = load_inputs()
    guard_validation = validate_authority_guards(baseline, expected)
    validate_bindings(rows)
    calculated = calculate(baseline, rows)
    assert_expected(calculated, expected)

    OUT.mkdir(parents=True, exist_ok=True)
    workbook_path = OUT / "QPS_Partial_Relax_Workload_v1.xlsx"
    csv_path = OUT / "bindings_normalized.csv"
    receipt_path = OUT / "workload_receipt.json"

    write_workbook(baseline, rows, expected, calculated, workbook_path)
    write_normalized_csv(rows, csv_path)
    semantic_digest, semantic = workbook_semantic_digest(workbook_path)

    receipt = {
        "schema": "gbogeb.qps_rtm_partial_relax_workload/v1",
        "workload": "QPS_PARTIAL_RELAX_V06_EXPECTED_CALCULATION",
        "source_repository": expected["source_repository"],
        "source_commit": expected["source_commit"],
        "source_control_path": expected["source_path"],
        "source_control_blob_sha": expected["source_blob_sha"],
        "baseline_source_path": baseline["source_path"],
        "baseline_source_blob_sha": baseline["source_blob_sha"],
        "input_fixture_sha256": {
            "baseline_v05.json": sha256_file(BASELINE),
            "bindings.csv": sha256_file(BINDINGS),
            "expected_v06.json": sha256_file(EXPECTED),
        },
        "binding_rows": len(rows),
        "calculated": calculated,
        "expected_state": expected["state"],
        "guard_validation": guard_validation,
        "calculation_matches_expected_control": True,
        "excel_semantic_sha256": semantic_digest,
        "excel_sheet_names": list(semantic),
        "normalized_csv_sha256": sha256_file(csv_path),
        "status": "PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION",
        "authority_transfer": expected["authority_transfer"],
        "formal_credit_delta": expected["formal_credit_delta"],
        "engineering_credit_delta": expected["engineering_credit_delta"],
        "negotiation_credit_delta": expected["negotiation_credit_delta"],
        "compliance_credit_delta": expected["compliance_credit_delta"],
        "claim_guards": [
            "EXPECTED_V06_NE_PROMOTED_CURRENT_STATE",
            "WORKLOAD_REPRODUCIBILITY_NE_ENGINEERING_VALIDATION",
            "WORKLOAD_REPRODUCIBILITY_NE_CONTRACTUAL_OR_COMPLIANCE_CREDIT",
            "EXACT_V05_WORKBOOK_REGENERATION_GATE_REMAINS_SEPARATE",
        ],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))

----END FILE: scripts/qps_rtm_workload.py

----FILE: .github/workflows/qps-project-workload.yml
name: qps-project-workload-proof

on:
  pull_request:
    paths:
      - "data/qps_rtm_partial_relax_v06/**"
      - "notebooks/qps_rtm_partial_relax_workload.ipynb"
      - "scripts/qps_rtm_workload.py"
      - "scripts/runtime_probe.py"
      - "requirements-probe.txt"
      - "Makefile"
      - "docs/QPS_RTM_REAL_WORKLOAD_PROOF.md"
      - "triage/W288_QPS_RTM_REAL_WORKLOAD_3PSTAR_MIP.yaml"
      - "handover/SC_2026-09-22_W288_QPS_RTM_REAL_WORKLOAD_v1.md"
      - "handover/PATCH_ALL_W288_QPS_RTM_REAL_WORKLOAD.md"
      - ".github/workflows/qps-project-workload.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  qps-rtm-workload:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout exact candidate
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha || github.sha }}
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: requirements-probe.txt
      - name: Install governed workload dependencies
        run: python -m pip install -r requirements-probe.txt
      - name: Execute real QPS notebook twice
        run: python scripts/runtime_probe.py --notebook notebooks/qps_rtm_partial_relax_workload.ipynb --output-dir artifacts/qps_rtm_partial_relax_probe
      - name: Verify workload receipt
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          p = Path("artifacts/qps_rtm_workload/workload_receipt.json")
          data = json.loads(p.read_text())
          assert data["status"] == "PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION"
          assert data["binding_rows"] == 5
          assert data["calculation_matches_expected_control"] is True
          assert data["guard_validation"]["all_non_compensating_guards_passed"] is True
          assert data["authority_transfer"] is False
          for key in ("formal_credit_delta", "engineering_credit_delta", "negotiation_credit_delta", "compliance_credit_delta"):
              assert isinstance(data[key], (int, float)) and not isinstance(data[key], bool) and data[key] == 0
          print(json.dumps({
              "status": data["status"],
              "binding_rows": data["binding_rows"],
              "excel_semantic_sha256": data["excel_semantic_sha256"],
              "normalized_csv_sha256": data["normalized_csv_sha256"],
              "non_compensating_guards": data["guard_validation"]["all_non_compensating_guards_passed"],
          }, sort_keys=True))
          PY
      - name: Upload exact-head project workload evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: qps-project-workload-${{ github.event.pull_request.head.sha || github.sha }}
          path: |
            artifacts/qps_rtm_partial_relax_probe/
            artifacts/qps_rtm_workload/
          if-no-files-found: error

----END FILE: .github/workflows/qps-project-workload.yml

----FILE: notebooks/qps_rtm_partial_relax_workload.ipynb
{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "intro",
   "metadata": {},
   "source": [
    "# QPS RTM partial-relaxation workload proof\n",
    "\n",
    "This notebook executes a bounded real QPS workload using source-backed repository control snapshots from GBOGEB/cryoplant-project. It reproduces the expected v0.6 calculation and an Excel/CSV roundtrip. It does not regenerate the authoritative v0.5 workbook and therefore cannot promote expected counts or grant engineering/compliance/contract authority."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "load",
   "metadata": {},
   "outputs": [],
   "source": [
    "from scripts.qps_rtm_workload import load_inputs\n",
    "baseline, bindings, expected = load_inputs()\n",
    "print({'baseline_atomic_rows': baseline['atomic_rows'], 'binding_rows': len(bindings), 'expected_state': expected['state']})"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "calculate",
   "metadata": {},
   "outputs": [],
   "source": [
    "from scripts.qps_rtm_workload import validate_authority_guards, validate_bindings, calculate, assert_expected\n",
    "guard_validation = validate_authority_guards(baseline, expected)\n",
    "validate_bindings(bindings)\n",
    "calculated = calculate(baseline, bindings)\n",
    "assert_expected(calculated, expected)\n",
    "print({'guards': guard_validation, 'calculated': calculated})"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "excel",
   "metadata": {},
   "outputs": [],
   "source": [
    "import json\n",
    "from scripts.qps_rtm_workload import run\n",
    "receipt = run()\n",
    "print(json.dumps(receipt, sort_keys=True))"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

----END FILE: notebooks/qps_rtm_partial_relax_workload.ipynb

----FILE: docs/QPS_RTM_REAL_WORKLOAD_PROOF.md
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
7. validates non-compensating authority, zero-credit, expected-state and exact-v0.5 regeneration guards directly from the source-backed fixtures;
8. emits a workload receipt only after those guards pass.

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
source SHA and the checked-in source fixtures still satisfy the explicit
non-compensating no-authority / zero-credit / exact-v0.5-regeneration gates.
It is not engineering validation, contractual acceptance, bidder compliance,
or promotion of the expected v0.6 counts.

----END FILE: docs/QPS_RTM_REAL_WORKLOAD_PROOF.md

----FILE: triage/W289_QPS_AUTHORITY_GUARD_P1_REPAIR.yaml
schema: gbogeb.codespaces_jupyter.w289_qps_authority_guard_repair/v1
as_of: "2026-09-22T19:13:00+02:00"
mission: W289_QPS_REAL_WORKLOAD_NON_COMPENSATING_GUARD_REPAIR
repository: GBOGEB/codespaces-jupyter
base_main: d589aaad01ddbf37f8020a448cd847539583bb23
origin:
  merged_pr: 5
  merged_w288_head: e23965cd1ee9485eeff1168a2b3d98fb6c4b603f
  merged_commit: d589aaad01ddbf37f8020a448cd847539583bb23
  codex_finding_id: 4074272043
  severity: P1
  finding: VALIDATE_AUTHORITY_GUARDS_INSTEAD_OF_HARD_CODING
reason:
  - W288 merged before the final Codex review completed
  - final Codex review identified a material non-compensating authority-guard defect
  - main therefore requires a bounded post-merge repair
repair:
  source_fixture_validation:
    - baseline authority_transfer must be false
    - baseline formal_credit_delta must be zero
    - baseline status must be PASS
    - expected state must be EXPECTED_NOT_YET_CREDITED
    - expected authority_transfer must be false
    - formal_credit_delta must be zero
    - engineering_credit_delta must be zero
    - negotiation_credit_delta must be zero
    - compliance_credit_delta must be zero
    - exact-v0.5 regeneration promotion gate must equal the controlled statement
  receipt:
    - authority and credit values are emitted from the validated expected fixture
    - guard_validation is persisted in workload_receipt.json
  ci:
    - guard_validation.all_non_compensating_guards_passed must be true
    - authority_transfer must be false
    - all four credit deltas must be zero
  notebook:
    - guard validation is executed and displayed before the calculation
review_followup:
  codex_finding_id: 4074342402
  severity: P2
  finding: REJECT_BOOLEAN_CREDIT_DELTAS_INSTEAD_OF_TREATING_THEM_AS_ZERO
  repair:
    - numeric-zero validation requires int or float, explicitly excludes bool, and value equals zero
    - baseline formal credit uses strict numeric-zero validation
    - all expected credit deltas use strict numeric-zero validation
    - CI repeats the strict numeric-zero and non-bool assertion
sequence:
  3PR:
    refresh: PASS
    probe: PASS
    rank: PASS_P1_NON_COMPENSATING_GUARD_DEFECT
  MIP:
    modernize: PASS_SOURCE_GUARDS_FAIL_CLOSED
    innovate: PASS_RECEIPT_SOURCE_DERIVED_AUTHORITY_STATE
    perpetuate: PASS_CI_ASSERTS_NON_COMPENSATING_GUARDS
  3PC:
    prepare: PASS_REPAIR_BRANCH_MATERIALIZED
    prove: PENDING_POST_P2_EXACT_HEAD_RECERTIFICATION
    commit: PENDING_REVIEW_MERGE
  3P3: NOT_AUTHORIZED_BEFORE_REPAIR_PROVE_AND_COMMIT
authority_transfer: false
formal_credit_delta: 0
engineering_credit_delta: 0
negotiation_credit_delta: 0
compliance_credit_delta: 0

----END FILE: triage/W289_QPS_AUTHORITY_GUARD_P1_REPAIR.yaml

----FILE: handover/SC_2026-09-22_W289_QPS_AUTHORITY_GUARD_P1_REPAIR_v1.md
# W289 lossless handover - QPS authority-guard P1 repair

Repository: GBOGEB/codespaces-jupyter

## Why W289 exists

W288 PR #5 merged at d589aaad01ddbf37f8020a448cd847539583bb23
before its final requested Codex review completed. That review subsequently
raised material P1 finding 4074272043 against merged code.

The issue was not the reproduced QPS count calculation. The issue was that the
workload receipt hard-coded no-authority / zero-credit values rather than
rejecting source-backed fixtures that contradicted those guards. That could make
the exact-v0.5 regeneration and zero-credit conditions compensating.

## Repair

W289 changes only the bounded proof/control layer:

- validate baseline authority_transfer=false;
- validate baseline formal_credit_delta=0 and baseline status=PASS;
- validate expected state=EXPECTED_NOT_YET_CREDITED;
- validate expected authority_transfer=false;
- validate formal, engineering, negotiation and compliance credit deltas are 0;
- require the controlled exact-v0.5 regeneration promotion gate verbatim;
- emit authority and credit values from the validated fixture;
- persist guard_validation in workload_receipt.json;
- make CI assert guard_validation and all zero-credit/no-authority fields;
- expose guard validation in the real QPS notebook before calculation.

The QPS expected calculation remains unchanged. The exact source v0.5 workbook
binary regeneration gate in GBOGEB/cryoplant-project remains separate and
unsatisfied by this runtime proof.

## P2 follow-up

Codex review of exact head 01f864e2e9becaeb616706990c75010d96ae9c61
raised P2 finding 4074342402: Python treats False == 0, so a JSON boolean could
incorrectly satisfy a zero-credit check. The repair now defines numeric zero as
an int or float that is not bool and equals zero. The baseline formal-credit
field, all expected credit fields, and CI receipt verification use that strict
check.

The earlier exact-head proof remains historical evidence for the P1 repair, but
3PC Prove is reset until the P2-repaired final head is recertified.

## Exact next gate

Open the W289 repair PR, obtain exact-head qps-project-workload-proof and generic
runtime proof, then request final review. Require the project workflow to show:
more than zero executed notebook cells on both runs, equal notebook outputs,
PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION, and
guard_validation.all_non_compensating_guards_passed=true.

Merge only after the material P1 is repaired and the exact-head proof is green.
Then emit the MissionControl closure receipt.

No authority transfer. All formal, engineering, negotiation and compliance
credit deltas remain zero.

----END FILE: handover/SC_2026-09-22_W289_QPS_AUTHORITY_GUARD_P1_REPAIR_v1.md

----END OF PATCH ALL W289
