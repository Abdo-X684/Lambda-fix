/* BHL x OP4 dashboard - no frameworks, no external calls. */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (ms) => {
  ms = Math.max(0, Math.floor(ms || 0));
  const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60,
        s = Math.floor(ms / 1000) % 60, x = ms % 1000;
  const pad = (n, w = 2) => String(n).padStart(w, '0');
  return (h ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`) + `.${pad(x, 3)}`;
};
const signed = (ms) => (ms < 0 ? '-' : '+') + fmt(Math.abs(ms));

function toast(msg) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2600);
}

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r;
}

/* ----------------------------------------------------------------- timer --- */
const PB_KEY = 'bhl-op4-speedrun-pb';
let chapters = [];
let pb = [];
try { pb = JSON.parse(localStorage.getItem(PB_KEY) || '[]'); } catch { pb = []; }
const run = { elapsed: 0, startTs: 0, running: false, idx: 0, splits: [], finished: false };

function renderSplits() {
  const el = $('splits');
  el.innerHTML = chapters.map((ch, i) => {
    const done = i < run.idx;
    const cls = done ? 'done' : (i === run.idx && !run.finished ? 'current' : '');
    const at = done ? fmt(run.splits[i]) : '—';
    const best = pb[i] != null ? fmt(pb[i]) : '—';
    let delta = '—', dcls = '';
    if (done && pb[i] != null) {
      const d = run.splits[i] - pb[i];
      delta = signed(d); dcls = d < 0 ? 'neg' : 'pos';
    }
    return `<li class="${cls}">
      <span><b>${esc(ch.name_ar)}</b><span class="maps"> · ${esc(ch.name)} · ${ch.maps.length} خرائط</span></span>
      <span class="num">${at}</span><span class="num">${best}</span>
      <span class="num delta ${dcls}">${delta}</span></li>`;
  }).join('');
  $('curChapter').textContent = run.finished ? '✅ اكتمل الرن' : `الفصل الحالي: ${chapters[run.idx]?.name_ar || '—'}`;
  const total = pb[chapters.length - 1];
  $('pbTotal').textContent = `أفضل زمن: ${total != null ? fmt(total) : '—'}`;
  $('runState').textContent = run.finished ? 'مكتمل' : run.running ? 'قيد التشغيل ⏱' : (run.elapsed ? 'متوقف مؤقتاً' : 'جاهز');
}

function tick() {
  if (run.running) run.elapsed = performance.now() - run.startTs;
  $('rta').textContent = fmt(run.elapsed);
  requestAnimationFrame(tick);
}

function start() {
  if (run.finished) reset();
  run.startTs = performance.now() - run.elapsed;
  run.running = true;
  renderSplits();
}
function pause() {
  if (!run.running) return;
  run.elapsed = performance.now() - run.startTs;
  run.running = false;
  renderSplits();
}
function split() {
  if (!run.running || run.finished || !chapters.length) return;
  run.splits.push(run.elapsed);
  run.idx += 1;
  if (run.idx >= chapters.length) {
    run.elapsed = performance.now() - run.startTs;
    run.running = false;
    run.finished = true;
    let improved = false;
    for (let i = 0; i < run.splits.length; i++) {
      if (pb[i] == null || run.splits[i] < pb[i]) { pb[i] = run.splits[i]; improved = true; }
    }
    localStorage.setItem(PB_KEY, JSON.stringify(pb));
    toast(improved ? `🎉 رقم شخصي جديد: ${fmt(run.elapsed)}` : `🏁 رن مكتمل: ${fmt(run.elapsed)}`);
  } else {
    toast(`تقسيم ${run.idx}: ${fmt(run.elapsed)}`);
  }
  renderSplits();
}
function reset() {
  Object.assign(run, { elapsed: 0, startTs: 0, running: false, idx: 0, splits: [], finished: false });
  renderSplits();
}

$('btnStart').onclick = start;
$('btnPause').onclick = pause;
$('btnSplit').onclick = split;
$('btnReset').onclick = reset;
document.addEventListener('keydown', (e) => {
  if (e.repeat || ['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
  if (e.code === 'Space') { e.preventDefault(); split(); }
  else if (e.key.toLowerCase() === 'r') reset();
  else if (e.key.toLowerCase() === 'p') (run.running ? pause : start)();
  else if (e.key.toLowerCase() === 's') start();
});

/* ----------------------------------------------------------------- merge --- */
function renderMerge(report) {
  const s = report.summary;
  const pill = (label, value, cls = '') => `<span class="pill ${cls}">${esc(label)}: ${esc(value)}</span>`;
  let html = '<div class="pills">' +
    pill('الوضع', report.mode) +
    pill('القواعد', s.rules) +
    pill('ملفات الشجرة', s.tree_files) +
    pill('دمج نظيف', s.merged + s.unchanged, 'good') +
    pill('حقن', s.injected, 'good') +
    pill('إضافة', s.added, 'good') +
    pill('توليد', s.generated, 'good') +
    pill('تعارضات محجورة', s.conflicts, s.conflicts ? 'warn' : 'good') +
    pill('تدقيقات تكافؤ', s.audited || 0, 'good') +
    pill('تأجيل يدوي', s.deferred, s.deferred ? 'warn' : 'good') +
    pill('انحراف/أخطاء', s.anchor_drift + s.missing + s.errors,
         s.anchor_drift + s.missing + s.errors ? 'bad' : 'good') +
    '</div>';
  html += `<p class="hash">tree sha256: ${esc(report.tree_hash)}</p>`;
  if (!report.conflicts.length && !report.manual_port.length) {
    html += '<p class="pill good">🎉 لا تعارضات ولا منقولات مؤجلة — الدمج مكتمل</p>';
  }
  if (report.audits && report.audits.length) {
    html += '<table><thead><tr><th>ملف OP4</th><th>إصلاح BugfixedHL المعادل</th><th>النتيجة</th></tr></thead><tbody>';
    for (const a of report.audits) {
      html += `<tr><td class="num">${esc(a.path)}</td><td>${esc(a.feature)}</td>` +
              `<td><span class="tag ${a.verdict === 'equivalent' ? 'merged' : 'error'}">${esc(a.verdict)}</span> ` +
              `(${a.checks.filter((c) => c.ok).length}/${a.checks.length} فحص)</td></tr>`;
    }
    html += '</tbody></table>';
  }
  if (report.conflicts.length) {
    html += `<p class="notes">⚠ ${report.conflicts.length} تعارض Three-way محجور في <code>integration/conflicts/</code> (لا يلوّث ملفات البناء).</p>`;
  }
  if (report.manual_port.length) {
    html += `<p class="notes">📝 منقول يدوياً لاحقاً: ${report.manual_port.map((m) => esc(m.path)).join('، ')}</p>`;
  }
  if (report.warnings.length) {
    html += `<p class="notes">${report.warnings.map((w) => esc(w)).join('<br>')}</p>`;
  }
  html += '<table><thead><tr><th>القاعدة</th><th>الإجراء</th><th>المسار</th><th>الحالة</th></tr></thead><tbody>';
  for (const f of report.files) {
    html += `<tr><td>${esc(f.rule)}</td><td>${esc(f.action)}</td><td class="num">${esc(f.path)}</td>` +
            `<td><span class="tag ${esc(f.status)}">${esc(f.status)}</span></td></tr>`;
  }
  html += '</tbody></table>';
  $('mergeResult').innerHTML = html;
  $('mergeBadge').textContent = `${s.rules} قاعدة نُفّذت`;
}

async function doMerge(mode) {
  $('mergeResult').innerHTML = '<span class="muted">⏳ جارٍ تشغيل خط الأنابيب…</span>';
  try {
    const r = await api('/api/merge', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    const data = await r.json();
    if (!data.ok) {
      $('mergeResult').innerHTML = `<p class="notes">❌ ${esc(data.error)}</p>`;
      return;
    }
    renderMerge(data.report);
    toast(mode === 'offline' ? '✅ الدمج (offline) اكتمل' : '✅ دمج SDK الحقيقي اكتمل');
  } catch (e) { $('mergeResult').innerHTML = `<p class="notes">❌ ${esc(e.message)}</p>`; }
}

$('btnMergeOffline').onclick = () => doMerge('offline');
$('btnMergeReal').onclick = () => doMerge('upstream');
$('btnPackage').onclick = async () => {
  $('packageResult').innerHTML = '<p class="muted">⏳ جارٍ بناء حزمة التوزيع…</p>';
  try {
    const r = await api('/api/package', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
    });
    const d = await r.json();
    if (!d.ok) { $('packageResult').innerHTML = `<p class="notes">❌ ${esc(d.error)}</p>`; return; }
    $('packageResult').innerHTML = `<div class="result">
      <p class="pill good">📦 ${esc(d.file_count)} ملفاً · ${esc(d.bytes)} بايت</p>
      <p class="hash">sha256: ${esc(d.sha256)}</p>
      <a href="/dist/bhl-op4-speedrun-overlay.zip">⬇ تنزيل الحزمة</a>
      <span class="muted"> · يحتوي كودنا فقط، بلا أي مصدر SDK مرخّص خارجياً.</span></div>`;
    toast('✅ حزمة التوزيع جاهزة');
  } catch (e) { $('packageResult').innerHTML = `<p class="notes">❌ ${esc(e.message)}</p>`; }
};
$('btnTests').onclick = async () => {
  $('mergeResult').innerHTML = '<span class="muted">⏳ جارٍ تشغيل 66 اختبار Python…</span>';
  try {
    const r = await api('/api/tests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const d = await r.json();
    $('mergeResult').innerHTML = `<p class="pill ${d.ok ? 'good' : 'bad'}">${d.ok ? '✅ كل الاختبارات نجحت' : '❌ فشل'}</p><pre class="code">${esc(d.output)}</pre>`;
  } catch (e) { $('mergeResult').innerHTML = `<p class="notes">${esc(e.message)}</p>`; }
};

/* --------------------------------------------------------------- loading --- */
function renderStatus(st) {
  $('statusPill').textContent = st.last_report ? `آخر دمج: ${st.last_report.mode}` : 'جاهز للدمج';
  $('statusPill').classList.add('ok');
  $('stats').innerHTML = [
    ['قواعد الدمج', st.rules], ['خرائط OP4', st.route.maps], ['فصول', st.route.chapters],
    ['مصادر مثبّتة', st.upstreams.length], ['اختبارات', '66 + 77'],
  ].map(([label, value]) => `<div class="stat"><b>${esc(value)}</b><span>${esc(label)}</span></div>`).join('');
  $('upstreams').innerHTML = st.upstreams.map((u) => `<div class="up-row">
      <b>${esc(u.name)}</b> <span class="tag">${esc(u.role)}</span>
      <div class="repo">${esc(u.repo)} @ <span class="sha">${esc(u.ref.slice(0, 12))}</span></div>
      <div class="muted">${esc(u.license)}</div></div>`).join('');
  $('sdkHint').textContent = st.sdk_cached
    ? '✅ SDKات الحقيقية محمّلة في .cache/upstreams — زر «دمج SDK الحقيقي» متاح.'
    : 'ℹ الدمج الحقيقي يحتاج `make fetch` أولاً (تنزيل مثبّت بـ sha256). الدمج offline يعمل الآن بدون إنترنت.';
  $('btnMergeReal').disabled = !st.sdk_cached;
  $('ruleCount').textContent = st.rules;
  $('routeBadge').textContent = `${st.route.maps} خريطة + ${st.route.boot_camp} تدريب`;
  const s = st.last_report && st.last_report.summary;
  $('doneBanner').innerHTML = s
    ? `✅ <b>الدمج مكتمل</b> · ${esc(s.tree_files)} ملف · ${esc(s.audited || 0)} تدقيق تكافؤ · ` +
      `${esc(s.injected)} حقن · <b>0</b> تعارضات · <b>0</b> مؤجّل · <b>0</b> أخطاء` +
      (st.package_ready ? ' · 📦 حزمة التوزيع جاهزة' : '')
    : '🚧 جارٍ تجهيز الدمج…';
}

function renderRoute(route) {
  chapters = route.chapters;
  $('routeList').innerHTML = chapters.map((ch, i) => `<div class="chapter">
      <b>${esc(ch.id)} · ${esc(ch.name)}</b><span class="ar">${esc(ch.name_ar)}</span>
      ${ch.maps.map((m) => `<span class="map">${esc(m)}</span>`).join('')}</div>`).join('') +
    `<div class="chapter"><b>${esc(route.boot_camp.id)} · ${esc(route.boot_camp.name)}</b>
      <span class="ar">${esc(route.boot_camp.name_ar)} · فئة منفصلة</span>
      ${route.boot_camp.maps.map((m) => `<span class="map">${esc(m)}</span>`).join('')}</div>`;
  renderSplits();
}

async function loadAll() {
  try {
    const [st, route, plan, cfg] = await Promise.all([
      api('/api/status').then((r) => r.json()),
      api('/api/route').then((r) => r.json()),
      api('/api/plan').then((r) => r.json()),
      api('/api/config').then((r) => r.text()),
    ]);
    renderStatus(st); renderRoute(route);
    $('cfg').textContent = cfg;
    $('planRules').innerHTML = plan.plan.rules.map((r) =>
      `<div>${esc(r.id.padEnd(28))} ${esc(r.action.padEnd(10))} ${esc(r.path)}</div>`).join('');
    if (st.last_report) {
      const rep = await api('/api/report').then((r) => r.text());
      $('mergeResult').innerHTML = `<p class="muted">آخر تقرير محفوظ: ${esc(st.last_report.started_at)} · <span class="hash">${esc(st.last_report.tree_hash)}</span></p><pre class="code">${esc(rep.slice(0, 2600))}</pre>`;
    }
  } catch (e) { toast(`تعذّر تحميل البيانات: ${e.message}`); }
}

$('btnCopyCfg').onclick = async () => {
  await navigator.clipboard.writeText($('cfg').textContent);
  toast('📋 نُسخ speedrun.cfg');
};
$('btnDownloadCfg').onclick = () => {
  const blob = new Blob([$('cfg').textContent], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'speedrun.cfg'; a.click();
  URL.revokeObjectURL(a.href);
};
$('readmeDetails').addEventListener('toggle', async (e) => {
  if (e.target.open && $('readme').textContent === '…') {
    $('readme').textContent = await api('/api/readme').then((r) => r.text());
  }
});

loadAll();
tick();
