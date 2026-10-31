---
name: invoice-extract
description: Extract invoice fields (supplier, number, date, net, tax, total, IBAN) into validated JSON. Use when the user shares an invoice or receipt as text or an image and wants the data.
---

# Invoice extraction

- Output JSON matching `reference/schema.json`; then check: total = net + tax (±0.01), date not in the future.
- If a check fails, say which one and ask; do not "fix" numbers silently.
- Mask the IBAN except the last 4 characters in anything you display.
