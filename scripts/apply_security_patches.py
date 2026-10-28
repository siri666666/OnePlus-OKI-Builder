"""在内核源码根目录运行：python3 apply_security_patches.py <patches/security 目录>

对每个适用于当前内核版本的补丁判断状态：
  能正向打上 -> 打上并核对修复特征；能反向应用 -> 源码已包含；
  修复特征都在且漏洞特征都不在 -> 源码已用其他方式修复；其余 -> 报错退出。
"""
import json
import os
import re
import subprocess
import sys


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return None


def all_present(markers):
    return bool(markers) and all((read(f) or "").count(t) > 0 for f, t in markers)


def any_present(markers):
    return any((read(f) or "").count(t) > 0 for f, t in markers)


def git_apply(*args):
    return subprocess.run(["git", "apply", *args], capture_output=True, text=True)


def main():
    patch_dir = os.path.abspath(sys.argv[1])
    makefile = read("Makefile") or ""
    ver = re.search(r"^VERSION = (\d+)", makefile, re.M)
    pl = re.search(r"^PATCHLEVEL = (\d+)", makefile, re.M)
    kernel = f"{ver.group(1)}.{pl.group(1)}" if ver and pl else "?"
    with open(os.path.join(patch_dir, "series.json"), encoding="utf-8") as f:
        series = [e for e in json.load(f) if e["kernel"] == kernel]
    if not series:
        print(f"::notice title=Security Fixes::内核 {kernel} 暂无安全补丁，跳过")
        return 0

    rows, failed = [], []
    for e in series:
        path = os.path.join(patch_dir, e["patch"])
        if git_apply("--check", path).returncode == 0:
            r = git_apply(path)
            if r.returncode == 0 and all_present(e["fixed"]) and not any_present(e["vulnerable"]):
                status = "本次打上"
            else:
                status = "打上后核对失败"
                failed.append(e)
        elif git_apply("--check", "-R", path).returncode == 0:
            status = "源码已包含"
        elif all_present(e["fixed"]) and not any_present(e["vulnerable"]):
            status = "源码已用其他方式修复"
        else:
            status = "无法打上"
            failed.append(e)
        rows.append((e["cve"], e["patch"], status))
        print(f"{e['cve']:16s} {status:12s} {e['patch']}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("### 安全补丁 / Security fixes\n\n| CVE | 状态 | 补丁 |\n|---|---|---|\n")
            for cve, patch, status in rows:
                f.write(f"| {cve} | {status} | `{patch}` |\n")
            f.write("\n")

    if failed:
        names = ", ".join(e["patch"] for e in failed)
        print(f"::error title=Security Fixes::以下补丁无法确认已修复：{names}。可关闭 SECURITY_FIXES 选项后重试，并反馈此问题")
        return 1
    done = sum(1 for r in rows if r[2] == "本次打上")
    print(f"::notice title=Security Fixes::内核 {kernel}：{len(rows)} 个安全补丁，本次打上 {done} 个，其余源码已包含")
    return 0


if __name__ == "__main__":
    sys.exit(main())
