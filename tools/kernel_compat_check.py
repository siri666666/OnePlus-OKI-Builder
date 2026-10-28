"""Offline check: can a self-built kernel Image load the device's vendor modules?

Usage: python -X utf8 kernel_compat_check.py <new Image> <stock Image> <first_stage dir> <vendor_dlkm dir>
  first_stage dir: lib/modules extracted from the vendor_boot ramdisk (must contain modules.load)
  vendor_dlkm dir: the device's /vendor_dlkm/lib/modules
  stock Image: kernel from the OTA boot.img (used as the baseline; it should show zero diffs)

For every module it checks missing symbols, __versions CRC vs the kernel's __kcrctab, and
symbols exported by both the kernel and a module. First-stage failures are fatal (init aborts).

离线检查自编内核 Image 能否加载设备上的厂商模块；参数同上，第一阶段"相对原厂新增"全为 0 才可刷入。
"""
import array, collections, glob, os, re, struct, sys

IDENT = re.compile(rb"[A-Za-z_][A-Za-z0-9_.$]{0,200}")


def ko_info(path):
    d = open(path, "rb").read()
    shoff, = struct.unpack_from("<Q", d, 0x28)
    es, num, stx = struct.unpack_from("<HHH", d, 0x3A)
    secs = [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * es) for i in range(num)]
    nb = d[secs[stx][4]:secs[stx][4] + secs[stx][5]]
    sec = {nb[s[0]:nb.index(b"\0", s[0])].decode(): s for s in secs}
    und, exp, ver = set(), set(), {}
    st, ss = sec.get(".symtab"), sec.get(".strtab")
    if st:
        sb = d[ss[4]:ss[4] + ss[5]]
        for o in range(st[4], st[4] + st[5], 24):
            nm, _, _, shn = struct.unpack_from("<IBBH", d, o)
            if shn == 0 and nm:
                und.add(sb[nm:sb.index(b"\0", nm)].decode())
    ks = sec.get("__ksymtab_strings")
    if ks:
        exp = {x.decode() for x in d[ks[4]:ks[4] + ks[5]].split(b"\0") if x}
    v = sec.get("__versions")
    if v:
        for o in range(v[4], v[4] + v[5], 64):
            crc, = struct.unpack_from("<Q", d, o)
            ver[d[o + 8:o + 64].split(b"\0")[0].decode()] = crc & 0xFFFFFFFF
    return und, exp, ver


def ksymtab(d):
    n = len(d) // 4
    v = array.array("i", d[:n * 4])

    def name_at(t):
        if 0 < t < len(d) and d[t - 1] == 0:
            m = IDENT.match(d, t)
            if m and m.end() < len(d) and d[m.end()] == 0:
                return m.group().decode()
        return None

    hits = {i for i in range(n - 3) if 0 < i * 4 + 4 + v[i + 1] < len(d) and d[i * 4 + 4 + v[i + 1] - 1] == 0}
    best = None
    for i in sorted(hits):
        if i - 3 in hits:
            continue
        j = i
        while j + 3 in hits:
            j += 3
        cnt = (j - i) // 3 + 1
        if cnt < 200 or (best and cnt <= best[1]):
            continue
        names = [name_at(i * 4 + k * 12 + 4 + v[i + k * 3 + 1]) for k in range(cnt)]
        if sum(x is not None for x in names) > cnt * 0.98:
            best = (i, cnt, names)
    return best[2]


def kernel_exports(path, expected):
    d = open(path, "rb").read()
    names = ksymtab(d)
    idx = {s: i for i, s in enumerate(names) if s}
    votes = collections.Counter()
    for k, (s, c) in enumerate(expected.items()):
        if k > 3000:
            break
        if s in idx:
            pat = struct.pack("<I", c)
            p = d.find(pat)
            while p >= 0:
                votes[p - 4 * idx[s]] += 1
                p = d.find(pat, p + 1)
    base, cnt = votes.most_common(1)[0]
    crcs = array.array("I", d[base:base + 4 * len(names)])
    return {s: c for s, c in zip(names, crcs) if s}, set(d.split(b"\0")), cnt


def check(image, stage_mods, all_mod_exports, kexp, tokens):
    missing, crc_bad, dup = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for m, (und, exp, ver) in stage_mods.items():
        for s in exp & set(kexp):
            dup[m].append(s)
        for s in und:
            if s in kexp:
                if s in ver and ver[s] != kexp[s]:
                    crc_bad[m].append(s)
            elif s not in all_mod_exports and s.encode() not in tokens:
                missing[m].append(s)
    return missing, crc_bad, dup


def main():
    new_img, stock_img, fs_dir, dlkm_dir = sys.argv[1:5]
    first = [l.strip() for l in open(os.path.join(fs_dir, "modules.load")) if l.strip()]
    fs_all = {os.path.basename(p): ko_info(p) for p in glob.glob(os.path.join(fs_dir, "*.ko"))}
    dlkm = {os.path.basename(p): ko_info(p) for p in glob.glob(os.path.join(dlkm_dir, "*.ko"))}
    stages = {"第一阶段(致命)": {m: fs_all[m] for m in first if m in fs_all}, "第二阶段": dlkm}
    all_exports = set().union(*(e for _, e, _ in list(fs_all.values()) + list(dlkm.values())))
    expected = {}
    for _, _, ver in list(fs_all.values()) + list(dlkm.values()):
        expected.update(ver)
    baseline = None
    for label, img in (("原厂", stock_img), ("新内核", new_img)):
        kexp, tokens, votes = kernel_exports(img, expected)
        print(f"== {label} {img}: 导出 {len(kexp)} 个符号, CRC 定位票数 {votes}")
        result = {}
        for stage, mods in stages.items():
            r = check(img, mods, all_exports, kexp, tokens)
            result[stage] = r
            for title, data in zip(("缺符号", "CRC 不符", "重复导出"), r):
                items = {m: s for m, s in data.items() if s}
                if baseline is not None:
                    base = baseline[stage][("缺符号", "CRC 不符", "重复导出").index(title)]
                    items = {m: [x for x in s if x not in base.get(m, [])] for m, s in items.items()}
                    items = {m: s for m, s in items.items() if s}
                tag = "（相对原厂新增）" if baseline is not None else ""
                print(f"   {stage} {title}{tag}: {sum(map(len, items.values()))} 处 / {len(items)} 个模块")
                for m, s in sorted(items.items(), key=lambda x: -len(x[1]))[:8]:
                    print(f"      {m}: {', '.join(sorted(s)[:6])}")
        if baseline is None:
            baseline = result


if __name__ == "__main__":
    main()
