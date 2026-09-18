PYTHON ?= python
ENV_NAME ?= gbogeb-jupyter
PROBE_NOTEBOOK ?= notebooks/runtime_probe.ipynb
PROBE_OUT ?= artifacts/runtime_probe

.PHONY: runtime scoopo coco sync doctor probe report jupyter smoke clean-probe

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
