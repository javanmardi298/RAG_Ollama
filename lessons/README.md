# درس‌ها: یادگیری قدم‌به‌قدم با کد، تست خودکار و راهنما

هر درس یک پروژه‌ی واقعی را به گام‌های کوچک می‌شکند. هر گام: **متن آموزشی کامل** (مفهوم، چرا، خط‌به‌خط کد، دام‌ها)، **کد ناقص** با TODO که تو کامل می‌کنی، **تست خودکار** که می‌گوید درست نوشتی یا نه و چرا، **راهنمایی سه‌سطحی**، **امتحان کوتاه** و جواب مرجع.

## از کجا شروع کنم؟
1. [راه‌اندازی (۳۰ دقیقه)](00_setup/README.md): Python، نصب، و اتصال مدل: Ollama، Claude، OpenCode.
2. [p01 — جست‌وجوی FAQ](p01_faq_search/README.md) (پایه، بدون هیچ مدل).
3. [p22 — Agentic RAG](p22_agentic_rag/README.md) (میانی).
4. [p17 — مبانی JEPA](p17_jepa_basics/README.md) (PyTorch، CPU).
5. [m01 — مقایسه‌ی مدل‌ها](m01_compare_models/README.md) (Ollama در برابر Claude در برابر OpenCode با عدد).

## روش پیشنهادی: notebook (کد را می‌بینی، اجرا می‌کنی، آخر بررسی می‌شود)
هر درس یک notebook دارد: `lessons/<درس>/<درس>.ipynb`. هر گام در آن به این ترتیب است: **متن درس** ← **✍️ کد تو** (کد ناقص را اینجا کامل می‌کنی؛ به فایل جدا نیازی نیست) ← **▶ اجرای نمایشی** ← **✅ بررسی خودکار** ← **🔍 کد تست‌ها** (ببین چه چیزی سنجیده می‌شود) ← **💡 جواب مرجع** (تاشو) ← **📝 امتحان کوتاه**. در پایان **🏁 گزارش نهایی درس**: نتیجه‌ی تست و امتحان هر گام.

```powershell
pip install -r requirements-notebook.txt
windows\notebook.bat p01_faq_search        # یا: python -m learn lab p01_faq_search
```
یا از پنل: «درس‌های تعاملی» ← «📓 notebook». در Colab: دکمه‌ی «Open in Colab» بالای هر notebook. در VS Code: فایل `.ipynb` را باز کن و kernel پایتون venv را انتخاب کن.

## روش‌های دیگر (همان درس‌ها)
```bash
python -m learn list                       # درس‌ها و پیشرفت تو
python -m learn start p01_faq_search       # متن گام ۱ + ساخت فایل پاسخ در work/
python -m learn check p01_faq_search       # تست خودکار روی پاسخ تو
python -m learn hint  p01_faq_search       # راهنمایی (هر بار یک سطح بیشتر)
python -m learn quiz  p01_faq_search 1     # امتحان کوتاه
python -m learn solution p01_faq_search    # جواب مرجع (بعد از یک تلاش)
python -m learn review                     # سؤال‌هایی که اشتباه زدی
python -m learn errors                     # دفترچه‌ی خطاهای خودت
```
همین‌ها در **پنل** (منوی «درس‌های تعاملی»: ویرایشگر، بررسی، راهنمایی، امتحان، انتخاب مدل) هم هست. پاسخ‌های تو در `work/` می‌مانند و commit نمی‌شوند.

## حالت معلم (Claude یا OpenCode راهنمای توست)
از Claude Desktop، Claude Code یا OpenCode بخواه: «درس p01 را با من جلو ببر». ابزارهای `lessons_list`، `lesson_step`، `lesson_check`، `lesson_hint` به آن‌ها داده می‌شود. معلم مفهوم را توضیح می‌دهد، تو کد را می‌نویسی، او نتیجه‌ی تست را با پرسش راهنما برایت باز می‌کند و **جواب کامل نمی‌دهد** (فایل `solution.py` از ابزار پنل خوانده نمی‌شود). برای Claude Code/OpenCode که خودشان فایل می‌خوانند، این قرارداد است نه قفل: در تنظیمات آن‌ها قاعده‌ی deny برای `lessons/**/solution.py` بگذار.

## مدل زبانی هر درس
پیش‌فرض `offline` (بدون نصب؛ شکل کار را نشان می‌دهد). برای جواب واقعی: `LEARN_PROVIDER=ollama | anthropic | opencode | openai_compatible` ([راهنمای کامل](00_setup/README.md)).

## قاعده‌های کار (برای هر درس)
- قبل از «بهتر کردن» اندازه بگیر؛ بعد از هر تغییر دوباره اندازه بگیر.
- نتیجه‌ی یک اجرا یا یک seed را باور نکن.
- کلید API و داده‌ی واقعی مشتری هرگز در git نرود.

## همه‌ی پروژه‌ها

| درس | عنوان | سطح | نوع | نیاز |
|---|---|---|---|---|
| [p01_faq_search](p01_faq_search/README.md) | جستجوی معنایی در FAQ و پایگاه دانش پشتیبانی | پایه | **تعاملی** · 5 گام | — |
| [p02_product_search](p02_product_search/README.md) | جستجوی محصول در فروشگاه آنلاین | پایه | راهنما | — |
| [p03_document_qa](p03_document_qa/README.md) | پرسش و پاسخ روی اسناد سازمان با ارجاع به منبع | پایه | راهنما | — |
| [p04_ticket_triage](p04_ticket_triage/README.md) | طبقه‌بندی و مسیریابی تیکت پشتیبانی | پایه | راهنما | — |
| [p05_invoice_extraction](p05_invoice_extraction/README.md) | استخراج داده از فاکتور و رسید + workflow تأیید | میانی | راهنما | — |
| [p06_text_to_sql](p06_text_to_sql/README.md) | دستیار تحلیل داده (Text-to-SQL) | میانی | راهنما | — |
| [p07_email_triage_workflow](p07_email_triage_workflow/README.md) | workflow پاسخ به ایمیل‌های صندوق مشترک | میانی | راهنما | — |
| [p08_support_agent](p08_support_agent/README.md) | دستیار پشتیبانی چندنوبتی فروشگاه (پروژه‌ی اصلی همین repo) | میانی | راهنما | — |
| [p09_multilingual_rag](p09_multilingual_rag/README.md) | RAG چندزبانه (فارسی، انگلیسی، آلمانی) | میانی | راهنما | — |
| [p10_research_agent](p10_research_agent/README.md) | agent پژوهشی (deep research) با ارجاع قابل‌بررسی | پیشرفته | راهنما | — |
| [p11_code_assistant](p11_code_assistant/README.md) | دستیار کد: پرسش از codebase و agent که تست اجرا می‌کند | پیشرفته | راهنما | — |
| [p12_multi_agent_claims](p12_multi_agent_claims/README.md) | پردازش خسارت بیمه با چند agent و تأیید انسانی | پیشرفته | راهنما | — |
| [p13_graphrag](p13_graphrag/README.md) | GraphRAG: پرسش چندپرشی با گراف دانش | پیشرفته | راهنما | — |
| [p14_llmops_platform](p14_llmops_platform/README.md) | پلتفرم LLMOps: gateway، هزینه، ارزیابی در CI و پایش | پیشرفته | راهنما | — |
| [p15_finetune_distill](p15_finetune_distill/README.md) | fine-tune و distillation مدل کوچک (LoRA، DPO) | پیشرفته | راهنما | — |
| [p16_llm_security](p16_llm_security/README.md) | آزمایشگاه امنیت برنامه‌های LLM (red-team) | پیشرفته | راهنما | — |
| [p17_jepa_basics](p17_jepa_basics/README.md) | مبانی JEPA: پیش‌بینی در فضای embedding (I-JEPA کوچک) | پایه | **تعاملی** · 4 گام | torch |
| [p18_collapse_sigreg](p18_collapse_sigreg/README.md) | فروپاشی نمایش (collapse) و درمان‌ها: EMA در برابر SIGReg | میانی | راهنما | torch |
| [p19_world_model_planning](p19_world_model_planning/README.md) | world model نهفته و تصمیم‌گیری با برنامه‌ریزی (CEM + MPC) | میانی | راهنما | torch |
| [p20_surprise_monitoring](p20_surprise_monitoring/README.md) | پایش با «غافلگیری»: کشف ناهنجاری با خطای پیش‌بینی world model | میانی | راهنما | torch |
| [p21_vjepa2_video](p21_vjepa2_video/README.md) | V-JEPA 2 واقعی: embedding ویدیو، جست‌وجو، رخداد غیرعادی و تشخیص عمل | پیشرفته | راهنما | GPU (Colab) |
| [p22_agentic_rag](p22_agentic_rag/README.md) | Agentic RAG: مسیر‌یابی، نمره‌دهی شواهد، بازنویسی، راستی‌آزمایی و امتناع | میانی | **تعاملی** · 5 گام | — |
| [p23_contextual_multimodal_rag](p23_contextual_multimodal_rag/README.md) | Contextual Retrieval و RAG چندوجهی (ColPali) روی PDF واقعی | میانی | راهنما | — |
| [p24_agent_reliability](p24_agent_reliability/README.md) | پایایی agent: pass^k، ارزیابی مسیر و حالت نهایی | میانی | راهنما | — |
| [p25_prompt_optimization](p25_prompt_optimization/README.md) | بهینه‌سازی خودکار prompt (GEPA / DSPy) بدون overfitting | میانی | راهنما | — |
| [p26_mcp_a2a](p26_mcp_a2a/README.md) | ساخت MCP server (spec 2026) و همکاری agent ها با A2A | میانی | راهنما | — |
| [p27_context_engineering](p27_context_engineering/README.md) | Context engineering و حافظه برای agent های طولانی | میانی | راهنما | — |
| [p28_secure_agent](p28_secure_agent/README.md) | agent امن با طراحی: provenance و policy در کد (CaMeL) | پیشرفته | راهنما | — |
| [p29_agentic_rl](p29_agentic_rl/README.md) | RL با پاداش قابل‌بررسی (GRPO) برای مدل کوچک ابزارمحور | پیشرفته | راهنما | GPU (Colab) |
| [p30_agent_skills](p30_agent_skills/README.md) | Agent Skills: بسته‌بندی دانش و روال کار با SKILL.md | پایه | راهنما | — |

## درس‌های عمومی
- [00_setup](00_setup/README.md)
- [m01_compare_models](m01_compare_models/README.md)

- [واژه‌نامه](glossary.md)
- [رفع اشکال](troubleshooting.md)
