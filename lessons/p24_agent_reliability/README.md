# پایایی agent: pass^k، ارزیابی مسیر و حالت نهایی
_Agent reliability: pass^k, trajectory and final-state evaluation_ · سطح میانی · 1–2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p24_agent_reliability` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
agent ای که ۸۰٪ وقت‌ها درست است ولی در ۸ اجرای پشت‌سرهم فقط ۲۰٪ همه درست است؛ معیار tau-bench برای پشتیبانی و خرده‌فروشی.
## مسئله
یک اجرا برای هر سناریو پایایی را نشان نمی‌دهد؛ مشتری تکرار را تجربه می‌کند، نه میانگین را.
## هدف
هر سناریو را k بار اجرا کنی، pass@k و pass^k گزارش کنی، حالت نهایی DB را با gold مقایسه کنی و منبع ناپایداری را پیدا کنی.

## پیش‌نیاز
- [p08_support_agent](../p08_support_agent/README.md)

## داده
- سناریوهای مرحله‌ی ۶ همین repo · evaluation.repeats در configs/project.yaml
- [tau-bench / tau2-bench](https://github.com/sierra-research/tau2-bench) · MIT · معیار مرجع pass^k

## قطعه‌ها
- `sim_user_eval` ارزیابی با کاربر شبیه‌سازی‌شده: support.evaluation
- `pass_k` pass^k (پایایی agent در k اجرا): labkit.metrics.reliability_report
- `trajectory_eval` ارزیابی مسیر agent (ابزار درست، ترتیب، حالت نهایی DB): tau-bench style: حالت نهایی DB را با gold مقایسه کن (support.evaluation الگو است)
- `bootstrap_ci` فاصله‌ی اطمینان bootstrap: support.evaluation
- `run_registry` ثبت اجرا و مقایسه: support.panel.registry
- `cost_ledger` ثبت توکن، هزینه و تأخیر: labkit.ops.Ledger
- `llm_judge` LLM judge اعتبارسنجی‌شده (kappa): support.evaluation

## گام 1: تکرار و pass^k
**یاد بگیر**
- pass@k (حداقل یک موفقیت) در برابر pass^k (همه موفق)
- واریانس از کجا می‌آید: temperature، user simulator، ابزار

**بساز**
- evaluation.repeats=4 و stage6 را اجرا کن

**بسنج:** منحنی pass^k برای k=1..4

**دام:** pass@1 بالا با pass^4 پایین = محصول غیرقابل‌اعتماد.

## گام 2: ارزیابی مسیر و حالت نهایی
**یاد بگیر**
- ابزار درست، ترتیب، آرگومان؛ حالت DB

**بساز**
- برای هر سناریو حالت نهایی مورد انتظار بنویس و diff کن

**بسنج:** نرخ حالت نهایی درست

**دام:** متن پاسخ خوب ولی DB غلط = شکست.

## گام 3: ریشه‌یابی و بهبود
**یاد بگیر**
- دسته‌بندی شکست‌ها
- temperature=0، prompt سفت‌تر، تأیید

**بساز**
- ۳ تغییر و اثرش روی pass^k با CI

**بسنج:** بهبود pass^k با CI

**دام:** یک بار اجرا بعد از تغییر را باور نکن.

## معیارها
- pass^k
- pass@k
- final-state accuracy
- cost per successful task

## سؤال مصاحبه
- pass^k چیست و چرا از pass@1 مهم‌تر است؟
- ناپایداری agent از کجا می‌آید؟
- ارزیابی حالت نهایی را چطور ساختی؟

## نسخه‌ی پیشرفته
- tau2-bench با کاربر دارای ابزار
- مدل‌سازی هزینه‌ی شکست
- تست mutation روی prompt
