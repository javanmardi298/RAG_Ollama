# ساخت MCP server (spec 2026) و همکاری agent ها با A2A
_Build an MCP server (2026 spec) and agent-to-agent with A2A_ · سطح میانی · 1–2 هفته

> **وضعیت:** راهنمای مرحله‌ای (بدون تمرین خودکار). برای اسکلت کد قابل اجرا: `python -m support.panel.presets scaffold p26_mcp_a2a` یا دکمه‌ی «ساخت اسکلت» در پنل. درس تعاملی کامل برای این پروژه هنوز ساخته نشده؛ ساختار آن مثل درس‌های `p01_faq_search` است.

## کاربرد واقعی
اتصال ابزارهای سازمان به Claude Desktop/Code و هر کلاینت MCP؛ همکاری agent های تیم‌های مختلف با A2A (Linux Foundation).
## مسئله
هر ابزار برای هر کلاینت یک اتصال جدا می‌خواهد؛ agent های مستقل راه استاندارد برای کشف و فراخوانی هم ندارند.
## هدف
یک MCP server با ابزار، resource و prompt بسازی (با مجوزهای امن مثل پنل همین repo)، آن را به Claude Desktop وصل کنی، و یک agent را از طریق A2A با Agent Card در دسترس agent دیگر بگذاری.

## پیش‌نیاز
- [p10_research_agent](../p10_research_agent/README.md)

## داده
- [MCP specification](https://modelcontextprotocol.io/specification) · MIT · نسخه‌ی 2026-07-28: هسته‌ی stateless، حذف session
- [A2A protocol](https://a2a-protocol.org/) · Apache 2.0 · v1.0، Agent Card امضاشده

## قطعه‌ها
- `mcp_server_sdk` ساخت MCP server (spec 2026-07-28، stateless): support.panel.mcp_server
- `mcp` ابزارها از طریق MCP: support.panel.mcp_server
- `a2a` A2A v1.0 (Agent Card امضاشده، agent↔agent): a2a-sdk (Linux Foundation)
- `tool_agent` agent با tool calling: support.agent
- `confirmation` تأیید صریح قبل از عمل: support.agent
- `auth_ratelimit` احراز هویت و rate limit: FastAPI middleware / API gateway
- `tracing` tracing: OpenTelemetry / Langfuse (محلی) / LangSmith

## گام 1: MCP server
**یاد بگیر**
- tools / resources / prompts
- stdio در برابر Streamable HTTP، stateless

**بساز**
- run.py: سه ابزار فقط‌خواندنی + یک ابزار نوشتنی با تأیید
- اتصال به Claude Desktop (claude_desktop_config.json)

**بسنج:** ابزارها در Claude دیده و درست صدا زده می‌شوند

**دام:** ابزار نوشتنی بدون تأیید و allow-list = خطر.

## گام 2: امنیت
**یاد بگیر**
- کمترین دسترسی، مسیرهای مجاز، اسرار از env
- tool poisoning و توضیح ابزارهای مخرب

**بساز**
- allow-list مسیر، رد خواندن .env (مثل support.panel)

**بسنج:** تست‌های منفی (خواندن .env، مسیر بیرون)

**دام:** به توضیح ابزارهای شخص ثالث اعتماد نکن.

## گام 3: A2A
**یاد بگیر**
- Agent Card، task، streaming
- MCP = ابزار برای agent؛ A2A = agent با agent

**بساز**
- agent p10 را با A2A در دسترس بگذار و از agent دیگر صدا بزن

**بسنج:** یک task انتها-به-انتها

**دام:** اعتماد بین agent ها: امضا و احراز هویت.

## معیارها
- tool-call success rate
- negative security tests passed
- end-to-end A2A task latency

## سؤال مصاحبه
- MCP و A2A چه فرقی دارند؟
- چه تغییری در spec 2026 آمد؟
- MCP server را چطور امن کردی؟

## نسخه‌ی پیشرفته
- OAuth برای MCP راه‌دور
- انتشار در MCP registry
- A2A با چند agent و orchestrator
