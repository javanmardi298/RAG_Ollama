# Support-ticket triage with a human fallback

![tests](https://github.com/<your-user>/ticket_triage/actions/workflows/tests.yml/badge.svg)

Routes support tickets to 6 intents with TF-IDF (word + character n-grams) and logistic regression, and automates a
ticket only when the calibrated confidence reaches a threshold chosen on dev for a target accuracy; the rest goes to a
human.

## Results (`results/results.json`)
| | accuracy | macro-F1 |
|---|---|---|
| test, split by wording template (honest) | {acc} | {f1} |
| random split (leaky, for comparison) | {leaky_acc} | {leaky_f1} |

Human fallback on test (threshold chosen on dev for 80% target accuracy): coverage {cov80}, accuracy of automated tickets {acc80}.

## What I learned
- A random split looked perfect ({leaky_acc}) because near-identical tickets were on both sides; splitting by template shows the real accuracy.
- The model was most confident on some of its mistakes ("delivery is delayed" → damaged item, from similar character
  n-grams), so a confidence threshold alone cannot reach 90% here: everything goes to a human, which is the safe answer.

## Run it
```bash
python -m venv .venv && .venv\Scripts\Activate.ps1      # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python check_setup.py && python -m pytest -q
```
Open `01_ticket_triage.ipynb` and run all cells. Optional zero-shot LLM: `TRIAGE_PROVIDER=ollama|anthropic|opencode`.

## Limitations
- Synthetic tickets from 60 templates; real tickets are longer, multilingual and mix intents.
- Temperature and thresholds are fitted on 48 dev tickets.

## Licence
MIT
