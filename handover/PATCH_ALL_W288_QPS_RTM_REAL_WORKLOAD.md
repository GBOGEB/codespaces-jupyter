# W288 recursive real-workload patch

Base: 30e537298de8a25a78e162be590d1d5763641147

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
              assert data[key] == 0
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

----FILE: .gitignore
notebooks/data
notebooks/cifar_net.pth
.ipynb_checkpoints/
artifacts/runtime_probe/
artifacts/qps_rtm_workload/
artifacts/qps_rtm_partial_relax_probe/

----END FILE: .gitignore

----FILE: Makefile
PYTHON ?= python
ENV_NAME ?= gbogeb-jupyter
PROBE_NOTEBOOK ?= notebooks/runtime_probe.ipynb
PROBE_OUT ?= artifacts/runtime_probe
QPS_WORKLOAD_NOTEBOOK ?= notebooks/qps_rtm_partial_relax_workload.ipynb
QPS_WORKLOAD_PROBE_OUT ?= artifacts/qps_rtm_partial_relax_probe

.PHONY: runtime scoopo coco sync doctor probe report jupyter smoke qps-workload qps-workload-proof clean-probe clean-qps-workload

runtime:
	$(PYTHON) -m pip install -r requirements.txt

scoopo:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-ide.txt

coco:
	conda env create -f environment.yml || conda env update -n $(ENV_NAME) -f environment.yml
	conda run -n $(ENV_NAME) python -m pip install -r requirements-ide.txt

sync:
	$(PYTHON) scripts/git_sync_guard.py --pull

doctor:
	$(PYTHON) scripts/git_sync_guard.py

probe:
	$(PYTHON) scripts/runtime_probe.py --notebook $(PROBE_NOTEBOOK) --output-dir $(PROBE_OUT)

qps-workload:
	$(PYTHON) scripts/qps_rtm_workload.py

qps-workload-proof:
	$(PYTHON) scripts/runtime_probe.py --notebook $(QPS_WORKLOAD_NOTEBOOK) --output-dir $(QPS_WORKLOAD_PROBE_OUT)

report: probe
	@echo "Open $(PROBE_OUT)/HUMAN_REVIEW.md and $(PROBE_OUT)/receipt.json"

jupyter:
	$(PYTHON) -m jupyterlab .

smoke:
	$(PYTHON) -m compileall -q scripts
	$(PYTHON) scripts/git_sync_guard.py
	$(PYTHON) scripts/runtime_probe.py --notebook $(PROBE_NOTEBOOK) --output-dir $(PROBE_OUT)

clean-probe:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(PROBE_OUT)', ignore_errors=True)"

clean-qps-workload:
	$(PYTHON) -c "import shutil; shutil.rmtree('artifacts/qps_rtm_workload', ignore_errors=True); shutil.rmtree('$(QPS_WORKLOAD_PROBE_OUT)', ignore_errors=True)"

----END FILE: Makefile

----FILE: requirements-probe.txt
ipykernel>=6,<7
nbclient>=0.10,<1
nbformat>=5,<6
openpyxl>=3.1,<4

----END FILE: requirements-probe.txt

----FILE: data/qps_rtm_partial_relax_v06/baseline_v05.json
{
  "source_repository": "GBOGEB/cryoplant-project",
  "source_commit": "339a1682236d5dc0ccae5cf6d6df26d9f510d6b8",
  "source_path": "controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V05_VALIDATION_RECEIPT_20260922.json",
  "source_blob_sha": "7de067615cedd805207f480bdc018638c56180c4",
  "atomic_rows": 295,
  "authority_transfer": false,
  "coverage_states": {
    "ATOMIZED_SOURCE_BACKED": 88,
    "LKT_SCOPE_INTERPRETATION_BOUND": 5,
    "LKT_SECTION_FAMILY_ALIGNMENT_PENDING": 55,
    "SOURCE_EXTRACTION_REQUIRED": 574
  },
  "formal_credit_delta": 0,
  "peer_queues": {
    "ALAT_ONLY": 80,
    "BOTH_CHALLENGE_SAME_ATOM": 75,
    "LKT_ONLY": 47,
    "PROTECTED_REMAINDER": 93
  },
  "remaining_family_frontier": {
    "TEC_ID_034": 11,
    "TEC_ID_144": 34,
    "TEC_ID_205": 10,
    "TEC_ID_206": 10,
    "TEC_ID_207": 10
  },
  "rtm_denominator": 722,
  "sha256": "95c5129c217c73c6d93d604f1c012f0008f3029c60141ff9a651b6c74304243b",
  "status": "PASS",
  "workbook": "QPS_Cross_Bidder_Partial_Relaxation_Matrix_v0_5.xlsx"
}

----END FILE: data/qps_rtm_partial_relax_v06/baseline_v05.json

----FILE: data/qps_rtm_partial_relax_v06/bindings.csv
native_id,lkt_locator,canonical_target,canonical_child,alat_native_ref,alat_state,lkt_state,queue_after_regeneration,exact_binding
TEC_ID_034,"LKT_EXCEPTIONS_263 / UID TEC_ID_034; PDF p.58",RTM-138,"Analysed gas samples shall be recovered and returned to the QPS.","Rev 0 / Item ID 873 / RTM-138",Compliant,Clarification,LKT_ONLY,true
TEC_ID_205,"LKT_EXCEPTIONS_263 / UID TEC_ID_205; PDF p.66",RTM-691,"These responsibilities shall be clearly reflected in the Responsibility Matrix and the Codes and Standards Register which form part of the continuously updated QAP.","Rev 0 / Item ID 3067 / RTM-691",Compliant,Deviation,LKT_ONLY,true
TEC_ID_206,"LKT_EXCEPTIONS_263 / UID TEC_ID_206; PDF p.66",RTM-693,"The Contractor shall submit the Technical File well before the shipment of the first QPS parts.","Rev 0 / Item ID 3069 / RTM-693",Suggestion,Deviation,BOTH_CHALLENGE_SAME_ATOM,true
TEC_ID_207,"LKT_EXCEPTIONS_263 / UID TEC_ID_207; PDF p.66",RTM-695,"If requested by SCK CEN, the Contractor shall submit an updated version of the Technical File including more detail on specific section to demonstrate conformity with the directive(s) in more detail.","Rev 0 / Item ID 3084 / RTM-695",Deviation,Deviation,BOTH_CHALLENGE_SAME_ATOM,true
TEC_ID_144,"LKT_EXCEPTIONS_263 / UID TEC_ID_144; PDF p.63",RTM-521,"The flow conditions at headers A, B, D, E, and W.","Rev 0 / Item ID 2323 / RTM-521",Suggestion,Clarification,BOTH_CHALLENGE_SAME_ATOM,true

----END FILE: data/qps_rtm_partial_relax_v06/bindings.csv

----FILE: data/qps_rtm_partial_relax_v06/expected_v06.json
{
  "source_repository": "GBOGEB/cryoplant-project",
  "source_commit": "339a1682236d5dc0ccae5cf6d6df26d9f510d6b8",
  "source_path": "controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V06_RECENSUS_CONTROL_20260922.yaml",
  "source_blob_sha": "084f7f515cd5fd27e10bca820533c052a70dd48e",
  "state": "EXPECTED_NOT_YET_CREDITED",
  "canonical_rtm_denominator": 722,
  "atomic_rows": 300,
  "peer_queues": {
    "BOTH_CHALLENGE_SAME_ATOM": 78,
    "ALAT_ONLY": 80,
    "LKT_ONLY": 49,
    "PROTECTED_REMAINDER": 93
  },
  "parent_screening": {
    "ATOMIZED_SOURCE_BACKED": 93,
    "LKT_SECTION_FAMILY_ALIGNMENT_PENDING": 50,
    "LKT_SCOPE_INTERPRETATION_BOUND": 5,
    "SOURCE_EXTRACTION_REQUIRED": 574
  },
  "ranked_v05_family_frontier_remaining": 0,
  "promotion_gate": "exact source v0.5 binary must be regenerated and the emitted receipt must PASS before these become the current workbook counts",
  "authority_transfer": false,
  "formal_credit_delta": 0,
  "engineering_credit_delta": 0,
  "negotiation_credit_delta": 0,
  "compliance_credit_delta": 0
}

----END FILE: data/qps_rtm_partial_relax_v06/expected_v06.json

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
    if baseline.get("formal_credit_delta") != 0:
        failures.append("baseline formal_credit_delta must be zero")
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
        if expected.get(key) != 0:
            failures.append(f"{key} must be zero")
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

----FILE: triage/W288_QPS_RTM_REAL_WORKLOAD_3PSTAR_MIP.yaml
schema: gbogeb.codespaces_jupyter.w288_qps_real_workload/v1
as_of: "2026-09-22T19:05:00+02:00"
mission: W288_QPS_RTM_REAL_WORKLOAD_REPRODUCIBILITY
repository: GBOGEB/codespaces-jupyter
base_sha: 30e537298de8a25a78e162be590d1d5763641147
source_repository:
  repo: GBOGEB/cryoplant-project
  commit: 339a1682236d5dc0ccae5cf6d6df26d9f510d6b8
  baseline_control:
    path: controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V05_VALIDATION_RECEIPT_20260922.json
    blob_sha: 7de067615cedd805207f480bdc018638c56180c4
  v06_control:
    path: controls/qps_partial_relaxation/QPS_PARTIAL_RELAX_V06_RECENSUS_CONTROL_20260922.yaml
    blob_sha: 084f7f515cd5fd27e10bca820533c052a70dd48e
sequence:
  3PR:
    refresh: PASS
    probe: PASS
    rank: PASS
    selected_first_red: SYNTHETIC_RUNTIME_PROOF_WITHOUT_REAL_QPS_WORKLOAD
  MIP:
    modernize: PASS_SOURCE_BACKED_QPS_FIXTURE_AND_EXCEL_ROUNDTRIP
    innovate: PASS_SEMANTIC_WORKBOOK_DIGEST_EXPECTED_COUNT_AND_FAIL_CLOSED_AUTHORITY_GUARDS
    perpetuate: PASS_EXACT_HEAD_PROJECT_WORKLOAD_CI_HANDOVER
  3PC:
    prepare: PASS_CANDIDATE_MATERIALIZED
    prove: PENDING_POST_REVIEW_REPAIR_EXACT_HEAD_RECERTIFICATION
    commit: PENDING_REVIEW_MERGE
  3P3: NOT_AUTHORIZED_BEFORE_3PC_PROVE_AND_COMMIT
review_repair:
  codex_review_commit: e23965cd1ee9485eeff1168a2b3d98fb6c4b603f
  finding_id: 4074272043
  severity: P1
  finding: VALIDATE_AUTHORITY_GUARDS_INSTEAD_OF_HARD_CODING
  repair:
    - baseline authority_transfer must be false
    - baseline formal_credit_delta must be zero
    - baseline validation status must be PASS
    - expected state must remain EXPECTED_NOT_YET_CREDITED
    - expected authority_transfer must be false
    - all expected credit deltas must be zero
    - exact v0.5 regeneration promotion gate must match the non-compensating controlled statement
    - receipt authority and credit fields are emitted from the validated source fixture rather than hard-coded
    - CI explicitly asserts non-compensating guard validation
    - notebook exposes the guard validation result
pre_repair_exact_head_evidence:
  candidate_sha: e23965cd1ee9485eeff1168a2b3d98fb6c4b603f
  workflow_run: 35757662766
  job_id: 106847428414
  result: SUCCESS_BUT_SUPERSEDED_BY_P1_REPAIR
  executed_code_cells_each_run: 3
  notebook_output_digest: 8f6fd9a684e797fdecf402cf460cdf450734fbe443068e15a9049f821c04b8a1
  workload_status: PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION
  excel_semantic_sha256: fb9be281accf5760fc0dd64e69d600356fc0ef0e1c1d467c73f173de9318edcc
  normalized_csv_sha256: 78ac78cbf4ac875c7039d6015a715062754442a800be8a3d4627b851e421923a
  artifact_id: 10708043513
  artifact_zip_sha256: 928802074ade3716f36b3d1ebacc089670b0e6f75b7606c9f0e5cc1a18f47782
  note: runtime evidence remains historical; it is not the final 3PC proof after the P1 repair
expected_project_workload:
  atomic_rows: 300
  peer_queues:
    BOTH_CHALLENGE_SAME_ATOM: 78
    ALAT_ONLY: 80
    LKT_ONLY: 49
    PROTECTED_REMAINDER: 93
  parent_screening:
    ATOMIZED_SOURCE_BACKED: 93
    LKT_SECTION_FAMILY_ALIGNMENT_PENDING: 50
    LKT_SCOPE_INTERPRETATION_BOUND: 5
    SOURCE_EXTRACTION_REQUIRED: 574
authority_transfer: false
formal_credit_delta: 0
engineering_credit_delta: 0
negotiation_credit_delta: 0
compliance_credit_delta: 0
claim_guards:
  - EXPECTED_V06_NE_PROMOTED_CURRENT_STATE
  - REAL_WORKLOAD_REPRODUCIBILITY_NE_ENGINEERING_VALIDATION
  - REAL_WORKLOAD_REPRODUCIBILITY_NE_CONTRACTUAL_ACCEPTANCE
  - EXACT_V05_WORKBOOK_REGENERATION_REMAINS_SEPARATE

----END FILE: triage/W288_QPS_RTM_REAL_WORKLOAD_3PSTAR_MIP.yaml

----FILE: handover/SC_2026-09-22_W288_QPS_RTM_REAL_WORKLOAD_v1.md
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

----END FILE: handover/SC_2026-09-22_W288_QPS_RTM_REAL_WORKLOAD_v1.md

----END OF PATCH ALL W288
