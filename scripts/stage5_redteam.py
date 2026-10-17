# Stage 5: red-team the guardrails with attacks you write yourself. Extend eval/redteam.yaml every time something slips through.
import json, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.guardrails import allowed_numbers, check_input, check_output, mask_pii

cases = yaml.safe_load((ROOT / "eval" / "redteam.yaml").read_text(encoding="utf-8"))

# Inputs: each attack lists the flags it MUST raise. Missing flag = the guardrail missed it.
inputs = []
for a in cases["inputs"]:
    flags = check_input(a["text"]).flags
    missed = sorted(set(a["expect_flags"]) - set(flags))
    inputs.append({**a, "flags": flags, "masked": mask_pii(a["text"]), "caught": not missed, "missed": missed})
    print("OK  " if not missed else "MISS", flags, "|", mask_pii(a["text"]))

# Outputs: bad answers the output check MUST reject, good ones it must let through.
# Allowed numbers = the case's tool facts + policy_rules.yaml, exactly as in the agent.
outputs = []
for b in cases["outputs"]:
    problems = check_output(b["text"], allowed_numbers({"facts": b.get("allowed_numbers", [])}), b.get("customer_email")).problems
    outputs.append({**b, "problems": problems, "caught": bool(problems) == b["should_fail"]})
    print("OK  " if outputs[-1]["caught"] else "MISS", problems, "|", b["text"])

summary = {"input_catch_rate": sum(i["caught"] for i in inputs) / len(inputs),
           "output_catch_rate": sum(o["caught"] for o in outputs) / len(outputs),
           "n_inputs": len(inputs), "n_outputs": len(outputs),
           "missed": [i["text"] for i in inputs if not i["caught"]] + [o["text"] for o in outputs if not o["caught"]]}
print(json.dumps(summary, indent=2, ensure_ascii=False))
(RESULTS_DIR / "stage5_redteam.json").write_text(json.dumps({"summary": summary, "inputs": inputs, "outputs": outputs},
                                                            indent=2, ensure_ascii=False), encoding="utf-8")
