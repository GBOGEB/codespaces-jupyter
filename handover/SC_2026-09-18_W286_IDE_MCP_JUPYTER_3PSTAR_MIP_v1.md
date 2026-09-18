# W286 lossless handover — GitHub-first IDE/MCP/Jupyter

**Repository:** `GBOGEB/codespaces-jupyter`  
**Base:** `1eba2240a86d1fd2bd6375e2fac481caf645cdde`  
**Authority transfer:** false

## Read first

1. `triage/W286_IDE_MCP_JUPYTER_3PSTAR_MIP.yaml`
2. `docs/GITHUB_FIRST_IDE_MCP_WORKFLOW.md`
3. `Makefile`
4. `scripts/git_sync_guard.py`
5. `scripts/runtime_probe.py`
6. `artifacts/runtime_probe/receipt.json` when produced by CI

## Sequential method state

3PR Refresh → Probe → Rank is complete. The ranked defect was the mismatch
between a real GitHub-backed runtime node and a stale local-only README, plus the
absence of guarded refresh and exact double-run notebook proof.

MIP Modernize → Innovate → Perpetuate is materialized in this branch.

3PC Prepare is complete. 3PC Prove requires the pull-request workflow to execute
the deterministic notebook twice at the exact candidate SHA with more than zero
executed code cells and equal governed output digests. 3PC Commit remains the
review/merge boundary. 3P3 is not authorized before those gates.

## Restart command

After merge, a local operator restarts with:

```bash
git switch main
make sync
make scoopo
make probe
```

For a clean machine, clone first from
`https://github.com/GBOGEB/codespaces-jupyter.git`.

## Non-compensation

A passing notebook proves reproducible runtime only. It does not provide
engineering, procurement, compliance, negotiation, or domain-validation credit.
