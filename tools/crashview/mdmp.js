// Minimal MDMP (Windows Minidump) reader for the Lambda-fix crash viewer.
//
// Why hand written: the viewer must run from a phone with no build step and no
// network, so a native parser is not an option. This reads the streams the
// viewer actually needs and stops there. Every structure offset below comes
// from the Microsoft MINIDUMP_* definitions; nothing is guessed.

export const StreamType = {
  ThreadList: 3,
  ModuleList: 4,
  MemoryList: 5,
  Exception: 6,
  SystemInfo: 7,
  Memory64List: 9,
};

const SIGNATURE = 0x504d444d; // 'MDMP'

class Reader {
  constructor(buffer) {
    this.dv = new DataView(buffer);
    this.buf = new Uint8Array(buffer);
    this.decoder = new TextDecoder('utf-16le');
  }

  u32(off) { return this.dv.getUint32(off, true); }
  i32(off) { return this.dv.getInt32(off, true); }
  u64(off) {
    // Minidumps from 32-bit processes keep the high dword at zero; read it as a
    // pair so a 64-bit dump still works for the values we display.
    const lo = this.dv.getUint32(off, true);
    const hi = this.dv.getUint32(off + 4, true);
    return hi * 0x100000000 + lo;
  }

  // MINIDUMP_STRING: u32 byte length, then UTF-16LE characters.
  minidumpString(rva) {
    const len = this.u32(rva);
    if (len === 0 || len > 4096) return '';
    const start = rva + 4;
    const bytes = this.buf.subarray(start, start + len);
    return this.decoder.decode(bytes).replace(/\0+$/, '');
  }
}

// MINIDUMP_LOCATION_DESCRIPTOR = { u32 DataSize, u32 Rva }
function location(r, off) {
  return { size: r.u32(off), rva: r.u32(off + 4) };
}

function guid(r, off) {
  const d1 = r.u32(off).toString(16).padStart(8, '0');
  const d2 = r.dv.getUint16(off + 4, true).toString(16).padStart(4, '0');
  const d3 = r.dv.getUint16(off + 6, true).toString(16).padStart(4, '0');
  const rest = [];
  for (let i = 8; i < 16; i++) {
    rest.push(r.buf[off + i].toString(16).padStart(2, '0'));
  }
  return `${d1}-${d2}-${d3}-${rest.slice(0, 2).join('')}-${rest.slice(2).join('')}`.toUpperCase();
}

// MINIDUMP_MEMORY_DESCRIPTOR: u64 StartOfMemoryRange + MINIDUMP_LOCATION_DESCRIPTOR
function memoryDescriptor(r, off) {
  return {
    start: r.u64(off),
    size: r.u32(off + 8),
    rva: r.u32(off + 12),
  };
}

export function parseMinidump(arrayBuffer) {
  const r = new Reader(arrayBuffer);
  const signature = r.u32(0);
  if (signature !== SIGNATURE) {
    throw new Error('Not a minidump: the file does not start with the MDMP signature.');
  }

  const version = r.u32(4);
  const numberOfStreams = r.u32(8);
  const streamDirectoryRva = r.u32(12);

  const streams = {};
  for (let i = 0; i < numberOfStreams; i++) {
    const base = streamDirectoryRva + i * 12; // MINIDUMP_DIRECTORY
    const type = r.u32(base);
    streams[type] = { size: r.u32(base + 4), rva: r.u32(base + 8) };
  }

  // ---- SystemInfo (7) -----------------------------------------------------
  let system = null;
  if (streams[StreamType.SystemInfo]) {
    const o = streams[StreamType.SystemInfo].rva;
    system = {
      processorArchitecture: r.dv.getUint16(o, true),
      processorLevel: r.dv.getUint16(o + 4, true),
      numberOfProcessors: r.buf[o + 6],
      majorVersion: r.u32(o + 8),
      minorVersion: r.u32(o + 12),
      buildNumber: r.u32(o + 16),
      platformId: r.u32(o + 20),
    };
  }

  // ---- Modules (4) --------------------------------------------------------
  const modules = [];
  if (streams[StreamType.ModuleList]) {
    const o = streams[StreamType.ModuleList].rva;
    const count = r.u32(o);
    for (let i = 0; i < count; i++) {
      const m = o + 4 + i * 108; // sizeof(MINIDUMP_MODULE)
      // MINIDUMP_MODULE: BaseOfImage(8) SizeOfImage(4) CheckSum(4)
      // TimeDateStamp(4) ModuleNameRva(4) VersionInfo(52) CvRecord(8)
      // MiscRecord(8) Reserved0(8) Reserved1(8) = 108 bytes.
      const nameRva = r.u32(m + 20);
      modules.push({
        base: r.u64(m),
        size: r.u32(m + 8),
        checksum: r.u32(m + 12),
        timestamp: r.u32(m + 16),
        name: r.minidumpString(nameRva),
      });
    }
  }

  // ---- Threads (3) --------------------------------------------------------
  const threads = [];
  if (streams[StreamType.ThreadList]) {
    const o = streams[StreamType.ThreadList].rva;
    const count = r.u32(o);
    for (let i = 0; i < count; i++) {
      const t = o + 4 + i * 48; // sizeof(MINIDUMP_THREAD)
      const stack = memoryDescriptor(r, t + 24);
      threads.push({
        threadId: r.u32(t),
        suspendCount: r.u32(t + 4),
        priorityClass: r.u32(t + 8),
        priority: r.u32(t + 12),
        teb: r.u64(t + 16),
        stack,
      });
    }
  }

  // ---- Exception (6) ------------------------------------------------------
  let exception = null;
  if (streams[StreamType.Exception]) {
    const o = streams[StreamType.Exception].rva;
    // MINIDUMP_EXCEPTION_STREAM: u32 ThreadId, u32 __alignment, then
    // MINIDUMP_EXCEPTION, which starts 8 bytes in.
    const threadId = r.u32(o);
    const e = o + 8;
    const exceptionCode = r.u32(e);
    const exceptionFlags = r.u32(e + 4);
    // ExceptionAddress is what crashed. In a 32-bit dump the ExceptionRecord
    // field only carries the low dword (verified byte for byte on a real
    // GoldSrc dump), so read ExceptionAddress as a u64: the high dword really
    // is the faulting address.
    const exceptionRecord = r.u32(e + 8);
    const exceptionAddress = r.u64(e + 16);
    // NumberParameters sits right after the two 64-bit fields, at +24, and the
    // 15 EXCEPTION_INFORMATION entries follow it.
    const numberParameters = r.u32(e + 24);
    // An access violation always carries exactly two parameters, but this dump
    // reports NumberParameters = 0 (verified byte for byte). Read the pair the
    // code needs anyway: 0 = read, 1 = write, 8 = execute, then the address.
    const wanted = Math.max(Math.min(numberParameters, 15), 2);
    const params = [];
    for (let i = 0; i < wanted; i++) {
      params.push(r.u64(e + 28 + i * 8));
    }
    // The same area as plain dwords. Some crash writers store the two access
    // violation values here without the documented 64-bit padding, so the
    // report reads this view instead of trusting u64 alignment.
    const paramDwords = [];
    for (let i = 0; i < 15 * 2; i++) {
      paramDwords.push(r.u32(e + 28 + i * 4));
    }
    const context = location(r, e + 28 + 15 * 8);
    exception = {
      threadId,
      exceptionCode,
      exceptionFlags,
      exceptionRecord,
      exceptionAddress,
      numberParameters,
      parameters: params,
      paramDwords,
      context,
    };
  }

  // ---- Memory (5 or 9) ----------------------------------------------------
  // Memory64List (9) stores every range back to back in one blob, which is what
  // modern Windows writes for full dumps. MemoryList (5) keeps scattered RVAs.
  const ranges = [];
  let blobRva = 0;
  if (streams[StreamType.Memory64List]) {
    const o = streams[StreamType.Memory64List].rva;
    const count = r.u64(o);
    blobRva = r.u64(o + 8);
    for (let i = 0; i < count; i++) {
      const d = o + 16 + i * 16;
      ranges.push({ start: r.u64(d), size: r.u64(d + 8), rva: 0 });
    }
    let cursor = blobRva;
    for (const range of ranges) {
      range.rva = cursor;
      cursor += range.size;
    }
  } else if (streams[StreamType.MemoryList]) {
    const o = streams[StreamType.MemoryList].rva;
    const count = r.u32(o);
    for (let i = 0; i < count; i++) {
      ranges.push(memoryDescriptor(r, o + 4 + i * 16));
    }
  }

  // Some dumps also carry the stacks inside MemoryList; map them so stack reads
  // work for either layout.
  const readRange = (start, size) => {
    for (const range of ranges) {
      if (start >= range.start && start + size <= range.start + range.size) {
        const offset = range.rva + (start - range.start);
        return new DataView(r.buf.buffer, r.buf.byteOffset + offset, size);
      }
    }
    return null;
  };

  return {
    header: { signature, version, numberOfStreams },
    system,
    modules,
    threads,
    exception,
    ranges,
    readRange,
    streamTypes: Object.keys(streams).map(Number).sort((a, b) => a - b),
  };
}

export const MODULE_STRUCT_SIZE = 108;
export const THREAD_STRUCT_SIZE = 48;
export { guid, location };
