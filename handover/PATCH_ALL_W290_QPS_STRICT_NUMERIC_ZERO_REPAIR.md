# W290 recursive strict numeric-zero post-merge repair patch

Base: 3902e0edb18230e9236e48acfb36ce65b66732bc

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

----FILE: scripts/qps_guard_negative_probe.py
#!/usr/bin/env python3
"""Negative probe proving QPS authority guards fail closed on unsafe fixture mutations."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.qps_rtm_workload import load_inputs, validate_authority_guards


def must_reject(name: str, baseline: dict, expected: dict) -> str:
    try:
        validate_authority_guards(baseline, expected)
    except ValueError:
        return name
    raise AssertionError(f"guard mutation unexpectedly accepted: {name}")


def main() -> int:
    baseline, _rows, expected = load_inputs()
    positive = validate_authority_guards(baseline, expected)
    assert positive["all_non_compensating_guards_passed"] is True

    rejected: list[str] = []

    b = copy.deepcopy(baseline)
    b["authority_transfer"] = True
    rejected.append(must_reject("baseline_authority_transfer_true", b, copy.deepcopy(expected)))

    b = copy.deepcopy(baseline)
    b["formal_credit_delta"] = False
    rejected.append(must_reject("baseline_formal_credit_false", b, copy.deepcopy(expected)))

    b = copy.deepcopy(baseline)
    b["formal_credit_delta"] = 1
    rejected.append(must_reject("baseline_formal_credit_nonzero", b, copy.deepcopy(expected)))

    b = copy.deepcopy(baseline)
    b["status"] = "FAIL"
    rejected.append(must_reject("baseline_status_fail", b, copy.deepcopy(expected)))

    e = copy.deepcopy(expected)
    e["state"] = "PROMOTED"
    rejected.append(must_reject("expected_state_promoted", copy.deepcopy(baseline), e))

    e = copy.deepcopy(expected)
    e["authority_transfer"] = True
    rejected.append(must_reject("expected_authority_transfer_true", copy.deepcopy(baseline), e))

    for key in (
        "formal_credit_delta",
        "engineering_credit_delta",
        "negotiation_credit_delta",
        "compliance_credit_delta",
    ):
        e = copy.deepcopy(expected)
        e[key] = False
        rejected.append(must_reject(f"{key}_boolean_false", copy.deepcopy(baseline), e))

        e = copy.deepcopy(expected)
        e[key] = 1
        rejected.append(must_reject(f"{key}_nonzero", copy.deepcopy(baseline), e))

    e = copy.deepcopy(expected)
    e["promotion_gate"] = "workload proof may promote counts"
    rejected.append(must_reject("promotion_gate_weakened", copy.deepcopy(baseline), e))

    receipt = {
        "schema": "gbogeb.qps_guard_negative_probe/v1",
        "status": "PASS_GUARDS_FAIL_CLOSED",
        "positive_fixture_passed": True,
        "rejected_mutation_count": len(rejected),
        "rejected_mutations": rejected,
        "authority_transfer": False,
        "credit_delta": 0,
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

----END FILE: scripts/qps_guard_negative_probe.py

----FILE: .github/workflows/qps-project-workload.yml
name: qps-project-workload-proof

on:
  pull_request:
    paths:
      - "data/qps_rtm_partial_relax_v06/**"
      - "notebooks/qps_rtm_partial_relax_workload.ipynb"
      - "scripts/qps_rtm_workload.py"
      - "scripts/qps_guard_negative_probe.py"
      - "scripts/runtime_probe.py"
      - "requirements-probe.txt"
      - "Makefile"
      - "docs/QPS_RTM_REAL_WORKLOAD_PROOF.md"
      - "triage/W288_QPS_RTM_REAL_WORKLOAD_3PSTAR_MIP.yaml"
      - "handover/SC_2026-09-22_W288_QPS_RTM_REAL_WORKLOAD_v1.md"
      - "handover/PATCH_ALL_W288_QPS_RTM_REAL_WORKLOAD.md"
      - "triage/W289_QPS_AUTHORITY_GUARD_P1_REPAIR.yaml"
      - "handover/SC_2026-09-22_W289_QPS_AUTHORITY_GUARD_P1_REPAIR_v1.md"
      - "handover/PATCH_ALL_W289_QPS_AUTHORITY_GUARD_P1_REPAIR.md"
      - "triage/W290_QPS_STRICT_NUMERIC_ZERO_REPAIR.yaml"
      - "handover/SC_2026-09-23_W290_QPS_STRICT_NUMERIC_ZERO_REPAIR_v1.md"
      - "handover/PATCH_ALL_W290_QPS_STRICT_NUMERIC_ZERO_REPAIR.md"
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
      - name: Prove authority guards fail closed
        run: PYTHONDONTWRITEBYTECODE=1 python scripts/qps_guard_negative_probe.py
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

----FILE: triage/W290_QPS_STRICT_NUMERIC_ZERO_REPAIR.yaml
schema: gbogeb.codespaces_jupyter.w290_qps_strict_numeric_zero_repair/v1
as_of: "2026-09-23T11:18:00+02:00"
mission: W290_QPS_REAL_WORKLOAD_STRICT_NUMERIC_ZERO_POSTMERGE_REPAIR
repository: GBOGEB/codespaces-jupyter
base_main: 3902e0edb18230e9236e48acfb36ce65b66732bc
origin:
  merged_pr: 6
  merged_commit: 3902e0edb18230e9236e48acfb36ce65b66732bc
  codex_finding_id: 4074342402
  severity: P2
  finding: REJECT_BOOLEAN_CREDIT_DELTAS_INSTEAD_OF_TREATING_THEM_AS_ZERO
reason:
  - PR 6 merged before the post-review P2 repair commits were part of main
  - Python bool is a subclass of int and False == 0
  - zero-credit guards therefore require type-sensitive numeric-zero validation
repair:
  implementation:
    - add is_numeric_zero(value)
    - accept int or float zero only
    - explicitly reject bool
    - apply to baseline formal_credit_delta
    - apply to all expected formal/engineering/negotiation/compliance credit deltas
  negative_probe:
    - mutate baseline authority transfer true
    - mutate baseline formal credit to false and nonzero
    - mutate baseline status to FAIL
    - mutate expected state to PROMOTED
    - mutate expected authority transfer true
    - mutate each expected credit delta to false and nonzero
    - weaken exact-v0.5 promotion gate
    - require every mutation to be rejected
  ci:
    - run negative guard probe before notebook with PYTHONDONTWRITEBYTECODE=1
    - require strict numeric-zero and non-bool receipt values
    - preserve exact-head notebook repeat/digest and artifact receipt
    - bind W290 handover filter to the committed 2026-09-23 path
execution_history:
  - sha: aafb70de3c1ee0c29fded66e73f8dc66bfa4c946
    run: 35841827953
    result: FAIL
    first_red: NEGATIVE_PROBE_IMPORT_PATH
    repair: fc4bbd74127a013246a15fe819e1b04b70670222
  - sha: fc4bbd74127a013246a15fe819e1b04b70670222
    run: 35841901158
    result: FAIL
    first_red: NEGATIVE_PROBE_CREATED_PYCACHE_DIRTY_TREE
    repair: 05ba30e279055e31483cc08c1b1f51e5136577ce
  - sha: 05ba30e279055e31483cc08c1b1f51e5136577ce
    run: 35842012607
    job: 107119065381
    result: PASS_CANDIDATE_PROOF
    guard_negative_probe:
      status: PASS_GUARDS_FAIL_CLOSED
      rejected_mutation_count: 15
    notebook:
      executed_code_cells_each_run: 3
      equal_output_digest: a1f2a771bf4dbaa69a133ef793fd15d8e4755c17fbd4cf5133066fe1479c6c2a
    workload_receipt: PASS_REPRODUCED_EXPECTED_V06_CALCULATION_NOT_PROMOTION
    excel_semantic_sha256: fb9be281accf5760fc0dd64e69d600356fc0ef0e1c1d467c73f173de9318edcc
    normalized_csv_sha256: 78ac78cbf4ac875c7039d6015a715062754442a800be8a3d4627b851e421923a
    artifact_id: 10740834822
    artifact_zip_sha256: c63b80d0e203492133347be593613b11665b3716d64c6d6357134d2e6d961d84
    note: HISTORICAL_CANDIDATE_PROOF_REQUIRES_FINAL_SERIALIZED_HEAD_RECERTIFICATION
review:
  reviewed_sha: aafb70de3c1ee0c29fded66e73f8dc66bfa4c946
  findings:
    - id: 4080848699
      severity: P1
      finding: MAKE_WORKLOAD_MODULE_IMPORTABLE_WHEN_RUNNING_PROBE
      disposition: REPAIRED_BY_FC4BBD74127A013246A15FE819E1B04B70670222
    - id: 4080848709
      severity: P2
      finding: MATCH_HANDOVER_FILTER_TO_COMMITTED_W290_FILENAME
      disposition: REPAIRED_BY_35E3DBC592115AA2856B072329E19C52C395DD8A
sequence:
  3PR:
    refresh: PASS
    probe: PASS
    rank: PASS_P2_TYPE_SAFETY_NON_COMPENSATING_GUARD
  MIP:
    modernize: PASS_STRICT_NUMERIC_ZERO_GUARD
    innovate: PASS_NEGATIVE_MUTATION_PROOF
    perpetuate: PASS_EXACT_HEAD_CI_AND_DURABLE_HANDOVER
  3PC:
    prepare: PASS_REPAIR_BRANCH_MATERIALIZED
    prove: PENDING_FINAL_SERIALIZED_HEAD_RECERTIFICATION
    commit: PENDING_FINAL_REVIEW_AND_MERGE
  3P3: NOT_AUTHORIZED_BEFORE_W290_PROVE_AND_COMMIT
authority_transfer: false
formal_credit_delta: 0
engineering_credit_delta: 0
negotiation_credit_delta: 0
compliance_credit_delta: 0
claim_guards:
  - REAL_WORKLOAD_REPRODUCIBILITY_NE_ENGINEERING_VALIDATION
  - EXPECTED_V06_NE_PROMOTED_CURRENT_STATE
  - EXACT_V05_WORKBOOK_REGENERATION_REMAINS_SEPARATE
  - BOOLEAN_FALSE_NE_NUMERIC_ZERO_FOR_CREDIT_GATES

----END FILE: triage/W290_QPS_STRICT_NUMERIC_ZERO_REPAIR.yaml

----FILE: handover/SC_2026-09-23_W290_QPS_STRICT_NUMERIC_ZERO_REPAIR_v1.md
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

----END FILE: handover/SC_2026-09-23_W290_QPS_STRICT_NUMERIC_ZERO_REPAIR_v1.md

----END OF PATCH ALL W290
