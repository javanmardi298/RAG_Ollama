"""Generates files/data/tickets.json: synthetic support tickets with an intent and the template they came from (maintainers only)."""
import json
import random

rng = random.Random(7)
T = {
 "refund": ["refund for the {p} please, order {o}", "you charged me twice for {o}, I want a refund", "returned the {p}, when do I get my money", "I was promised a refund {d} days ago", "I want my money back for order {o}", "please refund order {o}, the {p} was not what I expected", "how long until I get the refund for {o}?",
            "still waiting for my refund, returned the {p} {d} days ago", "can you reimburse me for the {p}", "refund status for {o} please"],
 "shipping_delay": ["order {o} is late, where is it", "the {p} delivery is delayed again", "no update on my delivery for {d} days", "courier says the {p} is not shipped yet", "where is my order {o}? it is {d} days late", "my {p} has not arrived yet", "tracking for {o} has not moved in {d} days",
                    "delivery was promised last week, order {o}", "when will the {p} be delivered?", "parcel {o} seems lost"],
 "cancel_order": ["cancel my order for the {p}", "please cancel {o} immediately", "I changed my mind, cancel the order", "how do I cancel an order that is processing", "please cancel order {o}", "I ordered the {p} by mistake, cancel it", "can I still cancel {o} before it ships?",
                  "stop my order {o}, I found it cheaper", "cancel the {p} from my last order", "I need to cancel, order {o}"],
 "damaged_item": ["the {p} came damaged, order {o}", "broken {p} in the parcel", "the {p} is damaged and unusable", "glass on the {p} was shattered on arrival", "the {p} arrived broken", "order {o}: the {p} is scratched", "one leg of the {p} is cracked", "the box was crushed and the {p} is damaged",
                  "received a damaged {p} in order {o}", "the {p} has a big dent"],
 "account_access": ["locked out of my account", "I forgot my password and cannot reset it", "login fails with my email", "account access problem, cannot sign in", "I cannot log in to my account", "password reset email never arrives", "my account is locked after {d} attempts",
                    "how do I change the email on my account", "two-factor code does not work", "someone else may have accessed my account"],
 "invoice": ["invoice missing for order {o}", "please correct the invoice for {o}", "I need a copy of the invoice", "invoice needed for my expense report", "I need an invoice for order {o}", "the invoice for {o} has the wrong address", "please send a VAT invoice", "where can I download my invoice",
             "invoice amount for {o} is wrong", "can I get the invoice in my company's name"],
}
PRODUCTS = ["sofa", "chair", "lamp", "rug", "desk", "bed frame", "bookcase", "mirror"]


def noisy(s):
    if rng.random() < 0.3:
        s = s.lower()
    if rng.random() < 0.2:
        i = rng.randrange(1, max(len(s) - 1, 2))
        s = s[:i] + s[i + 1:]                       # a typo: one character missing
    return s


tickets = []
for label, temps in T.items():
    for ti, t in enumerate(temps):
        for _ in range(4):
            text = t.format(o=f"#{rng.randint(10000, 99999)}", p=rng.choice(PRODUCTS), d=rng.randint(2, 21))
            tickets.append({"text": noisy(text), "label": label, "template": f"{label}-{ti}"})
rng.shuffle(tickets)
json.dump({"tickets": tickets}, open("files/data/tickets.json", "w"), indent=0)
print(len(tickets), "tickets")
