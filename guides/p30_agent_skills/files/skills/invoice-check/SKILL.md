---
name: invoice-check
description: Check an invoice or receipt the user shares (as text or JSON) - required fields, total equals net plus tax, date not in the future - and report problems without fixing numbers silently. Use when the user shares an invoice or receipt and wants it checked or its data extracted.
---

# Invoice check

1. Put the invoice fields into JSON matching `reference/schema.json` (supplier, number, date, net, tax, total, iban).
2. Run `python scripts/validate_invoice.py <file.json>`; it lists every failed rule.
3. Report each failed rule and ask the user; never change a number to make the totals match.
4. When you show the IBAN, mask everything except the last 4 characters.
