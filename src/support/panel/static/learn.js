"use strict";
// Lessons page: lesson text, a code editor, automatic checks, hints, quiz, model choice and a teacher chat.
// Uses helpers from app.js ($, api, esc, toast, mdToHtml, go, route). Everything runs against the local panel API (/api/lessons).

const L = { data: null, cur: null, saveTimer: null, hintsShown: [], chat: [] };
const PROVIDER_FA = { offline: "offline (بدون مدل)", ollama: "Ollama (محلی)", anthropic: "Claude (API)", opencode: "OpenCode", openai_compatible: "سرور سازگار با OpenAI" };

async function learnLoad(force) {
  if (force || !L.data) L.data = await api("/api/lessons");
  return L.data;
}
const lessonInfo = (id) => L.data.tree.find((t) => t.lesson === id);
const stepShort = (s) => s.slice(0, 6);                      // "step01"

window.docGo = (path) => {
  let m = path.match(/^lessons\/([^/]+)\/(step\d\d_[^/]+)\/lesson\.md$/);
  if (m) return go(`/learn/${m[1]}/${m[2]}`);
  m = path.match(/^lessons\/([^/]+)\/README\.md$/);
  if (m && lessonInfo(m[1])?.interactive) return go(`/learn/${m[1]}`);
  go("/doc?path=" + encodeURIComponent(path));
};

async function pageLearn(main, r) {
  await learnLoad(true);
  if (!r.arg) return learnHome(main);
  const info = lessonInfo(r.arg);
  if (!info) throw new Error("درس پیدا نشد: " + r.arg);
  if (!info.interactive) return go("/doc?path=" + encodeURIComponent(info.readme));
  const step = r.arg2 || (info.steps.find((s) => !s.passed) || info.steps[0]).step;
  if (!r.arg2) { location.replace(`#/learn/${r.arg}/${step}`); return; }
  return learnStep(main, r.arg, step);
}

// ---------- home ----------
function learnHome(main) {
  const inter = L.data.tree.filter((t) => t.interactive), guides = L.data.tree.filter((t) => !t.interactive);
  const card = (t) => {
    const done = t.steps.filter((s) => s.passed).length, pct = Math.round(100 * done / t.steps.length);
    const next = t.steps.find((s) => !s.passed);
    return `<div class="card pad"><h3 style="margin-bottom:4px">${esc(t.lesson)}</h3>
      <div class="note">${t.steps.length} گام · ${done} انجام شده</div>
      <div class="bar" style="margin:8px 0"><i style="width:${pct}%"></i></div>
      <button class="btn p sm" onclick="go('/learn/${t.lesson}/${(next || t.steps[0]).step}')">${done === 0 ? "شروع" : done === t.steps.length ? "مرور" : "ادامه"}</button>
      <button class="btn sm" onclick="go('/doc?path=${encodeURIComponent(t.readme)}')">معرفی</button></div>`;
  };
  main.innerHTML = `<div class="card pad"><h2>درس‌های تعاملی</h2>
    <p class="note" style="margin:6px 0 0">هر گام: متن آموزشی ← کد ناقص که خودت کامل می‌کنی ← «بررسی» (تست خودکار) ← راهنمایی سه‌سطحی ← امتحان کوتاه. مدل زبانی را بالای صفحه‌ی هر گام انتخاب می‌کنی؛ پیش‌فرض بدون مدل است و همه‌چیز کار می‌کند.</p></div>
    <div class="grid2" style="margin-top:14px">${inter.map(card).join("")}</div>
    <div class="card pad" style="margin-top:14px"><h4>راهنمای مرحله‌ای (هنوز بدون تمرین خودکار)</h4>
      <div class="note" style="margin:6px 0">${guides.map((t) => `<a onclick="go('/doc?path=${encodeURIComponent(t.readme)}')">${esc(t.lesson)}</a>`).join(" · ")}</div></div>`;
}

// ---------- provider bar ----------
function provBar() {
  const p = L.data.provider;
  return `<div class="card pad provbar"><div class="row" style="gap:8px;flex-wrap:wrap;align-items:center">
    <b>مدل درس‌ها:</b>
    <select id="pvKind">${L.data.providers.map((k) => `<option value="${k}" ${p.provider === k ? "selected" : ""}>${PROVIDER_FA[k] || k}</option>`).join("")}</select>
    <input id="pvModel" placeholder="نام مدل" value="${esc(p.model)}" style="width:190px">
    <input id="pvBase" placeholder="http://localhost:1234/v1" value="${esc(p.api_base)}" style="width:210px">
    <label class="note">سقف $ <input id="pvBudget" type="number" min="0" step="0.1" value="${p.budget_usd}" style="width:70px"></label>
    <label class="note">قیمت ورودی/M <input id="pvIn" type="number" min="0" step="0.01" value="${p.price_in}" style="width:70px"></label>
    <label class="note">خروجی/M <input id="pvOut" type="number" min="0" step="0.01" value="${p.price_out}" style="width:70px"></label>
    <button class="btn sm" id="pvSave">ذخیره</button><button class="btn sm" id="pvTest">تست اتصال</button>
    <span class="note" id="pvMsg"></span></div>
    <div class="note" id="pvHelp" style="margin-top:6px"></div></div>`;
}
const PV_HELP = {
  offline: "بدون مدل: شکل کار را نشان می‌دهد؛ تست‌ها همیشه کار می‌کنند.",
  ollama: "Ollama باید روشن باشد و مدل دانلود شده باشد (مثلاً qwen2.5:7b). آدرس سرور از تنظیمات پروژه/.env می‌آید.",
  anthropic: "کلید API (sk-ant-…) در صفحه‌ی «اتصال‌ها» ذخیره می‌شود. اشتراک Claude.ai کلید API نیست. قیمت‌ها را از صفحه‌ی قیمت Anthropic بگذار تا سقف هزینه کار کند.",
  opencode: "مدل به شکل provider/model (دستور `opencode models`). OpenCode باید نصب و وارد provider شده باشد.",
  openai_compatible: "آدرس پایه‌ی سرور (LM Studio، vLLM، OpenRouter) و نام مدل؛ کلید در OPENAI_API_KEY."};
function wireProv() {
  const kind = $("#pvKind"); if (!kind) return;
  const sync = () => {
    $("#pvModel").style.display = kind.value === "offline" ? "none" : "";
    $("#pvBase").style.display = kind.value === "openai_compatible" ? "" : "none";
    $("#pvHelp").textContent = PV_HELP[kind.value] || "";
  };
  kind.onchange = sync; sync();
  const read = () => ({ provider: kind.value, model: $("#pvModel").value.trim(), api_base: $("#pvBase").value.trim(),
    budget_usd: +$("#pvBudget").value || 0, price_in: +$("#pvIn").value || 0, price_out: +$("#pvOut").value || 0 });
  $("#pvSave").onclick = async () => {
    try { L.data.provider = await api("/api/lessons/provider", read()); $("#pvMsg").textContent = "ذخیره شد"; } catch (e) { $("#pvMsg").textContent = "خطا: " + e.message; }
  };
  $("#pvTest").onclick = async () => {
    $("#pvMsg").textContent = "در حال تست…";
    try { L.data.provider = await api("/api/lessons/provider", read()); const t = await api("/api/lessons/provider/test", {});
      $("#pvMsg").textContent = t.ok ? `✓ پاسخ در ${t.seconds}s: ${t.reply}` : "✗ " + t.error; } catch (e) { $("#pvMsg").textContent = "✗ " + e.message; }
  };
}

// ---------- step page ----------
async function learnStep(main, lesson, step) {
  const d = await api(`/api/lessons/${lesson}/${step}`);
  const info = lessonInfo(lesson);
  L.cur = { lesson, step, d }; L.hintsShown = []; L.chat = [];
  docBase = `lessons/${lesson}/${step}`;
  const chips = info.steps.map((s) => `<button class="chip2 ${s.step === step ? "cur" : ""} ${s.passed ? "done" : ""}" title="${esc(s.title)}"
      onclick="go('/learn/${lesson}/${s.step}')">${s.passed ? "✓ " : ""}${stepShort(s.step).replace("step0", "")}</button>`).join("");
  const lessonOpts = L.data.tree.filter((t) => t.interactive).map((t) => `<option value="${t.lesson}" ${t.lesson === lesson ? "selected" : ""}>${esc(t.lesson)}</option>`).join("");
  main.innerHTML = `${provBar()}
    <div class="card pad learnhead"><div class="row" style="gap:10px;flex-wrap:wrap;align-items:center">
      <select id="lsSel">${lessonOpts}</select><div class="chips2">${chips}</div><span class="sp"></span>
      <a class="note" onclick="go('/learn')">همه‌ی درس‌ها</a></div></div>
    <div class="learncols">
      <div class="card pad mddoc" id="lessonText">${mdToHtml(d.text)}
        <div class="row" style="margin-top:18px;gap:8px">${d.prev ? `<button class="btn" onclick="go('/learn/${lesson}/${d.prev}')">→ گام قبل</button>` : ""}<span class="sp"></span>
        ${d.next ? `<button class="btn p" onclick="go('/learn/${lesson}/${d.next}')">گام بعد ←</button>` : ""}</div></div>
      <div class="learnside">
        <div class="card pad"><div class="row" style="align-items:center;gap:8px"><h4>کد تو</h4><code class="note mono" style="direction:ltr">${esc(d.answer_file)}</code><span class="sp"></span><span class="note" id="saveState"></span></div>
          <textarea id="code" class="code" spellcheck="false" dir="ltr">${esc(d.code)}</textarea>
          <div class="row" style="gap:6px;flex-wrap:wrap;margin-top:8px">
            <button class="btn p" id="bCheck">بررسی ▶ <small>Ctrl+Enter</small></button>
            ${d.runnable ? `<button class="btn" id="bRun" title="فایل را با مدل انتخاب‌شده اجرا می‌کند">اجرا با مدل</button>` : ""}
            <button class="btn" id="bHint">راهنمایی <small id="hintCount">${d.progress.hints || 0}/${d.hints_total}</small></button>
            <button class="btn" id="bSol">جواب مرجع</button><button class="btn bad sm" id="bReset">شروع دوباره</button></div>
          <div id="checkOut" style="margin-top:10px"></div><div id="hintOut"></div><div id="solOut"></div><pre id="runOut" class="runout" style="display:none"></pre></div>
        <div class="card pad" id="quizCard"></div>
        <div class="card pad"><h4>از معلم بپرس (Claude)</h4>
          <div class="note" style="margin:4px 0">راهنمایی می‌کند ولی جواب کامل نمی‌دهد. نیاز به کلید API در «اتصال‌ها» (یا از Claude Desktop/OpenCode با MCP).</div>
          <div class="msgs" id="askMsgs" style="max-height:240px"></div>
          <div class="ask"><textarea id="askIn" placeholder="مثلاً: چرا تست دوم رد می‌شود؟ فقط راهنمایی کن."></textarea><button class="btn p" id="askSend">ارسال</button></div></div>
      </div></div>`;
  $("#lsSel").onchange = (e) => go(`/learn/${e.target.value}`);
  wireProv(); wireEditor(); drawQuiz(d); drawAsk();
  if (d.progress.passed) $("#checkOut").innerHTML = `<div class="pill ok">این گام را قبلاً پاس کرده‌ای</div>`;
}

function wireEditor() {
  const ta = $("#code");
  const save = async () => { try { await api(`/api/lessons/${L.cur.lesson}/${L.cur.step}/answer`, { code: ta.value }, "PUT"); $("#saveState").textContent = "ذخیره شد"; } catch (e) { $("#saveState").textContent = "ذخیره نشد: " + e.message; } };
  ta.addEventListener("input", () => { $("#saveState").textContent = "…"; clearTimeout(L.saveTimer); L.saveTimer = setTimeout(save, 1200); });
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Tab") { e.preventDefault(); const s = ta.selectionStart; ta.setRangeText("    ", s, ta.selectionEnd, "end"); ta.dispatchEvent(new Event("input")); }
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); doCheck(); }
  });
  $("#bCheck").onclick = doCheck; $("#bHint").onclick = doHint; $("#bSol").onclick = doSolution; $("#bReset").onclick = doReset;
  if ($("#bRun")) $("#bRun").onclick = doRun;
  $("#askSend").onclick = askSend;
  $("#askIn").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askSend(); } });
}
const stepApi = (what) => `/api/lessons/${L.cur.lesson}/${L.cur.step}/${what}`;
const busy = (id, on, label) => { const b = $(id); if (!b) return; b.disabled = on; if (label !== undefined) b.dataset.l = b.dataset.l || b.innerHTML; b.innerHTML = on ? "…" : (b.dataset.l || b.innerHTML); };

async function doCheck() {
  clearTimeout(L.saveTimer); busy("#bCheck", true, "");
  try {
    const r = await api(stepApi("check"), { code: $("#code").value });
    $("#saveState").textContent = "ذخیره شد";
    if (r.skipped) { $("#checkOut").innerHTML = `<div class="adv warn"><span class="ic">△</span><div>${esc(r.skipped)}</div></div>`; return; }
    $("#checkOut").innerHTML = `<ul class="chk">${r.results.map((x) => `<li class="${x.ok ? "ok" : "bad"}"><b>${x.ok ? "✓" : "✗"}</b> ${esc(x.name)}${x.ok ? "" :
      `<div class="mono msg">${esc(x.message)}</div>${(x.trace || []).length ? `<pre class="mono tr">${esc(x.trace.join("\n"))}</pre>` : ""}`}</li>`).join("")}</ul>
      ${r.passed ? `<div class="pill ok" style="margin-top:6px">پاس شد 🎉 ${L.cur.d.quiz.length ? "حالا امتحان کوتاه را بزن." : ""}</div>` :
        `<div class="note" style="margin-top:6px">خط ✗ را بخوان؛ گیر کردی «راهنمایی» بزن.</div>`}`;
    if (r.passed) { await learnLoad(true); refreshChips(); if ($("#quizCard")) $("#quizCard").scrollIntoView({ block: "nearest" }); }
  } catch (e) { $("#checkOut").innerHTML = `<div class="adv error"><span class="ic">!</span><div>${esc(e.message)}</div></div>`; }
  finally { busy("#bCheck", false); }
}
function refreshChips() {
  const info = lessonInfo(L.cur.lesson);
  $$(".chips2 .chip2").forEach((b, i) => { const s = info.steps[i]; b.classList.toggle("done", s.passed); b.innerHTML = (s.passed ? "✓ " : "") + stepShort(s.step).replace("step0", ""); });
}
async function doRun() {
  const out = $("#runOut"); out.style.display = ""; out.textContent = "در حال اجرا با مدل انتخاب‌شده… (ممکن است چند دقیقه طول بکشد)";
  busy("#bRun", true, "");
  try {
    const r = await api(stepApi("run"), { code: $("#code").value });
    out.textContent = (r.stdout || "") + (r.stderr ? "\n--- stderr ---\n" + r.stderr : "") || "(خروجی خالی)";
  } catch (e) { out.textContent = "خطا: " + e.message; }
  finally { busy("#bRun", false); }
}
async function doHint() {
  try {
    const h = await api(stepApi("hint"), { level: 0 });
    L.hintsShown = L.hintsShown.filter((x) => x.level !== h.level); L.hintsShown.push(h);
    $("#hintCount").textContent = `${h.level}/${h.of}`;
    $("#hintOut").innerHTML = L.hintsShown.sort((a, b) => a.level - b.level).map((x) => `<div class="hintbox"><b>راهنمایی ${x.level}/${x.of}</b>${mdToHtml(x.hint)}</div>`).join("");
  } catch (e) { toast(e.message); }
}
async function doSolution() {
  try {
    let r = await api(stepApi("solution"), { force: false });
    if (!r.ok) { if (!confirm(r.error + "\n\nبه‌هرحال جواب را ببینم؟")) return; r = await api(stepApi("solution"), { force: true }); }
    $("#solOut").innerHTML = `<details open class="hintbox"><summary><b>جواب مرجع</b></summary><pre class="mono" dir="ltr">${esc(r.code)}</pre>
      <button class="btn sm" id="solCopy">گذاشتن در ویرایشگر</button></details>`;
    $("#solCopy").onclick = () => { $("#code").value = r.code; $("#code").dispatchEvent(new Event("input")); };
  } catch (e) { toast(e.message); }
}
async function doReset() {
  if (!confirm("کد این گام به نسخه‌ی اولیه برگردد؟ کد فعلی از بین می‌رود.")) return;
  await api(stepApi("reset"), {});
  const d = await api(`/api/lessons/${L.cur.lesson}/${L.cur.step}`); $("#code").value = d.code; $("#checkOut").innerHTML = "";
}

// ---------- quiz ----------
function drawQuiz(d) {
  const el = $("#quizCard"); if (!el) return;
  if (!d.quiz.length) { el.innerHTML = ""; return; }
  el.innerHTML = `<h4>امتحان کوتاه</h4>${d.quiz.map((q, i) => `<div class="qz" data-i="${i}"><div style="margin:8px 0 4px"><b>${i + 1}.</b> ${esc(q.q)}</div>
    ${q.options.map((o, k) => `<label class="qopt"><input type="radio" name="q${i}" value="${k}"> ${esc(o)}</label>`).join("")}<div class="qres note"></div></div>`).join("")}
    <button class="btn p sm" id="qSend" style="margin-top:8px">ثبت پاسخ‌ها</button> <span class="note" id="qScore"></span>`;
  $("#qSend").onclick = async () => {
    const answers = d.quiz.map((_, i) => { const c = $(`input[name=q${i}]:checked`); return c ? +c.value : -1; });
    if (answers.includes(-1)) return toast("به همه‌ی سؤال‌ها جواب بده");
    try {
      const r = await api(stepApi("quiz"), { answers });
      r.results.forEach((x, i) => { const b = $(`.qz[data-i="${i}"] .qres`); b.innerHTML = `<span class="pill ${x.ok ? "ok" : "bad"}">${x.ok ? "درست" : "نادرست"}</span> ${esc(x.why)}`; });
      $("#qScore").textContent = `${r.score}/${r.total}` + (r.wrong.length ? " — سؤال‌های اشتباه در مرور بعدی برمی‌گردند" : " 🎉");
    } catch (e) { toast(e.message); }
  };
}

// ---------- teacher chat ----------
function drawAsk() {
  const box = $("#askMsgs"); if (!box) return;
  const st = L.data.claude;
  box.innerHTML = L.chat.length ? L.chat.map((m) => `<div class="msg ${m.role}">${esc(m.text)}</div>`).join("")
    : `<div class="msg sys">${st.ready ? "یک سؤال یا «به من راهنمایی بده» بنویس." : "Claude وصل نیست: کلید API را در «اتصال‌ها» بگذار."}</div>`;
  box.scrollTop = box.scrollHeight;
}
async function askSend() {
  const el = $("#askIn"), text = el.value.trim(); if (!text) return;
  el.value = ""; L.chat.push({ role: "u", text }); drawAsk();
  const ctx = `teacher mode: the student is on lesson ${L.cur.lesson}, ${L.cur.step}. Use lesson_step / lesson_check; guide with questions and hints, never the full solution.`;
  const b = $("#askSend"); b.disabled = true; b.textContent = "…";
  try { const r = await api("/api/claude/chat", { message: text, chat_id: "learn", context: ctx }); L.chat.push({ role: "a", text: r.reply }); }
  catch (e) { L.chat.push({ role: "sys", text: "خطا: " + e.message }); }
  b.disabled = false; b.textContent = "ارسال"; drawAsk();
}
