"""Agentic RAG on FAQ pages: route -> retrieve -> grade -> rewrite (bounded) -> answer -> verify -> abstain.

Every decision is a small function. The rule-based versions run without any model; the model-based versions
(make_llm_components) ask an LLM for the same decisions in JSON. Both plug into the same loop, so they can be compared."""
import json
import os
import re
import shutil
import subprocess

STOP = {"the", "a", "an", "is", "are", "do", "does", "i", "you", "my", "to", "of", "and", "or", "in", "on", "for", "can", "how",
        "what", "it", "we", "your", "with", "if", "be", "at", "by", "from", "this", "that", "when", "where", "there", "much", "many",
        "get", "have", "long", "within", "will"}
SYN = {"send back": "return", "money back": "refund", "broken": "damage defect", "couch": "sofa"}
GREETINGS = {"hello", "hi", "hey", "thanks", "thank you", "bye"}


# ---------- data and a simple retriever ----------

def load_data(path="data/faq.json"):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["docs"], data["questions"]


def chunk_all(docs):
    """One chunk per '## ' section, heading path kept ('Returns > Return window')."""
    out = []
    for doc_id, text in docs.items():
        title, heading, buf, n = "", "", [], 0
        for line in text.splitlines() + ["# "]:
            if line.startswith("#"):
                body = " ".join(" ".join(buf).split())
                if body:
                    out.append({"id": f"{doc_id}#{n}", "doc_id": doc_id, "heading": " > ".join(x for x in (title, heading) if x), "text": body})
                    n += 1
                buf = []
                if line.startswith("## "):
                    heading = line[3:].strip()
                else:
                    title, heading = line[2:].strip(), ""
            else:
                buf.append(line)
    return out


def content_words(text):
    """Lowercase words without stop words; a trailing 's' is removed (invoices -> invoice)."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in STOP and len(w) > 1}


def expand(text):
    text = text.lower()
    for a, b in SYN.items():
        text = text.replace(a, b)
    return text


def make_search(chunks, k=3):
    """Word-overlap retriever (stand-in for BM25 / hybrid from the FAQ search project)."""
    def search(query):
        q = content_words(query)
        scored = [(len(q & content_words(c["heading"] + " " + c["text"])), i) for i, c in enumerate(chunks)]
        return [chunks[i] for s, i in sorted(scored, key=lambda t: (-t[0], t[1])) if s > 0][:k]
    return search


# ---------- rule-based decisions ----------

def route(question):
    q = question.strip().lower().rstrip("!.? ").strip()
    if q in GREETINGS or re.fullmatch(r"[\d\s+\-*/().]+", q):
        return "direct"
    return "retrieve"


def grade(question, chunk, min_ratio=0.5):
    """Relevant when at least half of the question's content words appear in the chunk."""
    q = content_words(expand(question))
    return bool(q) and len(q & content_words(chunk["heading"] + " " + chunk["text"])) / len(q) >= min_ratio


def rewrite(question, tried):
    words = sorted(content_words(expand(question)))
    out = []
    for cand in [expand(question), " ".join(words), *words]:
        if cand and cand not in tried and cand not in out:
            out.append(cand)
    return out


def verify(answer, chunks):
    """Every content word of the answer (citations removed) must appear in the evidence."""
    words = content_words(re.sub(r"\[[^\]]*\]", " ", answer or ""))
    return bool(words) and words <= content_words(" ".join(c["text"] for c in chunks))


def extractive_answer(question, chunks):
    """Best sentence of the best chunk, cited. No model needed."""
    qw = content_words(expand(question))
    best = max(chunks, key=lambda c: len(qw & content_words(c["text"])))
    sents = re.split(r"(?<=[.!?])\s+", best["text"])
    return max(sents, key=lambda s: len(qw & content_words(s))) + f" [{best['id']}]", [best["id"]]


# ---------- the loop ----------

def agentic_search(question, search, grade, rewrite, max_rounds=3, min_relevant=1):
    queries, tried, relevant, rounds = [question], [], {}, 0
    while queries and rounds < max_rounds:
        rounds += 1
        for q in queries:
            tried.append(q)
            for c in search(q):
                if grade(question, c):
                    relevant.setdefault(c["id"], c)
        if len(relevant) >= min_relevant:
            break
        queries = [x for x in rewrite(question, tried) if x not in tried]
    return {"chunks": list(relevant.values()), "rounds": rounds, "queries": tried}


def run_agent(question, search, grade=grade, rewrite=rewrite, answer_fn=extractive_answer, verify=verify, route=route,
              direct=lambda q: "Hello! How can I help?"):
    r = route(question)
    if r == "direct":
        return {"answer": direct(question), "citations": [], "route": r, "rounds": 0, "abstained": False}
    found = agentic_search(question, search, grade, rewrite)
    abstain = {"answer": None, "citations": [], "route": r, "rounds": found["rounds"], "abstained": True}
    if not found["chunks"]:
        return abstain
    text, cites = answer_fn(question, found["chunks"])
    ids = {c["id"] for c in found["chunks"]}
    cites = [c for c in cites if c in ids]
    if not cites or not verify(text, found["chunks"]):
        return abstain
    return {"answer": text, "citations": cites, "route": r, "rounds": found["rounds"], "abstained": False}


def plain_rag(question, search):
    """Baseline: always answers from whatever the search returns."""
    chunks = search(question)
    if not chunks:
        return {"answer": None, "citations": [], "route": "retrieve", "rounds": 1, "abstained": True}
    text, cites = extractive_answer(question, chunks)
    return {"answer": text, "citations": cites, "route": "retrieve", "rounds": 1, "abstained": False}


def report(outcomes, questions):
    out = {"answered_correctly": 0, "abstained_wrongly": 0, "abstained_correctly": 0, "answered_unanswerable": 0, "direct_ok": 0}
    for o, q in zip(outcomes, questions):
        if q["answerable"] == "yes":
            out["abstained_wrongly" if o["abstained"] else "answered_correctly"] += 1
        elif q["answerable"] == "no":
            out["abstained_correctly" if o["abstained"] else "answered_unanswerable"] += 1
        elif o["route"] == "direct":
            out["direct_ok"] += 1
    return out


# ---------- model-based decisions (Ollama, Claude or OpenCode) ----------

def make_llm(provider=None, model=None):
    """A function messages -> text. provider: ollama | anthropic | opencode (default: AGENT_PROVIDER)."""
    provider = provider or os.environ.get("AGENT_PROVIDER", "")
    if provider == "ollama":
        import ollama
        model = model or "qwen2.5:7b"
        return lambda msgs: ollama.chat(model=model, messages=msgs, options={"temperature": 0})["message"]["content"]
    if provider == "anthropic":
        import anthropic
        client, model = anthropic.Anthropic(), model or "claude-sonnet-5-5"   # reads ANTHROPIC_API_KEY

        def claude(msgs):
            r = client.messages.create(model=model, max_tokens=500, messages=msgs)
            return "".join(b.text for b in r.content if b.type == "text")
        return claude
    if provider == "opencode":
        if not shutil.which("opencode"):
            raise RuntimeError("opencode is not installed (https://opencode.ai)")
        model = model or "anthropic/claude-sonnet-5-5"
        return lambda msgs: subprocess.run(["opencode", "run", "-m", model, "\n\n".join(m["content"] for m in msgs)],
                                           capture_output=True, text=True, encoding="utf-8", timeout=300).stdout.strip()
    raise ValueError("set AGENT_PROVIDER to ollama, anthropic or opencode")


def ask_json(llm, prompt):
    text = llm([{"role": "user", "content": prompt + "\nAnswer with one JSON object only."}])
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def make_llm_components(llm):
    """The same four decisions, asked to a model. Returns keyword arguments for run_agent."""
    def m_route(q):
        r = ask_json(llm, f'Does this message need the shop FAQ? {{"route": "direct" or "retrieve"}}\nMessage: {q}')
        return "direct" if r.get("route") == "direct" else "retrieve"

    def m_grade(q, c):
        r = ask_json(llm, f'Does the passage help answer the question? {{"relevant": true or false}}\nQuestion: {q}\nPassage: {c["text"]}')
        return bool(r.get("relevant"))

    def m_rewrite(q, tried):
        r = ask_json(llm, f'These searches found nothing useful: {tried}. Give up to 2 different search queries for: {q}\n{{"queries": [...]}}')
        return [x for x in r.get("queries", []) if isinstance(x, str)][:2]

    def m_answer(q, chunks):
        src = "\n".join(f"[{c['id']}] {c['text']}" for c in chunks)
        text = llm([{"role": "user", "content": f"Answer ONLY from the sources and cite them like [returns#0]. If they do not "
                                                f"answer the question, say you do not know.\nSources:\n{src}\n\nQuestion: {q}"}])
        return text, re.findall(r"\[([^\]]+)\]", text)

    def m_verify(a, chunks):
        src = "\n".join(c["text"] for c in chunks)
        r = ask_json(llm, f'Is every claim in the answer supported by the sources? {{"supported": true or false}}\nSources:\n{src}\nAnswer: {a}')
        return bool(r.get("supported"))

    return {"route": m_route, "grade": m_grade, "rewrite": m_rewrite, "answer_fn": m_answer, "verify": m_verify,
            "direct": lambda q: llm([{"role": "user", "content": q}])}
