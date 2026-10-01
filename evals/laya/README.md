# Laya evaluation (CC-14, optional)

`run_laya_eval.py` scores [Laya](https://github.com/NandhaKishorM/laya) (Apache-2.0, `convaiinnovations/laya`, the `multilingual` subfolder with mmBERT-base, 322M parameters, 644 MB weights) on the three labelled triage sets (84 cases). It uses the same metrics as the rules intake.

**Modes compared:**

- `rules`: the current intake.
- `laya`: the model alone.
- `hybrid`: rules first, with the model allowed only to raise a fact from `unknown` to its dangerous value at probability ≥ 0.8. This is the only mode decision 0002 permits.

It also reports calibration (Brier score and ECE for P(dangerous value)) and per-case CPU latency.

**Setup.** The script runs in an isolated environment, and the backend never imports Laya:

```sh
uv venv .laya-venv
VIRTUAL_ENV=.laya-venv uv pip install "laya==0.3.22" "pydantic>=2.9"
HF_HOME=.hf-cache HF_HUB_DISABLE_XET=1 .laya-venv/bin/python evals/laya/run_laya_eval.py \
  --checkpoint multilingual --device cpu --json evals/laya/results-multilingual-cpu.json
```

Adoption criteria and results are in `docs/experiments/CC-14-laya.md`.
