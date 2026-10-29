# p22 — Agentic RAG: جست‌وجو را دوباره امتحان کن و بدان کی «نمی‌دانم» بگویی

**سطح:** میانی · **زمان:** ۵ تا ۸ ساعت · **پیش‌نیاز:** [p01](../p01_faq_search/README.md) (یا فهمیدن chunk و جست‌وجو) · **نیاز:** فقط Python؛ گام ۵ اختیاری با مدل واقعی

## مسئله
RAG ساده همیشه جواب می‌دهد، حتی وقتی چیز درستی پیدا نشده. سؤال «شماره‌ی تلفن مدیرعامل چیست؟» ممکن است تکه‌ای را بیاورد که کلمه‌ی «number» دارد و مدل از آن جوابی بسازد. **Agentic RAG** بازیابی را یک حلقه‌ی قابل‌کنترل می‌کند:

```
route → retrieve → grade → (rewrite → retrieve ...) → answer → verify → abstain
```
ریشه‌ها: [Self-RAG](https://arxiv.org/abs/2310.11511)، [Corrective RAG](https://arxiv.org/abs/2401.15884)، [Adaptive-RAG](https://arxiv.org/abs/2403.14403).

## گام‌ها
| گام | موضوع | چه می‌نویسی |
|---|---|---|
| [۱](step01_router/lesson.md) | مسیریابی | `route`: مستقیم / بازیابی / چندمرحله‌ای |
| [۲](step02_grader/lesson.md) | نمره‌دادن به شواهد | `content_words`، `grade` |
| [۳](step03_corrective_loop/lesson.md) | بازنویسی و حلقه‌ی اصلاحی | `rewrite`، `agentic_search` با سقف دور |
| [۴](step04_verify_abstain/lesson.md) | راستی‌آزمایی و امتناع | `verify`، `run_agent`، `report` |
| [۵](step05_llm_components/lesson.md) | اجزای مبتنی بر مدل زبانی | وصل کردن `labkit.agentic_rag` به Ollama/Claude/OpenCode |

داده: همان صفحه‌های FAQ درس p01 + سه سؤال عمداً بی‌جواب (`lessons/_data/`).

## چطور کار کنیم
```bash
python -m learn start p22_agentic_rag
python -m learn check p22_agentic_rag
python -m learn hint  p22_agentic_rag
```
نسخه‌ی کامل و قابل‌اجرای همین پروژه: `python -m support.panel.presets scaffold p22_agentic_rag` (و [پریست](../../presets/projects/p22_agentic_rag.yaml)).
