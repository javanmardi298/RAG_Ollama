# Design: Marketplace Support Agent

## Problem
Customers of an online furniture store write to support to cancel orders, track parcels, get refunds and ask about policies, in English and German.
The agent should resolve what it safely can on its own and hand everything else to a human, without breaking store policy or inventing facts.

## Scope
In scope: order tracking, cancellation, address change, returns and refunds, damaged items, policy questions, handoff to a human.
Out of scope (declined politely): account management, newsletters, product reviews, payment disputes (always human).

## Architecture (built stage by stage)
```
message ─▶ guardrails(in) ─▶ intent + confidence ─▶ router
                                                    ├─ rag      → policy retrieval → answer with citation
                                                    ├─ tool     → verify identity → read order → decide → (confirm) → act
                                                    ├─ handoff  → summary for the human agent
                                                    └─ out_of_scope → polite redirect
answer ─▶ guardrails(out) ─▶ customer          every turn is logged as a trace
```

## Metrics, defined before building
| Metric | Definition | Why |
|---|---|---|
| Intent macro-F1 | mean F1 over intents on the locked test split | rare intents count as much as common ones |
| Automation rate | conversations resolved with no human / all conversations | the business goal |
| Containment | conversations that did not escalate / all | standard support metric |
| **False automation rate** | automated conversations that should have gone to a human / automated conversations | the cost of being too confident; must stay low |
| Policy compliance | actions taken that the rules in `policy_rules.yaml` allow / all actions | checked by code, not by an LLM |
| Groundedness | answers whose claims are supported by retrieved policy text | measured with a validated LLM judge |
| Latency p50 / p95 | per turn, measured in stage 8 | production readiness |

Automation rate and false automation rate are always reported together: either one alone can be gamed.

## Data
- **Intents:** Bitext customer support (CDLA-Sharing-1.0), cleaned, deduplicated and split by sentence key (stage 0).
- **Orders:** synthetic SQLite database from WANDS product names, with simulated prices and hand-made boundary cases.
- **Policies:** `policies/{en,de}/*.md`, generated from the numbers in `configs/policy_rules.yaml`.

## Known limitations (to revisit)
- Bitext is template-generated English; real customer messages are messier. Stage 7 adds German and noisy test sets.
- Bitext has no out-of-scope messages; stage 1 adds them.
- Prices and order histories are simulated.
