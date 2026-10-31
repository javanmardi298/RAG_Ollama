"""Generates files/data/products.json: a small synthetic catalogue with graded relevance labels (maintainers only)."""
import json
import random

rng = random.Random(42)
CLASSES = {"sofa": ["Living Room Furniture", "sofa", "couch", "settee"], "armchair": ["Living Room Furniture", "armchair", "accent chair"],
           "dining chair": ["Kitchen & Dining", "dining chair", "side chair"], "coffee table": ["Living Room Furniture", "coffee table"],
           "dining table": ["Kitchen & Dining", "dining table", "kitchen table"], "bed frame": ["Bedroom Furniture", "bed frame", "platform bed"],
           "floor lamp": ["Lighting", "floor lamp"], "area rug": ["Rugs", "area rug", "carpet"], "desk": ["Office Furniture", "desk", "writing desk"],
           "bookcase": ["Storage", "bookcase", "bookshelf"]}
COLORS = ["grey", "blue", "green", "beige", "black", "white", "brown"]
MATERIALS = {"sofa": ["velvet", "linen", "leather"], "armchair": ["velvet", "linen", "leather"], "dining chair": ["oak", "metal", "plastic"],
             "coffee table": ["oak", "marble", "glass"], "dining table": ["oak", "walnut", "glass"], "bed frame": ["oak", "metal", "upholstered"],
             "floor lamp": ["metal", "brass", "wood"], "area rug": ["wool", "jute", "cotton"], "desk": ["oak", "walnut", "metal"],
             "bookcase": ["oak", "pine", "metal"]}
STYLES = ["modern", "mid-century", "rustic", "scandinavian", "industrial"]
products = []
pid = 0
for cls, (category, *names) in CLASSES.items():
    for _ in range(8):
        pid += 1
        color, mat, style = rng.choice(COLORS), rng.choice(MATERIALS[cls]), rng.choice(STYLES)
        seats = rng.choice([2, 3, 4]) if cls == "sofa" else None
        name = f"{rng.choice(['Alma', 'Brook', 'Cora', 'Dane', 'Elio', 'Faye', 'Gus', 'Hale', 'Iris', 'Juno'])} {names[0].title()}"
        feats = {"color": color, "material": mat, "style": style}
        if seats:
            feats["seats"] = str(seats)
        desc = (f"A {names[-1]} " + (f"made of {mat}. " if rng.random() < 0.3 else "for your home. ") + rng.choice(["Easy to assemble.", "Solid build for daily use.", "Fits small spaces.",
                "Comes with a 2-year warranty."]) + (f" Seats {seats}." if seats else ""))
        products.append({"product_id": pid, "product_name": name, "product_class": cls, "category": category,
                         "features": "|".join(f"{k}:{v}" for k, v in feats.items()), "description": desc})
QUERIES = ["grey velvet sofa", "leather couch", "3 seat sofa", "oak dining table", "kitchen table glass", "mid-century armchair",
           "accent chair blue", "metal desk", "writing desk walnut", "wool rug", "jute carpet", "brass floor lamp", "industrial lamp",
           "platform bed oak", "upholstered bed", "scandinavian bookshelf", "pine bookcase", "marble coffee table", "white dining chair",
           "rustic side chair", "green settee", "modern beige sofa", "black metal bookcase", "cotton area rug"]
SYN = {"couch": "sofa", "settee": "sofa", "carpet": "area rug", "kitchen table": "dining table", "accent chair": "armchair",
       "bookshelf": "bookcase", "platform bed": "bed frame", "side chair": "dining chair", "lamp": "floor lamp", "rug": "area rug",
       "desk": "desk", "bed": "bed frame", "chair": "dining chair", "table": "dining table"}


def parse(q):
    cls = next((c for c in CLASSES if c in q), None)
    if cls is None:
        cls = next((v for k, v in SYN.items() if k in q), None)
    attrs = [w for w in q.split() if w in COLORS or any(w in m for m in MATERIALS.values()) or w in STYLES or w.isdigit()]
    return cls, attrs


def add_product(cls, color=None, mat=None, style=None, seats=None):
    global pid
    pid += 1
    category, *names = CLASSES[cls]
    color, mat, style = color or rng.choice(COLORS), mat or rng.choice(MATERIALS[cls]), style or rng.choice(STYLES)
    feats = {"color": color, "material": mat, "style": style, **({"seats": str(seats)} if seats else {})}
    products.append({"product_id": pid, "product_name": f"Kai {names[0].title()}", "product_class": cls,
                     "category": category, "features": "|".join(f"{k}:{v}" for k, v in feats.items()),
                     "description": f"A {names[-1]} for your home." + (f" Seats {seats}." if seats else "")})


for q in QUERIES:                                   # every query gets at least one exact match
    cls, attrs = parse(q)
    kw = {"color": next((a for a in attrs if a in COLORS), None), "mat": next((a for a in attrs if a in MATERIALS[cls]), None),
          "style": next((a for a in attrs if a in STYLES), None), "seats": next((int(a) for a in attrs if a.isdigit()), None)}
    def exact(p, cls=cls, attrs=attrs):
        text = (p["features"] + " " + p["product_name"]).lower()
        return p["product_class"] == cls and all(a in text or (a.isdigit() and f"seats:{a}" in p["features"]) for a in attrs)
    if not any(exact(p) for p in products):
        add_product(cls, **kw)

queries, labels = [], []
for qid, q in enumerate(QUERIES, 1):
    cls, attrs = parse(q)
    queries.append({"query_id": qid, "query": q})
    for p in products:
        if p["product_class"] != cls:
            continue
        text = (p["features"] + " " + p["product_name"]).lower().replace("seats:", "seats ")
        hits = sum(a in text or (a.isdigit() and f"seats:{a}" in p["features"]) for a in attrs)
        grade = 2 if hits == len(attrs) else 1
        labels.append({"query_id": qid, "product_id": p["product_id"], "label": "Exact" if grade == 2 else "Partial"})
json.dump({"products": products, "queries": queries, "labels": labels}, open("files/data/products.json", "w"), indent=1)
print(len(products), "products", len(queries), "queries", len(labels), "labels",
      sum(l["label"] == "Exact" for l in labels), "exact")
