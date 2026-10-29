[简体中文](README.md) | **English**

# OnePlus-OKI-Builder

Build OnePlus / OPPO / realme OKI kernels online with GitHub Actions: official OnePlus kernel sources with SukiSU Ultra, SUSFS and KPM, packaged as AnyKernel3 zips. No local build environment needed.

## Features

- Sources pulled from OnePlus' official `kernel_manifest`
- SukiSU Ultra + SUSFS, with KPM / KPN
- Optional: BBG partition write protection, Unicode bypass fix, Re-Kernel, DroidSpaces, ZRAM (LZ4KD etc.)
- Auto-fixes a known source bug: on sm8650 Android 16 sources, a duplicate `test_task_ux` export makes the device bootloop
- Upstream fixes for known 6.1 security bugs (CVE-2026-43284, 43499, 64560, 98260) are applied automatically and skipped if the source already has them, see [patches/security](patches/security)
- The source kernel version is shown at the top of the run page
- Fast build with ccache

## Usage

1. Fork this repository
2. **Actions → Build All OnePlus Kernels → Run workflow**
3. Pick the device and options
4. Download `AnyKernel3_*.zip` from the run's Artifacts

See [FILE.md](FILE.md) for device codes. Suffixes `_b` / `_v` / `_u` mean Android 16 / 15 / 14.

## Before flashing

> [!CAUTION]
> A wrong kernel will not boot. Keep a stock `boot.img` backup and know how to restore it.

1. The kernel version shown on the run page must match your device (Settings → About → Kernel version).
2. Recommended: run [`tools/kernel_compat_check.py`](tools/kernel_compat_check.py) against your stock kernel and vendor modules. Any first-stage (vendor_boot) difference means a bootloop.
3. Remove Magisk first.
4. If ZRAM is enabled, install the ZRAM module before rebooting.

## Issues

Please report problems in this repository's [issues](../../issues) with the run link, device and OS version.

## Credits

- Build workflow modified from [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build) by Numbersf, under its [LICENSE](LICENSE)
- [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra), [susfs4ksu](https://gitlab.com/simonpunk/susfs4ksu), [AnyKernel3](https://github.com/osm0sis/AnyKernel3), [Baseband-guard](https://github.com/vc-teahouse/Baseband-guard), [Re-Kernel](https://github.com/Sakion-Team/Re-Kernel) and others

## Disclaimer

Provided as is. Flashing third-party kernels is at your own risk.
