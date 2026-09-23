#!/usr/bin/env python3
"""Negative probe proving QPS authority guards fail closed on unsafe fixture mutations."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.qps_rtm_workload import load_inputs, loads_json_lossless, validate_authority_guards


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

    tiny = loads_json_lossless('{"credit": 1e-400}')["credit"]
    assert tiny == Decimal("1e-400")
    e = copy.deepcopy(expected)
    e["formal_credit_delta"] = tiny
    rejected.append(must_reject("formal_credit_delta_tiny_decimal_nonzero", copy.deepcopy(baseline), e))

    e = copy.deepcopy(expected)
    e["formal_credit_delta"] = 0.0
    rejected.append(must_reject("formal_credit_delta_untrusted_float_zero", copy.deepcopy(baseline), e))

    for token in ("0.0", "0e0", "-0.0"):
        exact_zero = loads_json_lossless(f'{{"credit": {token}}}')["credit"]
        assert isinstance(exact_zero, Decimal)
        e = copy.deepcopy(expected)
        e["formal_credit_delta"] = exact_zero
        guard = validate_authority_guards(copy.deepcopy(baseline), e)
        assert type(guard["formal_credit_delta"]) is int
        assert guard["formal_credit_delta"] == 0
        json.dumps(guard)

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
