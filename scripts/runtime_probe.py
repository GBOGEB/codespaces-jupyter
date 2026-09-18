#!/usr/bin/env python3
"""Execute one notebook twice and emit an exact-source reproducibility receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], text=True, capture_output=True)
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def canonical_outputs(nb) -> list:
    cells = []
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        outputs = []
        for output in cell.get("outputs", []):
            kind = output.get("output_type")
            if kind == "stream":
                outputs.append({"type": kind, "name": output.get("name"), "text": output.get("text", "")})
            elif kind in {"execute_result", "display_data"}:
                outputs.append({"type": kind, "text/plain": output.get("data", {}).get("text/plain", "")})
            elif kind == "error":
                outputs.append({
                    "type": kind,
                    "ename": output.get("ename"),
                    "evalue": output.get("evalue"),
                    "traceback": output.get("traceback", []),
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
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    run1 = execute_once(source, out / "run1.executed.ipynb")
    run2 = execute_once(source, out / "run2.executed.ipynb")
    source_sha = git_head()
    equivalent = run1["output_digest"] == run2["output_digest"]
    gt_zero = run1["executed_code_cells"] > 0 and run2["executed_code_cells"] > 0
    passed = equivalent and gt_zero

    receipt = {
        "schema": "gbogeb.jupyter_runtime_probe_receipt/v1",
        "repository": "GBOGEB/codespaces-jupyter",
        "source_sha": source_sha,
        "source_notebook": str(source),
        "source_notebook_sha256": sha256_file(source),
        "environment_fingerprint": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "requirements_sha256": sha256_file(Path("requirements.txt")),
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
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    ryg = "GREEN" if passed else "RED"
    review = f"""# Jupyter runtime probe — human review

| Check | Result |
|---|---|
| Overall | {'🟢' if passed else '🔴'} {ryg} |
| Source SHA | `{source_sha}` |
| Run 1 executed cells | {run1['executed_code_cells']} |
| Run 2 executed cells | {run2['executed_code_cells']} |
| Equivalent output digest | {'YES' if equivalent else 'NO'} |
| Output digest | `{run1['output_digest']}` |

This is runtime/reproducibility evidence only. It does not confer engineering or
domain-validation authority.
"""
    (out / "HUMAN_REVIEW.md").write_text(review, encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
