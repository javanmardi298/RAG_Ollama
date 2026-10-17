"""What the panel knows about each stage: what to learn, what to run, which parameters matter, what comes out.

Content is for a beginner who will need the advanced version later: every stage has a short "advanced" list
(what a senior AI engineer would add next) and interview questions, next to the basic steps.
Tasks are the only commands the panel, the MCP server and Claude can start: a fixed allow-list, no free shell.
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field

PY = sys.executable

# The six requirements of the job ad this project is built for.
JOB_AD = {
    "multi_turn": "agent چندنوبتی (multi-turn) با ابزار",
    "auto_vs_handoff": "تصمیم بین حل خودکار و ارجاع به انسان",
    "multilingual_rag": "RAG چندزبانه (انگلیسی و آلمانی) با ارجاع به منبع",
    "eval_guardrails": "ارزیابی و guardrail",
    "production": "production: سرو کردن، تأخیر، پایش",
    "ab_test": "آزمایش A/B و بهبود مدل",
}


@dataclass
class Task:
    id: str
    label: str
    cmd: list[str]
    kind: str = "batch"               # batch: runs and ends | service: runs until stopped
    needs: list[str] = field(default_factory=list)   # preflight check ids that must pass
    minutes: str = ""                 # rough duration on a laptop
    lc: bool = False                  # LangChain / LangGraph version
    note: str = ""


@dataclass
class Stage:
    id: int
    title: str
    title_en: str
    goal: str
    concepts: list[tuple[str, str]]
    why: str
    steps: list[str]
    tasks: list[Task]
    settings: list[str]               # project.yaml sections shown on the stage page
    outputs: list[str]                # files in results/ (or data/) this stage produces
    pitfalls: list[str]
    interview: list[str]
    advanced: list[str]
    job_ad: list[str]
    files: list[str]


def _script(name: str, *args: str) -> list[str]:
    return [PY, "-u", f"scripts/{name}", *args]


def _pytest(*args: str) -> list[str]:
    return [PY, "-m", "pytest", "-q", *args]


STAGES: list[Stage] = [
    Stage(
        0, "داده، دیتابیس سفارش‌ها، قواعد فروشگاه", "Data, order database, policies",
        "همه‌ی ورودی‌های مرحله‌های بعد را تکرارپذیر بسازی: داده‌ی intent بدون نشت، دیتابیس سفارش با موارد مرزی، "
        "و یک خلاصه‌ی عددی که README از آن می‌خواند.",
        [("نشت داده (leakage)", "وقتی جمله‌ای که مدل در train دیده، با کمی تفاوت در test هم باشد؛ نمره‌ی test حافظه را می‌سنجد نه فهم را."),
         ("StratifiedGroupKFold", "تقسیم داده که هم نسبت هر intent را حفظ می‌کند (stratified) و هم همه‌ی نسخه‌های یک جمله را در یک بخش نگه می‌دارد (group)."),
         ("مورد مرزی (edge case)", "سفارشی که دقیقاً روی مرز قاعده است: روز ۱۴ در برابر ۱۵، یا ۱۵۰٫۰۰ در برابر ۱۵۰٫۰۱ یورو. باگ‌ها همین‌جا پنهان می‌شوند."),
         ("reference_date", "«امروز» شبیه‌سازی‌شده؛ با آن هر اجرا همان نتیجه را می‌دهد. هرگز date.today() استفاده نکن.")],
        "تقسیم تصادفی ساده روی Bitext نمره را خوش‌بینانه می‌کند، چون جمله‌ها از template ساخته شده‌اند. "
        "دیتابیس ساختگی ولی واقع‌گرا لازم است چون داده‌ی سفارش واقعی شخصی است، و ابزارها و ارزیابی مرحله‌ی ۶ به آن تکیه دارند.",
        ["پیش‌نیازها را در صفحه‌ی «اتصال‌ها و پیش‌نیازها» سبز کن (Python، پکیج‌ها، فضای دیسک).",
         "«ساخت داده و دیتابیس» را اجرا کن. بار اول Bitext، CLINC150 و WANDS دانلود می‌شوند.",
         "لاگ را بخوان: تعداد intentها، سهم flagها، تعداد تکراری‌های حذف‌شده، و اختلاف سهم intent بین بخش‌ها.",
         "تست‌ها را اجرا کن؛ همه باید سبز باشند (ترتیب تاریخ‌ها، موارد مرزی، همگامی قواعد EN/DE).",
         "results/data_summary.json را نگاه کن. از اینجا به بعد test قفل است؛ همه‌ی تصمیم‌ها روی dev."],
        [Task("stage0_data", "ساخت داده و دیتابیس", _script("stage0_data.py"), needs=["pkg_core", "disk"], minutes="۲–۱۰"),
         Task("tests_all", "اجرای همه‌ی تست‌ها", _pytest(), needs=["pkg_core"], minutes="زیر ۱")],
        ["project", "data"],
        ["data_summary.json", "../data/shop.db", "../data/processed/intents_train.csv"],
        ["اگر بعد از دیدن نتیجه‌ی test چیزی را عوض کنی، test دیگر test نیست.",
         "عوض کردن seed نتایج را با اجراهای قبلی غیرقابل‌مقایسه می‌کند.",
         "اگر intent جدیدی در داده باشد که در intents.yaml نیست، agent بعداً خراب می‌شود؛ اسکریپت همین‌جا جلویش را می‌گیرد."],
        ["چرا تقسیم تصادفی روی داده‌ی template-محور خطرناک است و چطور فهمیدی؟",
         "موارد مرزی را چطور انتخاب کردی و کدام تست آن‌ها را چک می‌کند؟",
         "چرا عددهای قواعد فقط در یک فایل هستند؟"],
        ["تقسیم زمانی (time-based split) وقتی داده‌ی واقعی با تاریخ داری.",
         "data contract و اعتبارسنجی schema با pandera یا Great Expectations.",
         "نسخه‌گذاری داده با DVC، و data card برای هر دیتاست (منبع، لایسنس، محدودیت).",
         "تشخیص near-duplicate با MinHash/embedding به‌جای کلید متنی."],
        [],
        ["scripts/stage0_data.py", "src/support/data.py", "src/support/orders.py", "configs/policy_rules.yaml"],
    ),
    Stage(
        1, "تشخیص intent", "Intent classification",
        "سه روش را روی یک داده و یک معیار مقایسه کنی (TF-IDF، embedding، LLM) و برنده را با سرعت و calibration انتخاب کنی، نه فقط دقت.",
        [("macro-F1", "میانگین F1 روی همه‌ی کلاس‌ها با وزن برابر؛ کلاس‌های کم‌نمونه هم دیده می‌شوند."),
         ("calibration و ECE", "آیا «۹۰٪ مطمئنم» واقعاً ۹۰٪ درست است؟ ECE فاصله‌ی میانگین اطمینان و دقت است. مرحله‌ی ۴ به اطمینانِ صادق نیاز دارد."),
         ("temperature scaling", "یک عدد T که روی dev یاد گرفته می‌شود و احتمال‌ها را صادق‌تر می‌کند، بدون تغییر پیش‌بینی."),
         ("out-of-scope (oos)", "پیامی که اصلاً به فروشگاه ربط ندارد؛ از CLINC150 می‌آید تا مدل یاد بگیرد «نمی‌دانم» بگوید."),
         ("few-shot پویا", "برای هر پیام، شبیه‌ترین مثال‌های train در prompt می‌روند؛ همان retrieval برای prompt.")],
        "TF-IDF سریع و قوی است و baseline لازم دارد. embedding مترادف و زبان دوم را بهتر می‌فهمد. LLM بدون آموزش کار می‌کند ولی کند است "
        "و اطمینان رایگان نمی‌دهد. مقایسه‌ی منصفانه یعنی همان dev، همان معیار، و گزارش سرعت کنار دقت.",
        ["پارامترها را تنظیم کن: اگر لپ‌تاپ GPU ندارد، run_embeddings را خاموش کن یا آن بخش را در Colab اجرا کن.",
         "مرحله را اجرا کن و نتایج dev سه مدل را مقایسه کن (دقت، ECE قبل و بعد از calibration، ms/پیام).",
         "برنده را در intents.winner انتخاب کن (بر اساس dev) و یک بار دیگر اجرا کن تا روی test گزارش شود.",
         "دقت به تفکیک flag را ببین: Z (غلط تایپی) و Q (محاوره‌ای) همان ورودی نویزی آگهی هستند."],
        [Task("stage1_intents", "مقایسه‌ی سه مدل intent", _script("stage1_intents.py"), needs=["pkg_core", "data_splits"],
              minutes="۳–۳۰"),
         Task("lc_stage1_intents", "نسخه‌ی LangChain (LCEL)", _script("lc_stage1_intents.py"),
              needs=["pkg_lc", "data_splits", "ollama", "ollama_model"], minutes="۵–۱۵", lc=True)],
        ["intents", "embeddings", "llm"],
        ["stage1_intents.json", "intent_model.joblib", "temperature.txt"],
        ["انتخاب برنده با نگاه به test = نشت تصمیم. فقط dev.",
         "T را برای همان مدلی fit کن که ذخیره می‌کنی؛ T یک مدل برای مدل دیگر بی‌معنی است.",
         "LLM روی نمونه ارزیابی می‌شود؛ مقایسه‌اش با کل dev دقیق نیست. حجم نمونه را گزارش کن."],
        ["چرا macro-F1 و نه accuracy؟", "calibration چه ربطی به ارجاع به انسان دارد؟",
         "اگر LLM دقیق‌تر ولی ۵۰ برابر کندتر بود، چه می‌کردی؟"],
        ["conformal prediction برای مجموعه‌ی پیش‌بینی با تضمین پوشش.",
         "SetFit یا fine-tune کوچک (مرحله‌ی ۹) روی داده‌ی کم.",
         "cross-validation و فاصله‌ی اطمینان برای اختلاف دو مدل (McNemar).",
         "تشخیص intent چندبرچسبی و پیام‌هایی که دو درخواست دارند."],
        ["auto_vs_handoff", "multilingual_rag"],
        ["scripts/stage1_intents.py", "src/support/intents.py"],
    ),
    Stage(
        2, "RAG روی قواعد (انگلیسی و آلمانی)", "Policy RAG",
        "به سؤال‌های قواعد فقط از روی سند جواب بدهی، با ارجاع به منبع، و وقتی جواب در سند نیست، بگویی نمی‌دانم.",
        [("BM25", "جستجوی کلیدواژه‌ای با وزن کمیاب بودن کلمه؛ سریع و دقیق، ولی مترادف را نمی‌فهمد (send back ≠ return)."),
         ("dense retrieval", "متن و سؤال به بردار تبدیل می‌شوند و شباهت معنایی سنجیده می‌شود؛ مترادف و زبان دیگر را می‌فهمد."),
         ("hybrid با RRF", "دو رتبه‌بندی فقط با جایگاه ترکیب می‌شوند: مجموع 1/(k+rank). مقیاس امتیازها مهم نیست."),
         ("recall@k و MRR", "آیا سند درست در k نتیجه‌ی اول هست؟ MRR: معکوس رتبه‌ی اولین سند درست."),
         ("grounding", "هر عدد جواب باید در منبع یا سؤال باشد؛ کد این را چک می‌کند، نه LLM.")],
        "پیکره کوچک است (۱۲ سند در دو زبان)، پس چالش مقیاس نیست؛ چالش مترادف، زبان دوم، و جلوگیری از جواب ساختگی است. "
        "hybrid ضعف هر روش را با دیگری می‌پوشاند و RRF نیازی به هم‌مقیاس کردن امتیاز ندارد.",
        ["eval/policy_qa.yaml را بخوان: هر سؤال، سند درست و عبارتی که جواب باید داشته باشد.",
         "مرحله را اجرا کن و recall@k سه حالت را مقایسه کن. سؤال‌های از دست رفته را بخوان و دلیلشان را پیدا کن.",
         "k و rag.mode را تغییر بده و دوباره اجرا کن؛ در «مقایسه‌ی اجراها» اثر را ببین.",
         "نرخ‌های جواب: fact، citation، عدد پشتیبانی‌شده، و رد کردن سؤال بی‌جواب."],
        [Task("stage2_rag", "ارزیابی retrieval و جواب‌ها", _script("stage2_rag.py"),
              needs=["pkg_core", "pkg_embed", "ollama", "ollama_model"], minutes="۲–۱۰"),
         Task("lc_stage2_rag", "نسخه‌ی LangChain (retriever + RRF)", _script("lc_stage2_rag.py"),
              needs=["pkg_lc", "ollama", "ollama_model"], minutes="۲–۱۰", lc=True)],
        ["rag", "embeddings", "llm"],
        ["stage2_rag.json"],
        ["۳۰ سؤال کم است: یک سؤال = ۳ درصد. اختلاف کوچک را جدی نگیر.",
         "توکن‌ساز پیش‌فرض BM25Retriever در LangChain فقط روی فاصله تکه می‌کند؛ نسخه‌ی پروژه اصلاحش کرده.",
         "اگر جواب درست است ولی citation غلط است، کاربر نمی‌تواند به آن اعتماد کند."],
        ["چرا hybrid؟ کی BM25 تنها بهتر است؟", "RRF را توضیح بده و چرا امتیازها را جمع نمی‌کنی.",
         "چطور مطمئن می‌شوی مدل عدد نمی‌سازد؟"],
        ["reranker (cross-encoder) روی ۲۰ نتیجه‌ی اول.", "query rewriting و HyDE برای سؤال‌های کوتاه.",
         "ارزیابی chunking (اندازه، overlap، عنوان در هر chunk).",
         "ارزیابی با RAGAS یا معیارهای faithfulness، و پایگاه برداری (FAISS/pgvector) در مقیاس بزرگ."],
        ["multilingual_rag"],
        ["scripts/stage2_rag.py", "src/support/rag.py", "policies/", "eval/policy_qa.yaml"],
    ),
    Stage(
        3, "ابزارها و agent چندنوبتی", "Tools and multi-turn agent",
        "agentی بسازی که سفارش را با ابزار پیدا و تغییر دهد، بدون اینکه امنیت را به prompt بسپارد.",
        [("tool calling", "LLM به‌جای متن، نام ابزار و آرگومان برمی‌گرداند؛ کد ابزار را اجرا و نتیجه را برمی‌گرداند."),
         ("تأیید صریح", "هر عمل تغییردهنده (لغو، مرجوعی) فقط بعد از «بله»ی مشتری اجرا می‌شود؛ این را کد اجبار می‌کند."),
         ("idempotency", "دومین لغو برای یک سفارش رد می‌شود (UNIQUE در جدول actions)؛ retry دو بار پول برنمی‌گرداند."),
         ("هویت از session", "ابزار مشتری را از session می‌گیرد، نه از آرگومانی که LLM نوشته؛ پس LLM نمی‌تواند سفارش دیگری را ببیند."),
         ("workflow بیرونی + حلقه‌ی درونی", "guardrail → intent → تصمیم → مسیر، ثابت و با کد؛ فقط مسیر ابزار حلقه‌ی LLM دارد.")],
        "آن‌چه با کد قابل تصمیم است (قواعد، هویت، مالکیت سفارش) با LLM تصمیم گرفته نمی‌شود. LLM فقط زبان را می‌فهمد و ابزار را انتخاب می‌کند.",
        ["تست‌های ابزار و agent را اجرا کن؛ بدون مدل و با ScriptedLLM کار می‌کنند.",
         "«آزمون سریع agent» را اجرا کن: چند پیام ثابت از کل زنجیره می‌گذرند.",
         "در صفحه‌ی «چت با agent» با یک سفارش واقعی از shop.db گفتگو کن: شماره سفارش و ایمیل بده، لغو بخواه، «بله» بگو.",
         "سعی کن agent را فریب بدهی (ایمیل اشتباه، سفارش دیگران). نتیجه را در traces ببین."],
        [Task("tests_agent", "تست‌های ابزار و agent", _pytest("tests/test_tools.py", "tests/test_agent.py"),
              needs=["pkg_core"], minutes="زیر ۱"),
         Task("stage3_smoke", "آزمون سریع agent (۳ پیام)", _script("stage3_smoke.py"),
              needs=["pkg_core", "db", "intent_model", "ollama", "ollama_model"], minutes="۱–۳"),
         Task("tests_lc_routing", "تست مسیریابی گراف LangGraph", _pytest("tests/test_lc_routing.py"),
              needs=["pkg_core"], minutes="زیر ۱", lc=True)],
        ["agent", "llm"],
        ["stage3_smoke.json", "traces.jsonl"],
        ["قبل از interrupt در LangGraph کاری با اثر جانبی نکن: بعد از ادامه، node از اول اجرا می‌شود.",
         "اگر LLM آرگومان customer_id بنویسد و ابزار قبولش کند، نشت اطلاعات داری.",
         "تعداد قدم‌های ابزار را محدود کن (agent.max_tool_steps)؛ حلقه‌ی بی‌پایان هزینه و تأخیر است."],
        ["چرا تأیید مشتری را به prompt نسپردی؟", "idempotency را در این پروژه چطور تضمین کردی؟",
         "workflow و agent چه فرقی دارند و کی کدام؟"],
        ["state machine صریح با LangGraph (پوشه‌ی lc/) و checkpointer برای ادامه‌ی گفتگو.",
         "MCP برای ابزارها تا agentهای دیگر هم از آن‌ها استفاده کنند.",
         "مدیریت حافظه‌ی گفتگوی طولانی (خلاصه‌سازی، پنجره).",
         "اجرای موازی ابزارها و timeout/retry برای هر ابزار."],
        ["multi_turn"],
        ["src/support/agent.py", "src/support/tools.py", "src/support/policy.py", "src/support/lc/graph.py"],
    ),
    Stage(
        4, "تصمیم و ارجاع به انسان", "Decision and handoff",
        "آستانه‌ی اطمینان را از داده انتخاب کنی: برای intent پرریسک سخت‌گیرتر، و همیشه Automation Rate را کنار خطایش گزارش کنی.",
        [("منحنی risk-coverage", "برای هر آستانه: چند درصد خودکار حل می‌شود (coverage) و چند درصد آن‌ها غلط است (risk)."),
         ("بودجه‌ی خطا", "حداکثر خطای قابل‌قبول بین موارد خودکار؛ برای ریسک زیاد کمتر (مثلاً ۱٪)."),
         ("selective classification", "مدل حق دارد جواب ندهد؛ هدف دقت بالا روی آن‌چه جواب می‌دهد است."),
         ("آستانه‌ی هزینه‌محور", "اگر هزینه‌ی عمل اشتباه ۲۰ برابر ارجاع باشد، آستانه‌ای که هزینه‌ی کل را کمینه می‌کند."),
         ("False Automation Rate", "سهم موارد خودکاری که باید به انسان می‌رفتند. بدون آن، Automation Rate گمراه‌کننده است.")],
        "یک آستانه برای همه یعنی یا intent پرریسک بی‌دقت خودکار می‌شود یا intent کم‌ریسک بی‌دلیل به انسان می‌رود. "
        "آستانه‌ی جدا برای هر سطح ریسک، هر دو را حل می‌کند و از داده می‌آید، نه از حدس.",
        ["بودجه‌ی خطا را برای سه سطح ریسک تنظیم کن (high ≤ medium ≤ low).",
         "مرحله را اجرا کن؛ منحنی و آستانه‌ها را ببین. خودکار‌سازی و خطا روی dev کنار هم گزارش می‌شوند.",
         "use_tuned_thresholds را روشن نگه دار تا agent (مرحله‌ی ۳، ۶، ۸ و چت پنل) همین آستانه‌ها را بخواند.",
         "بودجه را تغییر بده و در «مقایسه‌ی اجراها» ببین coverage چقدر عوض می‌شود."],
        [Task("stage4_thresholds", "انتخاب آستانه‌ها از dev", _script("stage4_thresholds.py"),
              needs=["pkg_core", "data_splits", "intent_model"], minutes="زیر ۱"),
         Task("tests_decision", "تست‌های لایه‌ی تصمیم", _pytest("tests/test_decision.py"), needs=["pkg_core"], minutes="زیر ۱")],
        ["decision"],
        ["stage4_thresholds.json", "thresholds.json", "risk_coverage.png"],
        ["آستانه را روی test انتخاب نکن.", "اگر calibration بد باشد (ECE بالا)، آستانه‌ها معنای واقعی ندارند؛ اول مرحله‌ی ۱.",
         "Automation Rate تنها گزارش نشود؛ همیشه کنار False Automation Rate."],
        ["منحنی risk-coverage را توضیح بده.", "آستانه‌ی جدا برای هر ریسک را چطور انتخاب کردی؟",
         "اگر هزینه‌ی خطا را ندانی چه می‌کنی؟"],
        ["conformal risk control برای تضمین آماری خطا.", "آستانه‌ی وابسته به مشتری یا مبلغ سفارش.",
         "یادگیری از تصمیم‌های اپراتور انسانی (human feedback) و بازتنظیم دوره‌ای.",
         "ارزیابی off-policy قبل از تغییر آستانه در production."],
        ["auto_vs_handoff"],
        ["scripts/stage4_thresholds.py", "src/support/decision.py", "configs/intents.yaml"],
    ),
    Stage(
        5, "Guardrail", "Guardrails",
        "ورودی خطرناک (prompt injection، اطلاعات کارت) و خروجی خطرناک (عدد ساختگی، ایمیل دیگران، قول) را با کد بگیری.",
        [("prompt injection", "متنی که سعی می‌کند دستور سیستم را عوض کند. اینجا مسدود نمی‌شود؛ agent فقط در آن نوبت ابزار ندارد."),
         ("بررسی عدد ساختگی", "هر عدد جواب باید در نتیجه‌ی ابزار، قواعد یا پیام مشتری باشد؛ وگرنه یک بار retry و بعد ارجاع."),
         ("پنهان کردن PII", "ایمیل، IBAN، کارت (با چک Luhn) و تلفن قبل از لاگ شدن جایگزین می‌شوند."),
         ("red-teaming", "حمله‌هایی که خودت می‌نویسی؛ هر حمله‌ای که رد شد به فهرست اضافه می‌شود.")],
        "قواعد ارزان، سریع و قابل پیش‌بینی‌اند و اول اجرا می‌شوند. یک classifier مبتنی بر LLM می‌تواند روی آن‌ها اضافه شود "
        "برای چیزی که regex نمی‌گیرد. هر لایه‌ی LLM یک بررسی با کد پشتش دارد.",
        ["eval/redteam.yaml را بخوان؛ دو مورد عمداً «known gap» هستند.",
         "مرحله را اجرا کن؛ نرخ گرفتن حمله‌های ورودی و جواب‌های بد را ببین.",
         "یکی از known gapها را با اصلاح الگو در src/support/guardrails.py ببند و دوباره اجرا کن؛ بعد تست‌ها را اجرا کن.",
         "یک حمله‌ی جدید به فارسی/آلمانی بنویس و ببین گرفته می‌شود یا نه."],
        [Task("stage5_redteam", "red-team روی guardrailها", _script("stage5_redteam.py"), needs=["pkg_core"], minutes="زیر ۱"),
         Task("tests_guardrails", "تست‌های guardrail", _pytest("tests/test_guardrails.py"), needs=["pkg_core"], minutes="زیر ۱")],
        [],
        ["stage5_redteam.json"],
        ["regex همه چیز را نمی‌گیرد؛ نرخ ۱۰۰٪ روی فهرست خودت یعنی فهرست کوچک است، نه سیستم امن.",
         "false positive هم هزینه دارد: جواب درستی که به خاطر عدد مجاز رد شود، ارجاع بی‌دلیل است.",
         "PII را قبل از لاگ پنهان کن، نه بعد."],
        ["چرا injection را مسدود نکردی و فقط ابزار را گرفتی؟", "بررسی عدد ساختگی چطور کار می‌کند و کجا شکست می‌خورد؟",
         "لایه‌های دفاعی این agent را نام ببر."],
        ["classifier امنیتی (مثلاً Llama Guard یا یک مدل کوچک fine-tuneشده).",
         "canary token در system prompt برای تشخیص نشت.",
         "ارزیابی خودکار با مجموعه‌ی حمله‌ی عمومی (مثل garak یا PyRIT).",
         "سیاست rate limit و تشخیص سوءاستفاده در سطح کاربر."],
        ["eval_guardrails"],
        ["scripts/stage5_redteam.py", "src/support/guardrails.py", "eval/redteam.yaml"],
    ),
    Stage(
        6, "ارزیابی کل مکالمه", "End-to-end evaluation",
        "کل گفتگو را با مشتری شبیه‌سازی‌شده بسنجی؛ «جواب درست» را کد (policy.py) تعیین کند، نتیجه را از دیتابیس بخوانی، و فاصله‌ی اطمینان بدهی.",
        [("مشتری شبیه‌سازی‌شده", "یک LLM با هدف مشخص (مثلاً لغو سفارش X) که با agent حرف می‌زند."),
         ("ground truth با کد", "برای هر سناریو، همان تابع‌های policy.py نتیجه‌ی درست را تعیین می‌کنند؛ LLM قاضی نتیجه نیست."),
         ("bootstrap", "با نمونه‌گیری دوباره از سناریوها، فاصله‌ی اطمینان ۹۵٪ برای نرخ موفقیت."),
         ("LLM judge اعتبارسنجی‌شده", "برای لحن و وضوح، قاضی LLM؛ ولی اول با برچسب‌های خودت توافق (kappa) را بسنج."),
         ("paired bootstrap", "مقایسه‌ی دو agent روی همان سناریوها؛ تفاوت واقعی است یا شانس؟")],
        "دقت intent یا recall بازیابی نمی‌گوید مشتری به هدفش رسید یا نه. فقط ارزیابی کل گفتگو، با نتیجه‌ای که از دیتابیس خوانده می‌شود، "
        "Automation و False Automation و نقض قاعده را واقعاً اندازه می‌گیرد.",
        ["با evaluation.n_run = 20 شروع کن (کند است: LLM در دو طرف).",
         "مرحله را اجرا کن؛ task_success با فاصله‌ی اطمینان، automation، false automation و نقض قاعده را ببین.",
         "اگر مدل مشتری و agent یکی است، برای آزمون سخت‌تر مدل مشتری را عوض کن.",
         "«اعتبارسنجی LLM judge» را اجرا کن؛ در صفحه‌ی «برچسب‌زنی judge» حداقل ۳۰ جواب را برچسب بزن؛ دوباره اجرا کن.",
         "(اختیاری) مقایسه‌ی سه agent: plain، LangGraph و create_agent روی همان سناریوها."],
        [Task("stage6_eval", "ارزیابی با مشتری شبیه‌سازی‌شده", _script("stage6_eval.py"),
              needs=["pkg_core", "db", "intent_model", "ollama", "ollama_model"], minutes="۱۰–۶۰"),
         Task("stage6_judge", "اعتبارسنجی LLM judge", _script("stage6_judge.py"),
              needs=["pkg_core", "stage6_runs", "ollama"], minutes="۱–۵"),
         Task("lc_stage6_compare", "مقایسه‌ی سه agent (paired bootstrap)", _script("lc_stage6_compare.py"),
              needs=["pkg_lc", "db", "intent_model", "ollama", "ollama_model"], minutes="۳۰–۱۲۰", lc=True),
         Task("tests_eval", "تست‌های ارزیابی", _pytest("tests/test_evaluation.py"), needs=["pkg_core"], minutes="زیر ۱")],
        ["evaluation", "llm"],
        ["stage6_summary.json", "stage6_runs.jsonl", "stage6_judge.json"],
        ["۲۰ سناریو فاصله‌ی اطمینان پهنی می‌دهد؛ عدد تنها را گزارش نکن.",
         "یک مدل در دو طرف، آزمون را آسان‌تر می‌کند (agent و مشتری یک‌جور فکر می‌کنند).",
         "قاضی LLM بدون اعتبارسنجی، فقط یک نظر دیگر است."],
        ["چرا نتیجه را از دیتابیس می‌خوانی نه از متن گفتگو؟", "فاصله‌ی اطمینان را چطور حساب کردی؟",
         "LLM judge را چطور اعتبارسنجی کردی؟"],
        ["مجموعه‌ی regression در CI: هر PR روی ۵۰ سناریو اجرا شود.", "ارزیابی انسانی ساختاریافته و rubric.",
         "تولید سناریوی متنوع‌تر (persona، زبان، خشم) و تحلیل خطا به تفکیک دسته.",
         "trace-based eval با LangSmith/Langfuse و مقایسه‌ی نسخه‌ها."],
        ["eval_guardrails", "multi_turn", "auto_vs_handoff"],
        ["scripts/stage6_eval.py", "scripts/stage6_judge.py", "src/support/evaluation.py"],
    ),
    Stage(
        7, "آلمانی و ورودی نویزی", "German and noisy input",
        "ببینی مدل با غلط تایپی و زبان دوم چقدر افت می‌کند، و test set آلمانیِ بازبینی‌شده بسازی.",
        [("منحنی دقت در برابر نویز", "دقت در سطح نویز ۰ تا ۳ (غلط تایپی، حذف علامت، حذف please)؛ شیب منحنی مهم است."),
         ("نویز کنترل‌شده", "همان متن + همان سطح + همان seed = همان خروجی؛ پس منحنی تکرارپذیر است."),
         ("ترجمه‌ی ماشینی + بازبینی انسانی", "ترجمه خیلی تمیز و رسمی است؛ نمونه را دستی بررسی کن و چند پیام خودت بنویس.")],
        "آگهی «ورودی نویزی» و «چندزبانه» می‌خواهد. بدون عدد، این ادعا است؛ منحنی و test آلمانی آن را قابل اندازه‌گیری می‌کنند.",
        ["مرحله را اجرا کن؛ منحنی نویز ساخته می‌شود و فایل ترجمه برای بازبینی ایجاد می‌شود.",
         "data/processed/intents_test_de_TO_REVIEW.csv را باز کن، ترجمه‌های بد را ok=False کن، چند پیام خودت اضافه کن، "
         "با نام intents_test_de.csv ذخیره کن.",
         "دوباره اجرا کن تا دقت آلمانی گزارش شود. افت نسبت به انگلیسی را تحلیل کن."],
        [Task("stage7_robustness", "منحنی نویز و test آلمانی", _script("stage7_robustness.py"),
              needs=["pkg_core", "data_splits", "intent_model"], minutes="۱–۱۵")],
        ["robustness"],
        ["stage7_robustness.json", "../data/processed/intents_test_de.csv"],
        ["TF-IDF روی آلمانی ضعیف است چون روی انگلیسی آموزش دیده؛ embedding چندزبانه را مقایسه کن.",
         "ترجمه‌ی بازبینی‌نشده را گزارش نکن.", "تشخیص زبان stopword-محور برای پیام کوتاه None می‌دهد؛ این عمدی است."],
        ["چطور مقاومت در برابر غلط تایپی را اندازه گرفتی؟", "test آلمانی را چطور ساختی و چرا بازبینی دستی؟",
         "character n-gram چرا به غلط تایپی کمک می‌کند؟"],
        ["تشخیص زبان با fastText lid یا lingua.", "data augmentation با نویز در train.",
         "داده‌ی واقعی آلمانی و گویش‌ها؛ ارزیابی جداگانه برای هر زبان در production.",
         "ترجمه‌ی رفت‌وبرگشت (back-translation) برای تولید داده."],
        ["multilingual_rag"],
        ["scripts/stage7_robustness.py", "src/support/robustness.py"],
    ),
    Stage(
        8, "سرو کردن و پایش", "Serving and monitoring",
        "agent را پشت API ببری، زیر بار تأخیر p95 را بسنجی، و drift را از traceها تشخیص دهی.",
        [("p50 / p95 / p99", "تأخیری که ۵۰، ۹۵ و ۹۹ درصد درخواست‌ها زیر آن‌اند؛ کاربر p95 را حس می‌کند نه میانگین را."),
         ("load test", "چند کاربر هم‌زمان؛ throughput و خطا زیر بار."),
         ("PSI", "Population Stability Index؛ تغییر توزیع intentها بین دو پنجره. <0٫1 پایدار، >0٫25 بررسی."),
         ("trace", "رکورد هر نوبت (مسیر، intent، تأخیر) با PII پنهان؛ پایه‌ی پایش و دیباگ."),
         ("Docker", "همان محیط روی هر سیستم؛ Ollama بیرون از container اجرا می‌شود.")],
        "مدلی که فقط در نوت‌بوک کار می‌کند محصول نیست. FastAPI ساده و سریع است، trace ارزان‌ترین ابزار دیباگ است، "
        "و drift اولین علامت این است که ارزیابی دیروز دیگر معتبر نیست.",
        ["«اجرای API» را بزن (سرویس روی پورت serving.port بالا می‌آید).",
         "load test را اجرا کن؛ p95 را با serving.p95_target_ms مقایسه کن.",
         "«پایش» را اجرا کن: تأخیر، توزیع مسیرها و (با ترافیک کافی) drift.",
         "API را متوقف کن. (اختیاری) docker build -t support-agent . و اجرای container."],
        [Task("serve_api", "اجرای API (سرویس)", [PY, "-m", "uvicorn", "app.main:app", "--port", "{serving.port}"],
              kind="service", needs=["pkg_serve", "db", "intent_model", "ollama", "ollama_model"]),
         Task("loadtest", "load test", _script("loadtest.py"), needs=["pkg_serve"], minutes="۱–۱۰",
              note="اول API را اجرا کن."),
         Task("stage8_monitor", "پایش: تأخیر و drift", _script("stage8_monitor.py"), needs=["pkg_core"], minutes="زیر ۱"),
         Task("serve_api_lc", "اجرای API نسخه‌ی LangGraph (سرویس)",
              [PY, "-m", "uvicorn", "app.main_lc:app", "--port", "{serving.port}"], kind="service",
              needs=["pkg_lc", "pkg_serve", "db", "intent_model", "ollama"], lc=True)],
        ["serving", "monitoring"],
        ["stage8_loadtest.json", "stage8_monitor.json"],
        ["Ollama روی لپ‌تاپ معمولاً یک درخواست را هم‌زمان پردازش می‌کند؛ کاربر هم‌زمان بیشتر = صف و p95 بالاتر.",
         "PII را قبل از نوشتن trace پنهان کن.", "drift بدون پنجره‌ی مرجع معنی ندارد."],
        ["p95 را چطور اندازه گرفتی و چرا نه میانگین؟", "drift را چطور تشخیص می‌دهی؟",
         "اگر p95 از هدف بالاتر بود چه می‌کردی؟"],
        ["OpenTelemetry و Prometheus/Grafana.", "صف و autoscaling، batching درخواست‌ها، vLLM برای سرو مدل.",
         "rate limit، احراز هویت، و canary deployment.", "هشدار خودکار روی drift و افت کیفیت."],
        ["production"],
        ["app/main.py", "scripts/loadtest.py", "scripts/stage8_monitor.py", "src/support/monitoring.py", "Dockerfile"],
    ),
    Stage(
        9, "آزمایش A/B و fine-tune با LoRA", "Experiments and LoRA",
        "یک A/B را درست طراحی و خوانش کنی (حجم نمونه قبل از شروع، تخصیص پایدار، چک SRM، معیار guardrail) و یک مدل کوچک را با LoRA fine-tune کنی.",
        [("حجم نمونه", "قبل از آزمایش: برای دیدن +۳ درصد از ۶۰٪، چند گفتگو در هر بازو لازم است."),
         ("تخصیص پایدار", "hash(نام آزمایش + session) → بازو؛ همان کاربر همیشه همان بازو، بدون دیتابیس."),
         ("SRM", "اگر تقسیم ۵۰/۵۰ به ۵۳/۴۷ رسید، تخصیص خراب است؛ نتیجه را نخوان."),
         ("معیار guardrail", "معیاری که نباید بدتر شود (False Automation)؛ بهبود معیار اصلی کافی نیست."),
         ("LoRA", "به‌جای همه‌ی وزن‌ها، دو ماتریس کوچک آموزش داده می‌شوند (~۱٪ وزن‌ها)؛ روی GPU رایگان Colab ممکن است.")],
        "آزمایش بدون حجم نمونه یا با تخصیص خراب نتیجه‌ی غلط با اطمینان کاذب می‌دهد. LoRA نشان می‌دهد کی fine-tune به هزینه‌اش می‌ارزد.",
        ["پارامترهای experiments را تنظیم کن (نرخ پایه از مرحله‌ی ۶).",
         "مرحله را اجرا کن: حجم نمونه، تخصیص نمونه، SRM، آزمون اصلی و guardrail، و تصمیم ship.",
         "«ساخت بسته‌ی Colab» را بزن، zip را در Colab آپلود کن، اسکریپت LoRA را اجرا کن، stage9_lora.json را در results/ بگذار.",
         "نتیجه‌ی LoRA را با برنده‌ی مرحله‌ی ۱ مقایسه کن (دقت، سرعت، هزینه)."],
        [Task("stage9_ab", "طراحی و خوانش A/B", _script("stage9_ab.py"), needs=["pkg_core"], minutes="زیر ۱"),
         Task("tests_experiments", "تست‌های آزمایش و پایش", _pytest("tests/test_monitoring_experiments.py"),
              needs=["pkg_core"], minutes="زیر ۱")],
        ["experiments", "lora"],
        ["stage9_ab.json", "stage9_lora.json"],
        ["نگاه کردن مکرر به نتیجه و توقف وقتی معنادار شد (peeking) خطای نوع اول را بالا می‌برد.",
         "SRM را قبل از هر چیز چک کن.", "LoRA را روی همان split مرحله‌ی ۱ ارزیابی کن، نه split جدید."],
        ["حجم نمونه را چطور حساب کردی؟", "SRM چیست و چرا مهم است؟", "LoRA چطور کار می‌کند و کی ارزشش را دارد؟"],
        ["آزمون ترتیبی (sequential testing) یا always-valid p-value.", "CUPED برای کاهش واریانس.",
         "multi-armed bandit برای تخصیص پویا.", "QLoRA، distillation از LLM به مدل کوچک، و ارزیابی هزینه به ازای هر گفتگو."],
        ["ab_test"],
        ["scripts/stage9_ab.py", "scripts/stage9_lora_colab.py", "src/support/experiments.py"],
    ),
]

TASKS: dict[str, tuple[Stage, Task]] = {t.id: (s, t) for s in STAGES for t in s.tasks}


def stage(stage_id: int) -> Stage:
    return STAGES[stage_id]


def as_dict(s: Stage) -> dict:
    d = asdict(s)
    d["concepts"] = [{"term": a, "explain": b} for a, b in s.concepts]
    d["job_ad"] = [{"id": j, "text": JOB_AD[j]} for j in s.job_ad]
    return d
