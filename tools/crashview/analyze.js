// Stack walking for the Lambda-fix crash viewer.
//
// A minidump from a GoldSrc game has no frame pointers we can trust and often
// has no thread context stream at all, so this does the honest thing: it scans
// both stacks for values that land inside a loaded module and reports them as
// candidate frames, clearly labelled. It never invents a symbol name.

// A stack holds plenty of dwords that happen to look like code addresses. What
// matters is keeping the ones near the fault, so the limit is generous and the
// crash address itself is always included.
const MAX_FRAMES_PER_THREAD = 80;

export function moduleFor(modules, address) {
  // Modules are few (a few hundred at most); a linear scan is faster to read
  // than an interval tree and plenty fast here.
  for (const m of modules) {
    if (address >= m.base && address < m.base + m.size) {
      return { module: m, offset: address - m.base };
    }
  }
  return null;
}

function baseName(path) {
  const parts = String(path || '').split(/[\\/]/);
  return parts[parts.length - 1] || '(unnamed)';
}

// Collect every dword in a stack range that resolves inside a loaded module.
// Consecutive hits inside the same module are collapsed so the raw dword soup
// becomes readable. This is a scan, not an unwind: the caller decides which
// part of it to show.
export function scanStack(dump, thread, crashAddress) {
  const { stack } = thread;
  if (!stack || stack.size === 0) return { all: [], scanned: 0 };

  const view = dump.readRange(stack.start, stack.size);
  if (!view) return { all: [], scanned: 0 };

  const all = [];
  let previous = null;
  for (let off = 0; off + 4 <= stack.size; off += 4) {
    const value = view.getUint32(off, true);
    const hit = moduleFor(dump.modules, value);
    if (!hit) continue;

    const key = `${hit.module.base}:${Math.floor(hit.offset / 8)}`;
    if (previous === key) continue;
    previous = key;

    all.push({
      stackOffset: off,
      address: value,
      module: baseName(hit.module.name),
      modulePath: hit.module.name,
      offset: hit.offset,
      isCrashSite: crashAddress !== undefined && value === (crashAddress >>> 0),
    });
  }
  return { all, scanned: stack.size };
}

// Keep the part of the scan that matters: from just before the faulting frame
// down to where the engine's own frames run out. Reporting the first eighty
// dwords would show logger and dbghelp frames far away from the crash.
export function windowFrames(all, crashAddress) {
  if (all.length === 0) return { frames: [], truncatedHead: 0, truncatedTail: 0 };

  let anchor = all.findIndex((f) => f.isCrashSite);
  if (anchor < 0) {
    // No exact hit: fall back to the first frame that is not a system logger.
    anchor = all.findIndex((f) => !/^(dbghelp|ntdll|kernel32|KERNELBASE)\.dll$/i.test(f.module));
    if (anchor < 0) anchor = 0;
  }

  const start = Math.max(0, anchor - 3);
  const end = Math.min(all.length, start + MAX_FRAMES_PER_THREAD);
  return {
    frames: all.slice(start, end),
    truncatedHead: start,
    truncatedTail: all.length - end,
  };
}

// Exception codes Windows uses. Only the ones a game actually hits.
const EXCEPTION_NAMES = {
  0xc0000005: 'EXCEPTION_ACCESS_VIOLATION',
  0xc000001d: 'EXCEPTION_ILLEGAL_INSTRUCTION',
  0xc0000025: 'EXCEPTION_NONCONTINUABLE_EXCEPTION',
  0xc000008c: 'EXCEPTION_ARRAY_BOUNDS_EXCEEDED',
  0xc0000094: 'EXCEPTION_INT_DIVIDE_BY_ZERO',
  0xc0000095: 'EXCEPTION_INT_OVERFLOW',
  0xc0000096: 'EXCEPTION_PRIV_INSTRUCTION',
  0xc00000fd: 'EXCEPTION_STACK_OVERFLOW',
  0xc0000409: 'EXCEPTION_STACK_BUFFER_OVERRUN',
  0x80000003: 'EXCEPTION_BREAKPOINT',
  0xe06d7363: 'C++ EXCEPTION (throw)',
};

export function exceptionName(code) {
  return EXCEPTION_NAMES[code >>> 0] || null;
}

// EXCEPTION_ACCESS_VIOLATION carries two parameters: the access type
// (0 = read, 1 = write, 8 = execute) and the address that was touched.
//
// Not every writer lays the padding out the way the SDK documents it. In the
// GoldSrc dumps seen so far the two parameters occupy dwords at +36 and +48
// rather than the documented 64-bit slots, so a naive u64 read produces a value
// like 0x400000000 that cannot be a 32-bit address. Only report an address that
// could plausibly exist in a 32-bit process, otherwise say nothing.
const PLAUSIBLE_LIMIT = 0xffffffff;

function u32At(parameters, index) {
  const value = parameters[index];
  return typeof value === 'number' ? value : null;
}

export function describeAccessViolation(parameters, rawDwords) {
  if (!parameters || parameters.length < 2) return null;

  // Prefer the raw dword view when the caller has it: that is what the file
  // literally contains.
  const operation = rawDwords ? rawDwords[0] : u32At(parameters, 0);
  const candidate = rawDwords ? rawDwords[rawDwords.length - 1] : u32At(parameters, 1);
  if (operation === null || candidate === null) return null;

  const verb = operation === 0 ? 'read' : operation === 1 ? 'write' : operation === 8 ? 'execute' : null;
  if (!verb) return { verb: null, address: null, isNull: false, operation };

  const plausible = candidate <= PLAUSIBLE_LIMIT ? candidate : null;
  return {
    verb,
    address: plausible,
    isNull: plausible === 0,
    operation,
    // A near-null target is the classic null-pointer-plus-offset crash.
    nearNull: plausible !== null && plausible < 0x10000,
  };
}

export function hex(value, pad = 8) {
  return '0x' + (value >>> 0).toString(16).padStart(pad, '0');
}

// Turn a dump into the shape the UI renders. Kept separate from the parser so
// the parse step can fail on its own without the UI showing half a report.
export function analyze(dump) {
  const ex = dump.exception;
  const crashModule = ex ? moduleFor(dump.modules, ex.exceptionAddress) : null;

  const threads = dump.threads.map((t) => {
    const crashAddr = ex ? ex.exceptionAddress : undefined;
    const scanned = scanStack(dump, t, crashAddr);
    const isCrashing = ex ? t.threadId === ex.threadId : false;
    // The crashing thread gets the window around the fault; the others only
    // need a short sample near their most recent frame.
    const windowed = windowFrames(scanned.all, isCrashing ? crashAddr : undefined);
    return {
      threadId: t.threadId,
      stackStart: t.stack.start,
      stackSize: t.stack.size,
      isCrashing,
      totalCandidates: scanned.all.length,
      frames: windowed.frames,
      truncatedHead: windowed.truncatedHead,
      truncatedTail: windowed.truncatedTail,
      scanned: scanned.scanned,
    };
  });

  // Crashing thread first, then the rest by how much they managed to resolve.
  threads.sort((a, b) => {
    if (a.isCrashing !== b.isCrashing) return a.isCrashing ? -1 : 1;
    return b.frames.length - a.frames.length;
  });

  const offending = ex ? dump.modules.find((m) => ex.exceptionAddress >= m.base && ex.exceptionAddress < m.base + m.size) : null;

  return {
    ok: true,
    system: dump.system,
    moduleCount: dump.modules.length,
    modules: dump.modules,
    exception: ex
      ? {
          threadId: ex.threadId,
          code: ex.exceptionCode,
          name: exceptionName(ex.exceptionCode),
          record: ex.exceptionAddress,
          module: offending ? baseName(offending.name) : null,
          modulePath: offending ? offending.name : null,
          offset: offending ? ex.exceptionAddress - offending.base : null,
          // dwords [0] and [14] are the two access-violation values in the
          // layout GoldSrc writes; describeAccessViolation documents why.
          access: describeAccessViolation(ex.parameters, ex.paramDwords
            ? [ex.paramDwords[0], ex.paramDwords[14]]
            : null),
        }
      : null,
    crashModule,
    threads,
    hasContext: !!(ex && ex.context && ex.context.size > 0),
  };
}
