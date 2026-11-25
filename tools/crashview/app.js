import { parseMinidump } from './mdmp.js';
import { analyze, hex } from './analyze.js';

const $ = (id) => document.getElementById(id);
const fileInput = $('file');
const statusEl = $('status');
const reportEl = $('report');

const ARCH = {
  0: 'x86 (32-bit)',
  5: 'ARM',
  6: 'IA64',
  9: 'x64',
  12: 'ARM64',
};

const PLATFORM = {
  1: 'Windows 95/98/ME',
  2: 'Windows NT/2000/XP/7/10',
};

function setStatus(text, kind) {
  statusEl.hidden = !text;
  statusEl.textContent = text || '';
  statusEl.className = `status ${kind || ''}`;
}

function row(dl, term, value) {
  const dt = document.createElement('dt');
  dt.textContent = term;
  const dd = document.createElement('dd');
  if (value instanceof Node) dd.appendChild(value);
  else dd.textContent = value;
  dl.append(dt, dd);
}

function frameRow(frame, isTop) {
  const li = document.createElement('li');
  if (isTop) li.className = 'top';
  if (frame.isCrashSite) li.className = 'top';
  const where = document.createElement('span');
  where.className = 'where';
  where.textContent = frame.module;
  const off = document.createElement('span');
  off.className = 'off';
  off.textContent = `+${hex(frame.offset).slice(2)}`;
  li.append(where, off);
  return li;
}

function render(result, fileName) {
  // ---- summary -----------------------------------------------------------
  const summary = $('summary');
  summary.replaceChildren();
  const verdict = document.createElement('p');
  verdict.className = 'verdict';

  if (result.exception) {
    const ex = result.exception;
    const where = ex.module ? `${ex.module} + ${hex(ex.offset).slice(2)}` : 'an unknown module';
    const what = ex.name || `Exception ${hex(ex.code)}`;
    if (ex.access && ex.access.verb && ex.access.address !== null) {
      const target = ex.access.isNull
        ? 'address 0x00000000'
        : ex.access.nearNull
          ? `a near-null address (${hex(ex.access.address)})`
          : hex(ex.access.address);
      verdict.innerHTML =
        `<strong>${what}</strong> while trying to <strong>${ex.access.verb}</strong> ${target}, inside <strong>${where}</strong>.`;
    } else if (ex.access && ex.access.verb) {
      verdict.innerHTML = `<strong>${what}</strong> during a <strong>${ex.access.verb}</strong>, inside <strong>${where}</strong>.`;
    } else {
      verdict.innerHTML = `<strong>${what}</strong> inside <strong>${where}</strong>.`;
    }
  } else {
    verdict.textContent = 'This dump has no exception record, so it does not describe a crash.';
  }
  summary.appendChild(verdict);

  // ---- facts -------------------------------------------------------------
  const facts = $('facts');
  facts.replaceChildren();
  row(facts, 'File', fileName);
  if (result.system) {
    const s = result.system;
    row(facts, 'Architecture', ARCH[s.processorArchitecture] || `type ${s.processorArchitecture}`);
    row(facts, 'Platform', PLATFORM[s.platformId] || `id ${s.platformId}`);
    row(facts, 'OS build', `${s.majorVersion}.${s.minorVersion}.${s.buildNumber}`);
    row(facts, 'Processors', String(s.numberOfProcessors));
  }
  row(facts, 'Modules loaded', String(result.moduleCount));
  if (result.exception) {
    row(facts, 'Exception code', hex(result.exception.code));
    row(facts, 'Faulting thread', String(result.exception.threadId));
  }
  row(facts, 'Thread context saved', result.hasContext ? 'yes' : 'no — native symbol names are not recoverable from this file');
  if (result.crashModule) {
    row(facts, 'Faulting module', `${result.crashModule.module} at ${hex(result.crashModule.address)}`);
  }

  // ---- crashing thread ---------------------------------------------------
  const crashing = result.threads.find((t) => t.isCrashing) || result.threads[0];
  const framesEl = $('crash-frames');
  framesEl.replaceChildren();
  const walknote = $('walknote');

  if (crashing && crashing.frames.length) {
    const hidden = [];
    if (crashing.truncatedHead) hidden.push(`${crashing.truncatedHead} before`);
    if (crashing.truncatedTail) hidden.push(`${crashing.truncatedTail} after`);
    walknote.textContent =
      `Candidate frames from the faulting position, most recent first (${crashing.totalCandidates} values on this stack resolve inside a module` +
      (hidden.length ? `; ${hidden.join(' and ')} are not shown` : '') +
      '). They are candidates, not a reconstructed call stack — this dump carries no usable thread context, so no symbol names can be recovered.';

    crashing.frames.forEach((f) => {
      const li = frameRow(f, f.isCrashSite);
      if (f.isCrashSite) {
        li.style.background = '#2a1a1a';
        const badge = document.createElement('span');
        badge.className = 'badge bad';
        badge.textContent = 'FAULT';
        li.querySelector('.where').prepend(badge, document.createTextNode(' '));
      }
      framesEl.appendChild(li);
    });
  } else {
    walknote.textContent = 'No stack values resolving inside a module were found for this thread.';
  }

  // ---- other threads -----------------------------------------------------
  const threadsEl = $('threads');
  threadsEl.replaceChildren();
  const others = result.threads.filter((t) => t !== crashing);
  if (!others.length) {
    threadsEl.textContent = 'No other threads.';
  } else {
    for (const t of others) {
      const h = document.createElement('h3');
      h.textContent = `Thread ${t.threadId} — ${t.frames.length} frame candidate(s)`;
      const ol = document.createElement('ol');
      ol.className = 'frames';
      t.frames.slice(0, 12).forEach((f, i) => ol.appendChild(frameRow(f, i === 0)));
      threadsEl.append(h, ol);
    }
  }

  // ---- modules -----------------------------------------------------------
  const modsEl = $('modules');
  modsEl.replaceChildren();
  const sorted = [...result.modules].sort((a, b) => a.base - b.base);
  for (const m of sorted) {
    const li = document.createElement('li');
    const addr = document.createElement('span');
    addr.className = 'addr';
    addr.textContent = hex(m.base).slice(2);
    const name = document.createElement('span');
    name.textContent = m.name.split(/[\\/]/).pop();
    li.append(addr, name);
    modsEl.appendChild(li);
  }

  reportEl.hidden = false;
}

async function handleFile(file) {
  setStatus('Reading the dump…', 'busy');
  reportEl.hidden = true;
  try {
    const buffer = await file.arrayBuffer();
    const dump = parseMinidump(buffer);
    const result = analyze(dump);
    setStatus('', '');
    render(result, file.name);
  } catch (err) {
    console.error(err);
    setStatus(err && err.message ? err.message : String(err), 'error');
  }
}

fileInput.addEventListener('change', () => {
  const file = fileInput.files && fileInput.files[0];
  if (file) handleFile(file);
});

// Drag and drop, for when the page is opened on a desktop.
const drop = $('drop');
for (const type of ['dragenter', 'dragover']) {
  drop.addEventListener(type, (e) => {
    e.preventDefault();
    drop.querySelector('.pick').style.borderColor = 'var(--accent)';
  });
}
for (const type of ['dragleave', 'drop']) {
  drop.addEventListener(type, () => {
    drop.querySelector('.pick').style.borderColor = '';
  });
}
drop.addEventListener('drop', (e) => {
  e.preventDefault();
  const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// Offline: cache the shell so the app opens without a connection.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').catch(() => {
      // Opening straight from the filesystem has no service worker; the app
      // still works, it just is not installable there.
    });
  });
}
