"""Every tunable parameter of the project, in one validated file: configs/project.yaml.

Two kinds of numbers live in this repository and they are kept apart on purpose:
* store policy (14 days, 30 days, 150 EUR ...) -> configs/policy_rules.yaml. Business rules, checked by tests,
  never tuned to make a metric look better.
* experiment parameters (model names, k, error budgets, sample sizes ...) -> configs/project.yaml (this module).

Scripts, the API, the control panel and the Claude tools all read parameters through `settings()`, so a value
changed in the panel is the value the next run uses. Each field carries a description (shown in the panel)
and bounds, so a wrong value fails before a long run starts, not halfway through it.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config import CONFIG_DIR, RESULTS_DIR

PROJECT_FILE = CONFIG_DIR / "project.yaml"


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Project(_Section):
    seed: int = Field(7, ge=0, description="Seed for every random step (splits, sampling, bootstrap). "
                                           "Changing it makes new results incomparable with older runs.")


class LLM(_Section):
    host: str = Field("http://localhost:11434", description="Ollama server address.")
    chat_model: str = Field("qwen2.5:7b", description="Model used by the agent, the RAG answers and the LLM classifier.")
    temperature: float = Field(0.0, ge=0, le=2, description="0 = repeatable answers; keep 0 for evaluation.")
    user_sim_model: str = Field("qwen2.5:7b", description="Model playing the customer in stage 6. "
                                                          "A different model than the agent makes the test harder to game.")
    user_sim_temperature: float = Field(0.7, ge=0, le=2, description="Some randomness makes simulated customers more varied.")
    judge_model: str = Field("qwen2.5:7b", description="Model used as LLM judge (tone, clarity). Validate it against human labels first.")
    timeout_s: float = Field(180, ge=5, le=3600, description="Seconds before one LLM call is abandoned (slow laptops need more).")
    max_retries: int = Field(2, ge=0, le=10, description="Retries for timeouts / connection errors (with exponential backoff).")


class Embeddings(_Section):
    model: str = Field("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                       description="Multilingual sentence encoder (stage 1 classifier and stage 2 dense retrieval).")
    device: Literal["auto", "cpu", "cuda"] = Field("auto", description="auto = GPU if available.")
    batch_size: int = Field(128, ge=1, le=4096, description="Lower it if you run out of memory.")


class Data(_Section):
    bitext_csv: str = Field("", description="Optional local Bitext CSV (if the Hugging Face download fails).")
    wands_dir: str = Field("", description="Folder with WANDS product.csv (reuse the product-search project's copy).")
    clinc_json: str = Field("", description="Optional local CLINC150 data_full.json.")
    n_customers: int = Field(400, ge=10, le=100_000, description="Synthetic customers in shop.db.")
    n_products: int = Field(1500, ge=20, le=50_000, description="Products sampled from WANDS.")
    n_orders: int = Field(2500, ge=50, le=500_000, description="Synthetic orders (11 boundary orders are added on top).")
    test_oos_max: int = Field(300, ge=0, le=5000, description="Out-of-scope (CLINC150) messages added to the test split.")


class Intents(_Section):
    tfidf_C: float = Field(5.0, gt=0, le=1000, description="Inverse regularisation of the TF-IDF logistic regression.")
    embedding_C: float = Field(10.0, gt=0, le=1000, description="Inverse regularisation of the embedding classifier.")
    run_embeddings: bool = Field(True, description="Train the embedding classifier (slow on CPU; fast on Colab GPU).")
    run_llm: bool = Field(True, description="Evaluate the LLM classifier on a sample (needs Ollama, ~1-3 s per message).")
    llm_few_shot_k: int = Field(8, ge=0, le=50, description="Similar training examples put into the LLM prompt (0 = zero-shot).")
    llm_sample_per_intent: int = Field(8, ge=1, le=200, description="Dev messages per intent for the LLM classifier.")
    winner: Literal["tfidf", "embeddings"] = Field("tfidf", description="Model saved for the agent. Choose it on DEV "
                                                                         "(accuracy, ECE, speed), then report it once on test.")


class RAG(_Section):
    k: int = Field(3, ge=1, le=20, description="Chunks given to the LLM (and k of recall@k).")
    mode: Literal["bm25", "dense", "hybrid"] = Field("hybrid", description="Retrieval used by the agent.")
    rrf_k: int = Field(60, ge=1, le=1000, description="Reciprocal Rank Fusion constant; larger = flatter fusion.")
    bm25_k1: float = Field(1.5, ge=0, le=5, description="BM25 term-frequency saturation.")
    bm25_b: float = Field(0.75, ge=0, le=1, description="BM25 length normalisation.")


class Decision(_Section):
    error_budget_low: float = Field(0.05, gt=0, lt=1, description="Max error among automated LOW-risk cases (threshold search).")
    error_budget_medium: float = Field(0.02, gt=0, lt=1, description="Max error among automated MEDIUM-risk cases.")
    error_budget_high: float = Field(0.01, gt=0, lt=1, description="Max error among automated HIGH-risk cases.")
    cost_wrong_action: float = Field(20, gt=0, description="Cost of a wrong automated action (for the cost-based threshold).")
    cost_handoff: float = Field(1, gt=0, description="Cost of one handoff to a human.")
    use_tuned_thresholds: bool = Field(True, description="Agent uses results/thresholds.json from stage 4 (else built-in defaults).")

    @model_validator(mode="after")
    def _riskier_is_stricter(self):
        if not (self.error_budget_high <= self.error_budget_medium <= self.error_budget_low):
            raise ValueError("error budgets must satisfy high <= medium <= low (riskier intents get a stricter budget)")
        return self


class Agent(_Section):
    max_tool_steps: int = Field(5, ge=1, le=20, description="LLM/tool round trips per turn before handing off.")


class Evaluation(_Section):
    n_random_scenarios: int = Field(60, ge=0, le=5000, description="Random scenarios added to the 11 boundary cases.")
    n_run: int = Field(20, ge=1, le=5000, description="Scenarios actually simulated (slow: an LLM on both sides).")
    max_turns: int = Field(8, ge=2, le=30, description="Turn limit per simulated conversation.")
    n_bootstrap: int = Field(2000, ge=100, le=100_000, description="Bootstrap resamples for confidence intervals.")
    repeats: int = Field(1, ge=1, le=10, description="Runs per scenario. >1 measures reliability: pass^k = all k runs "
                                                       "succeed (tau-bench). Costs repeats x time.")


class Robustness(_Section):
    max_noise_level: int = Field(3, ge=0, le=3, description="Noise levels 0..N for the accuracy-vs-noise curve.")
    german_per_intent: int = Field(10, ge=1, le=200, description="Test messages per intent translated to German.")
    translate: bool = Field(True, description="Create the German file to review (needs Ollama). Off = only noise curve.")


class Serving(_Section):
    port: int = Field(8000, ge=1024, le=65535, description="Port of the support API (stage 8).")
    session_ttl_min: int = Field(30, ge=1, le=1440, description="Idle sessions are forgotten after this many minutes.")
    loadtest_users: int = Field(5, ge=1, le=200, description="Concurrent users in the load test.")
    loadtest_requests: int = Field(40, ge=1, le=10_000, description="Total requests in the load test.")
    p95_target_ms: int = Field(4000, ge=50, description="Latency target per turn; the advisor warns above it.")


class Monitoring(_Section):
    psi_alert: float = Field(0.25, gt=0, le=5, description="PSI above this = investigate drift.")
    handoff_ratio_alert: float = Field(1.5, gt=1, le=10, description="Alert if handoff rate grows by this factor.")
    window: int = Field(200, ge=10, le=100_000, description="Traces per window (reference = first, current = last).")


class Experiments(_Section):
    name: str = Field("prompt_v2", min_length=1, description="Experiment name; part of the assignment hash.")
    baseline_rate: float = Field(0.60, gt=0, lt=1, description="Current automation rate (from stage 6).")
    min_detectable_lift: float = Field(0.03, gt=0, lt=1, description="Smallest absolute change worth detecting.")
    alpha: float = Field(0.05, gt=0, lt=0.5, description="False positive rate of the test.")
    power: float = Field(0.8, gt=0.5, lt=1, description="Chance to detect a real effect of the given size.")
    srm_threshold: float = Field(0.001, gt=0, lt=0.1, description="p-value below which the split is considered broken.")
    max_false_automation_increase: float = Field(0.005, ge=0, lt=1, description="Guardrail: allowed increase in false automation.")
    control_n: int = Field(4200, ge=0, description="Readout input: conversations in control.")
    control_automated: int = Field(2520, ge=0, description="Readout input: automated conversations in control.")
    control_false_automation: int = Field(63, ge=0, description="Readout input: false automations in control.")
    treatment_n: int = Field(4180, ge=0, description="Readout input: conversations in treatment.")
    treatment_automated: int = Field(2650, ge=0, description="Readout input: automated conversations in treatment.")
    treatment_false_automation: int = Field(71, ge=0, description="Readout input: false automations in treatment.")


class LoRA(_Section):
    base_model: str = Field("xlm-roberta-base", description="Multilingual encoder fine-tuned on Colab.")
    r: int = Field(16, ge=1, le=256, description="LoRA rank: size of the trainable update.")
    alpha: int = Field(32, ge=1, le=512, description="LoRA scaling (often 2 x r).")
    dropout: float = Field(0.1, ge=0, lt=1, description="Dropout on the LoRA layers.")
    learning_rate: float = Field(5e-4, gt=0, lt=1, description="Higher than full fine-tuning: few weights are trained.")
    epochs: int = Field(3, ge=1, le=50, description="Training epochs.")
    batch_size: int = Field(32, ge=1, le=1024, description="Per-device batch size.")


class Claude(_Section):
    model: str = Field("claude-opus-5-5", description="Claude model for the panel's direct API chat.")
    effort: Literal["low", "medium", "high", "xhigh", "max"] = Field("high", description="Thinking depth vs. cost.")
    max_tokens: int = Field(16000, ge=256, le=128_000, description="Maximum tokens per Claude reply.")
    refusal_fallback: bool = Field(True, description="If Claude declines a request, let the API retry it on a fallback model.")
    max_tool_rounds: int = Field(12, ge=1, le=50, description="Tool calls Claude may chain in one answer.")
    allow_runs: bool = Field(True, description="Claude may start stage runs and tests through its tools.")
    allow_settings_changes: bool = Field(True, description="Claude may change project.yaml through its tools.")


class Settings(_Section):
    project: Project = Project()
    llm: LLM = LLM()
    embeddings: Embeddings = Embeddings()
    data: Data = Data()
    intents: Intents = Intents()
    rag: RAG = RAG()
    decision: Decision = Decision()
    agent: Agent = Agent()
    evaluation: Evaluation = Evaluation()
    robustness: Robustness = Robustness()
    serving: Serving = Serving()
    monitoring: Monitoring = Monitoring()
    experiments: Experiments = Experiments()
    lora: LoRA = LoRA()
    claude: Claude = Claude()

    @field_validator("llm")
    @classmethod
    def _host_has_scheme(cls, v: LLM):
        if not v.host.startswith(("http://", "https://")):
            raise ValueError("llm.host must start with http:// or https://")
        return v


HEADER = ("# Experiment parameters for every stage. Edit here, in the control panel, or through Claude's tools.\n"
          "# Store policy numbers are NOT here: they live in policy_rules.yaml.\n"
          "# Descriptions and allowed ranges: src/support/settings.py (also shown in the panel).\n")


def load(path: Path = PROJECT_FILE) -> Settings:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    return Settings.model_validate(data or {})


@lru_cache
def settings() -> Settings:
    """The current settings (cached per process; scripts are new processes, so they always see the latest file)."""
    return load()


def save(s: Settings, path: Path = PROJECT_FILE) -> None:
    path.write_text(HEADER + yaml.safe_dump(s.model_dump(mode="json"), sort_keys=False, allow_unicode=True),
                    encoding="utf-8")
    settings.cache_clear()


def apply_changes(changes: dict[str, object], path: Path = PROJECT_FILE) -> tuple[Settings, dict]:
    """Apply {"rag.k": 5, "llm.chat_model": "llama3.1:8b"} atomically: all valid -> saved, any invalid -> nothing saved.

    Returns the new settings and {key: (old, new)} for the keys that actually changed.
    """
    current = load(path)
    data = current.model_dump(mode="json")
    diff = {}
    for key, value in changes.items():
        section, _, field = key.partition(".")
        if section not in data or field not in data[section]:
            raise KeyError(f"unknown setting: {key}")
        if data[section][field] != value:
            diff[key] = (data[section][field], value)
        data[section][field] = value
    new = Settings.model_validate(data)        # raises pydantic.ValidationError, file untouched
    if diff:
        save(new, path)
    return new, diff


def schema() -> dict:
    """JSON schema with descriptions and bounds (the panel builds its forms from this)."""
    return Settings.model_json_schema()


# ---------- values derived from settings ----------

def tuned_thresholds() -> dict | None:
    """Stage 4 output, if it exists and use_tuned_thresholds is on. None = the agent uses decision.DEFAULT_THRESHOLDS."""
    path = RESULTS_DIR / "thresholds.json"
    if settings().decision.use_tuned_thresholds and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def error_budgets() -> dict[str, float]:
    d = settings().decision
    return {"low": d.error_budget_low, "medium": d.error_budget_medium, "high": d.error_budget_high}


def encoder_device() -> str | None:
    """None lets sentence-transformers pick (GPU if available)."""
    dev = settings().embeddings.device
    return None if dev == "auto" else dev
