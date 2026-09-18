# GBOGEB Codespaces Jupyter Runtime

Governed reproducible notebook runtime for the GBOGEB federation.

This repository is GitHub-backed and is intended to be the shared runtime
boundary between local Jupyter/Spyder work, Codespaces, GitHub Actions, MCP
repository mutation, and Red Hat execution. Local machines do **not** share a
working directory with MCP or CI; GitHub is the synchronization intermediate.

## Quick start

```bash
git clone https://github.com/GBOGEB/codespaces-jupyter.git
cd codespaces-jupyter
make scoopo
make probe
```

For a conda-first environment:

```bash
make coco
```

Start JupyterLab from the repository root:

```bash
make jupyter
```

## Refresh after remote GitHub/MCP work

```bash
git switch main
make sync
```

The sync guard refuses dirty, diverged, or locally-ahead states and only
fast-forwards a clean clone from `origin/main`.

## Governed runtime proof

`make probe` executes `notebooks/runtime_probe.ipynb` twice. Success requires:

- more than zero executed code cells on both runs;
- identical canonical output digests;
- an exact repository source SHA;
- a human-readable RYG review receipt.

Outputs are written below `artifacts/runtime_probe/`. GitHub Actions runs the
same probe on relevant pull requests.

## IDE and MCP integration

See `docs/GITHUB_FIRST_IDE_MCP_WORKFLOW.md` for Jupyter, Spyder, GitHub MCP,
local Git and GBOGEB_RH / RHEL operating rules.

## Authority guard

Notebook execution and repository mutation are runtime/tooling evidence only.
They do not confer engineering or domain-validation authority.
