# Stage 8: what production monitoring looks at, computed from the agent's traces (results/traces.jsonl).
# Traces come from the API (stage 8), the terminal chat (stage 3) and the panel's agent chat.
# Parameters: configs/project.yaml -> monitoring.*, serving.p95_target_ms
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from support.config import RESULTS_DIR
from support.monitoring import TraceWriter, drift_report, latency_summary
from support.settings import settings

M, srv = settings().monitoring, settings().serving
traces = TraceWriter(RESULTS_DIR / "traces.jsonl").read()
print(len(traces), "traces")
if not traces:
    raise SystemExit("No traces yet: chat with the agent (panel or stage 3) or run the API + load test first.")

out = {"n_traces": len(traces), "latency": latency_summary([t["latency_s"] for t in traces]),
       "routes": {}, "drift": None}
for t in traces:
    out["routes"][t["route"]] = out["routes"].get(t["route"], 0) + 1
out["latency"]["p95_target_ms"] = srv.p95_target_ms
out["latency"]["p95_ok"] = out["latency"]["p95_ms"] <= srv.p95_target_ms
print("latency:", out["latency"]); print("routes:", out["routes"])

# Drift: first window = reference, last window = current. Needs two full windows of traffic.
if len(traces) >= 2 * M.window:
    rep = drift_report(traces[:M.window], traces[-M.window:])
    rep["alert"] = rep["psi"] > M.psi_alert or rep.get("confidence_psi", 0) > M.psi_alert or \
        rep["handoff_rate"]["current"] > M.handoff_ratio_alert * max(rep["handoff_rate"]["reference"], 0.01)
    out["drift"] = rep
    print("drift:", json.dumps(rep, indent=2))
else:
    print(f"drift: need {2 * M.window} traces (monitoring.window = {M.window}); have {len(traces)}.")
(RESULTS_DIR / "stage8_monitor.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
