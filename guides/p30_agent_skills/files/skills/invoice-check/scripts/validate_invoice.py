"""Validate an invoice JSON: required fields, total = net + tax (to the cent), date not in the future. Exit code 1 on problems."""
import datetime as dt
import json
import sys

REQUIRED = ["supplier", "number", "date", "total"]


def problems(inv, today=None):
    today = today or dt.date.today()
    out = [f"missing field: {f}" for f in REQUIRED if inv.get(f) in (None, "")]
    if all(isinstance(inv.get(k), (int, float)) for k in ("net", "tax", "total")) and abs(inv["net"] + inv["tax"] - inv["total"]) > 0.01:
        out.append(f"total {inv['total']} is not net {inv['net']} + tax {inv['tax']}")
    try:
        if inv.get("date") and dt.date.fromisoformat(inv["date"]) > today:
            out.append(f"date {inv['date']} is in the future")
    except ValueError:
        out.append(f"date {inv['date']!r} is not YYYY-MM-DD")
    return out


def mask_iban(iban):
    s = iban.replace(" ", "")
    return "*" * (len(s) - 4) + s[-4:] if len(s) > 4 else s


if __name__ == "__main__":
    inv = json.load(open(sys.argv[1], encoding="utf-8"))
    found = problems(inv)
    print("\n".join(found) if found else "invoice ok")
    if inv.get("iban"):
        print("iban:", mask_iban(inv["iban"]))
    sys.exit(1 if found else 0)
