# Stage 6: end-to-end evaluation with simulated customers. Slow (LLM on both sides): start with 20 scenarios.
# Parameters: configs/project.yaml -> evaluation.*, llm.user_sim_model, decision.use_tuned_thresholds
# %%
import json, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.agent import Session
from support.config import DB_PATH, RESULTS_DIR
from labkit.metrics import reliability_report
from support.evaluation import build_scenarios, run_scenario, save_results, score, summarize, UserSimulator
from support.runtime import load_classifier, make_agent, make_answerer, make_llm
from support.settings import settings, tuned_thresholds
from support.tools import connect

E = settings().evaluation
classify = load_classifier()
agent_llm = make_llm("agent")
answerer = make_answerer(agent_llm)
print("thresholds:", tuned_thresholds() or "built-in defaults (run stage 4 to tune them)")


def fresh_agent():
    tmp = Path(tempfile.mkdtemp()) / "shop.db"
    shutil.copy(DB_PATH, tmp)                            # every scenario starts from the same clean database
    con = connect(tmp)
    return make_agent(con, llm=agent_llm, classify=classify, answerer=answerer), Session("eval"), con


scenarios = build_scenarios(connect(), n_random=E.n_random_scenarios)
# Boundary cases and security probes first: they are the ones most worth simulating when n_run is small.
scenarios.sort(key=lambda sc: sc.note == "random")
print(len(scenarios), "scenarios, simulating", min(E.n_run, len(scenarios)))

# %%
sim = UserSimulator(make_llm("user_sim"))
results, by_scenario = [], {}
for i, sc in enumerate(scenarios[:E.n_run], 1):
    for rep in range(E.repeats):        # repeats > 1: same scenario again (user simulator samples differently)
        r = run_scenario(fresh_agent, sim, sc, max_turns=E.max_turns)
        r["repeat"] = rep
        by_scenario.setdefault(sc.scenario_id, []).append(score(r)["success"])
        if rep == 0:
            results.append(r)           # point metrics and CIs use the first run of each scenario
        print(f"[{i}/{min(E.n_run, len(scenarios))}#{rep + 1}] {sc.scenario_id} expected={sc.expected} outcome={r['outcome']}")
save_results(results, RESULTS_DIR / "stage6_runs.jsonl")
summary = summarize(results, n_boot=E.n_bootstrap)
if E.repeats > 1:
    summary["reliability"] = {k: round(v, 4) if isinstance(v, float) else v
                              for k, v in reliability_report(by_scenario).items()}
summary["same_model_both_sides"] = settings().llm.user_sim_model == settings().llm.chat_model
summary["thresholds"] = tuned_thresholds()
print(json.dumps(summary, indent=2))
(RESULTS_DIR / "stage6_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
