"""Regenerate lessons/README.md (the index) and a guide page for every preset that has no interactive lesson yet."""
from __future__ import annotations

from support.config import ROOT

from . import api

LESSONS = ROOT / "lessons"
NEEDS = {"p17_jepa_basics": "torch", "p18_collapse_sigreg": "torch", "p19_world_model_planning": "torch",
         "p20_surprise_monitoring": "torch", "p21_vjepa2_video": "GPU (Colab)", "p29_agentic_rl": "GPU (Colab)"}


def _guide(p, presets) -> str:
    comps = presets.components()
    L = [f"# {p.title}", f"_{p.title_en}_ · سطح {presets.LEVELS[p.level]} · {p.weeks} هفته", "",
         "> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: "
         f"`python -m support.panel.presets scaffold {p.id}` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ "
         "ساختار آن مثل درس‌های `p01_faq_search` است.", "",
         f"## کاربرد واقعی\n{p.real_world}", f"## مسئله\n{p.problem}", f"## هدف\n{p.goal}", ""]
    if p.prerequisites:
        L += ["## پیش‌نیاز", *[f"- [{q}](../{q}/README.md)" for q in p.prerequisites], ""]
    L += ["## داده", *[f"- [{d.name}]({d.url}) · {d.license} · {d.note}" if d.url.startswith("http") else
                                     f"- {d.name}{' (`' + d.url + '`)' if d.url else ''} · {d.note}" for d in p.data], "",
          "## قطعه‌ها", *[f"- `{c}` {comps[c].name}: {comps[c].where}" for c in p.components], ""]
    for i, s in enumerate(p.stages, 1):
        L += [f"## گام {i}: {s.title}", "**یاد بگیر**", *[f"- {x}" for x in s.learn], "", "**بساز**", *[f"- {x}" for x in s.build], "",
              f"**بسنج:** {s.measure}", "", f"**دام:** {s.pitfall}", ""]
    L += ["## معیارها", *[f"- {m}" for m in p.metrics], "", "## سؤال مصاحبه", *[f"- {q}" for q in p.interview], "",
          "## نسخه‌ی پیشرفته", *[f"- {a}" for a in p.advanced], ""]
    return "\n".join(L)


def build() -> str:
    from support.panel import presets
    projs = presets.projects()
    for pid, p in projs.items():
        d = LESSONS / pid
        if not (d.exists() and api.steps(pid)):                 # interactive lessons keep their hand-written README
            d.mkdir(exist_ok=True)
            (d / "README.md").write_text(_guide(p, presets), encoding="utf-8")
    ov = {o["lesson"]: o for o in api.overview()}
    rows = []
    for pid, p in projs.items():
        o = ov.get(pid, {"steps": 0})
        kind = f"**تعاملی** · {o['steps']} گام" if o["steps"] else "راهنما"
        rows.append(f"| [{pid}]({pid}/README.md) | {p.title} | {presets.LEVELS[p.level]} | {kind} | {NEEDS.get(pid, '—')} |")
    extra = [f"- [{n}]({n}/README.md)" for n in ov if n not in projs]
    index = (LESSONS / "_index_head.md").read_text(encoding="utf-8") if (LESSONS / "_index_head.md").exists() else "# درس‌ها\n"
    text = (index.rstrip() + "\n\n## همه‌ی پروژه‌ها\n\n| درس | عنوان | سطح | نوع | نیاز |\n|---|---|---|---|---|\n" + "\n".join(rows)
            + "\n\n## درس‌های عمومی\n" + "\n".join(extra) + "\n\n- [واژه‌نامه](glossary.md)\n- [رفع اشکال](troubleshooting.md)\n")
    (LESSONS / "README.md").write_text(text, encoding="utf-8")
    return f"wrote lessons/README.md ({len(rows)} projects)"
