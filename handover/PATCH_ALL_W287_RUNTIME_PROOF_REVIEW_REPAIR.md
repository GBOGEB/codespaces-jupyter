# W287 recursive repair patch

Base: `98fedcf1147e5bb53e5f833b8a1c5cebb6ded3f9`.

----FILE: .gitignore
notebooks/data
notebooks/cifar_net.pth
.ipynb_checkpoints/
artifacts/runtime_probe/

----END FILE: .gitignore

----FILE: requirements.txt
ipywidgets==8.1.2
ipykernel>=6,<7
nbclient>=0.10,<1
nbformat>=5,<6
matplotlib==3.8.4
pandas==2.2.2
torch==2.7.1
torchvision==0.22.1
tqdm==4.66.4

----END FILE: requirements.txt

----FILE: requirements-probe.txt
ipykernel>=6,<7
nbclient>=0.10,<1
nbformat>=5,<6

----END FILE: requirements-probe.txt

----FILE: .github/workflows/runtime-probe.yml
name: governed-runtime-probe

on:
  pull_request:
    paths:
      - "requirements.txt"
      - "requirements-probe.txt"
      - "requirements-ide.txt"
      - "notebooks/**"
      - "scripts/runtime_probe.py"
      - "Makefile"
      - ".github/workflows/runtime-probe.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  reproducibility:
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
      - name: Install probe dependencies
        run: python -m pip install -r requirements-probe.txt
      - name: Execute notebook twice
        run: python scripts/runtime_probe.py --notebook notebooks/runtime_probe.ipynb --output-dir artifacts/runtime_probe
      - name: Upload exact-head runtime receipt
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: governed-runtime-probe-${{ github.event.pull_request.head.sha || github.sha }}
          path: artifacts/runtime_probe/
          if-no-files-found: error

----END FILE: .github/workflows/runtime-probe.yml

----FILE: scripts/runtime_probe.py
#!/usr/bin/env python3
"""Execute one notebook twice and emit an exact-source reproducibility receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import nbformat
from nbclient import NotebookClient


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_source_state() -> tuple[str, list[str]]:
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        text=True,
        capture_output=True,
    )
    if head.returncode != 0 or not head.stdout.strip():
        raise RuntimeError("exact-source proof requires a valid Git commit")

    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        text=True,
        capture_output=True,
        check=True,
    )
    dirty_entries = [line for line in status.stdout.splitlines() if line.strip()]
    if dirty_entries:
        raise RuntimeError(
            "exact-source proof requires a clean Git tree; dirty entries: "
            + "; ".join(dirty_entries)
        )
    return head.stdout.strip(), dirty_entries


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): normalize_json(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [normalize_json(v) for v in value]
    if isinstance(value, bytes):
        return {"__bytes_sha256__": sha256_bytes(value)}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def canonical_outputs(nb) -> list:
    cells = []
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        outputs = []
        for output in cell.get("outputs", []):
            kind = output.get("output_type")
            if kind == "stream":
                outputs.append({
                    "type": kind,
                    "name": output.get("name"),
                    "text": normalize_json(output.get("text", "")),
                })
            elif kind in {"execute_result", "display_data"}:
                outputs.append({
                    "type": kind,
                    "data": normalize_json(output.get("data", {})),
                })
            elif kind == "error":
                outputs.append({
                    "type": kind,
                    "ename": output.get("ename"),
                    "evalue": output.get("evalue"),
                    "traceback": normalize_json(output.get("traceback", [])),
                })
            else:
                outputs.append({
                    "type": kind,
                    "payload": normalize_json(dict(output)),
                })
        cells.append(outputs)
    return cells


def execute_once(source: Path, target: Path) -> dict:
    notebook = nbformat.read(source, as_version=4)
    executed = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        allow_errors=False,
    ).execute()
    nbformat.write(executed, target)
    code_cells = [cell for cell in executed.cells if cell.get("cell_type") == "code"]
    executed_cells = sum(cell.get("execution_count") is not None for cell in code_cells)
    canonical = canonical_outputs(executed)
    digest = sha256_bytes(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return {
        "executed_code_cells": executed_cells,
        "code_cells": len(code_cells),
        "output_digest": digest,
        "executed_notebook_sha256": sha256_file(target),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", default="notebooks/runtime_probe.ipynb")
    parser.add_argument("--output-dir", default="artifacts/runtime_probe")
    args = parser.parse_args()

    source = Path(args.notebook)
    source_sha, dirty_entries = git_source_state()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    run1 = execute_once(source, out / "run1.executed.ipynb")
    run2 = execute_once(source, out / "run2.executed.ipynb")
    equivalent = run1["output_digest"] == run2["output_digest"]
    gt_zero = run1["executed_code_cells"] > 0 and run2["executed_code_cells"] > 0
    passed = equivalent and gt_zero

    receipt = {
        "schema": "gbogeb.jupyter_runtime_probe_receipt/v2",
        "repository": "GBOGEB/codespaces-jupyter",
        "source_sha": source_sha,
        "source_tree_clean_before_execution": not dirty_entries,
        "source_notebook": str(source),
        "source_notebook_sha256": sha256_file(source),
        "environment_fingerprint": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "requirements_sha256": sha256_file(Path("requirements.txt")),
            "probe_requirements_sha256": sha256_file(Path("requirements-probe.txt")),
        },
        "run1": run1,
        "run2": run2,
        "equivalent_outputs": equivalent,
        "each_run_executed_gt0_cells": gt_zero,
        "status": "PASS_REPRODUCIBLE_GT0_CELLS" if passed else "FAIL_REPRODUCIBILITY",
        "authority_transfer": False,
        "claim_guards": [
            "NOTEBOOK_EXECUTION_NE_ENGINEERING_AUTHORITY",
            "RUNTIME_PASS_NE_DOMAIN_VALIDATION",
        ],
    }
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n",
        encoding="utf-8",
    )

    ryg = "GREEN" if passed else "RED"
    review = f"""# Jupyter runtime probe — human review

| Check | Result |
|---|---|
| Overall | {'🟢' if passed else '🔴'} {ryg} |
| Source SHA | `{source_sha}` |
| Source tree clean before run | YES |
| Run 1 executed cells | {run1['executed_code_cells']} |
| Run 2 executed cells | {run2['executed_code_cells']} |
| Equivalent all-MIME output digest | {'YES' if equivalent else 'NO'} |
| Output digest | `{run1['output_digest']}` |

This is runtime/reproducibility evidence only. It does not confer engineering or
domain-validation authority.
"""
    (out / "HUMAN_REVIEW.md").write_text(review, encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

----END FILE: scripts/runtime_probe.py

----FILE: triage/W287_RUNTIME_PROOF_REVIEW_REPAIR_3PSTAR_MIP.yaml
schema: gbogeb.codespaces_jupyter.w287_review_repair/v1
as_of: "2026-09-18T19:07:00+02:00"
mission: W287_RUNTIME_PROOF_REVIEW_REPAIR
repository: GBOGEB/codespaces-jupyter
parent_pr: 3
parent_merge_sha: 98fedcf1147e5bb53e5f833b8a1c5cebb6ded3f9
failed_run:
  run_id: 35360464702
  job_id: 105650169601
  classification: APPLICATION_PREEXECUTION_DEPENDENCY_CONFLICT
  first_red: TORCHVISION_0_21_0_REQUIRES_TORCH_2_6_0_BUT_TORCH_2_7_1_PINNED
  runner_admitted: true
  steps_executed: true
  notebook_probe_reached: false
codex_review_findings:
  - P1_ALIGN_TORCH_TORCHVISION
  - P2_REQUIRE_CLEAN_VALID_GIT_SOURCE
  - P2_HASH_ALL_MIME_OUTPUTS
  - P2_CHECKOUT_EXACT_PR_HEAD
  - P2_IGNORE_GENERATED_PROBE_ARTIFACTS
sequence:
  3PR:
    refresh: PASS
    probe: PASS
    rank: PASS
    selected_first_red: DEPENDENCY_CONFLICT_AND_EXACT_SOURCE_REVIEW_GAPS
  MIP:
    modernize: PASS_LIGHTWEIGHT_PROBE_REQUIREMENTS
    innovate: PASS_CLEAN_TREE_AND_ALL_MIME_CANONICALIZATION
    perpetuate: PASS_EXACT_HEAD_CI_AND_IGNORED_GENERATED_RECEIPTS
  3PC:
    prepare: PASS_REPAIR_BRANCH_MATERIALIZED
    prove: PENDING_FRESH_EXACT_HEAD_RUN
    commit: PENDING_REVIEW_MERGE
  3P3: NOT_AUTHORIZED_BEFORE_3PC_PROVE_AND_COMMIT
repairs:
  dependency_pair: torch==2.7.1 + torchvision==0.22.1
  probe_dependencies: requirements-probe.txt
  exact_head_checkout: "${{ github.event.pull_request.head.sha || github.sha }}"
  source_clean_guard: git_status_porcelain_must_be_empty
  output_digest: all_MIME_data_representations
  generated_artifacts: ignored_at_artifacts/runtime_probe/
authority_transfer: false
formal_credit_delta: 0
engineering_credit_delta: 0

----END FILE: triage/W287_RUNTIME_PROOF_REVIEW_REPAIR_3PSTAR_MIP.yaml

----FILE: handover/SC_2026-09-18_W287_RUNTIME_PROOF_REVIEW_REPAIR_v1.md
# W287 lossless handover — runtime proof review repair

The original W286 PR #3 merged at
`98fedcf1147e5bb53e5f833b8a1c5cebb6ded3f9`, but its first runtime attempt
`35360464702` obtained a real runner and failed before notebook execution
because `torchvision==0.21.0` required `torch==2.6.0` while the repository
pinned `torch==2.7.1`.

Codex review also identified four proof-integrity gaps: local dirty trees could
claim an old SHA, rich outputs only hashed `text/plain`, PR checkout used the
synthetic merge ref, and generated probe artifacts dirtied the next local sync.

W287 repairs all five items:

1. aligns `torch==2.7.1` with `torchvision==0.22.1`;
2. adds `requirements-probe.txt` so CI proof does not install unrelated heavy packages;
3. rejects missing/dirty Git source before runtime proof;
4. hashes all MIME representations in rich notebook output;
5. checks out the exact PR head and ignores generated probe receipts locally.

The next gate is one fresh exact-head GitHub Actions run with a real runner,
more than zero executed code cells in both passes, equal all-MIME output digests,
and an uploaded receipt bound to the candidate SHA.

No engineering or domain-validation authority is transferred.

----END FILE: handover/SC_2026-09-18_W287_RUNTIME_PROOF_REVIEW_REPAIR_v1.md

----END OF PATCH ALL W287
