**简体中文** | [English](README-en.md)

# 一加构建（OnePlus-OKI-Builder）

在 GitHub Actions 上在线编译一加 / 欧加真机型的 OKI 内核：基于一加官方开源内核源码，集成 SukiSU Ultra、SUSFS 和 KPM，输出 AnyKernel3 刷机包。不需要本地编译环境。

## 特性

- 按一加官方 `kernel_manifest` 拉取源码，机型下拉框附中文机型名
- SukiSU Ultra + SUSFS，内核模块方案可选 KPM / KPN
- 可选功能：BBG 关键分区写入保护、Unicode 绕过修复、ZRAM（LZ4KD 等）
- 自动修复已知源码问题：sm8650 Android 16 源码重复导出 `test_task_ux`，导致刷入后开机即崩
- 6.1 内核自动打上已知安全漏洞的上游修复（CVE-2026-43284、43499、64560、98260），源码已修复的会自动跳过，见 [patches/security](patches/security)
- 构建页面顶部直接显示源码内核版本
- 设备还没升级到最新系统时，自动改用一加源码历史里内核版本相同的那个系统版本的源码（可填「系统版本」挑最接近的一次）
- 极速构建 + ccache 缓存，二次构建通常 10～20 分钟

## 使用

1. Fork 本仓库
2. 进入 **Actions → Build All OnePlus Kernels → Run workflow**
3. 选择机型和功能选项，开始构建
4. 完成后在运行页面底部的 Artifacts 下载 `AnyKernel3_*.zip`

机型代号和对应的安卓版本见 [FILE.md](FILE.md)。代号末尾的 `_b` / `_v` / `_u` 分别对应 Android 16 / 15 / 14。

## 刷入前必读

> [!CAUTION]
> 刷错内核会导致无法开机。刷入前请确认手里有原厂 `boot.img` 备份，并知道如何恢复。

1. **核对内核版本**：构建页面顶部会提示本次源码的内核版本（如 `6.1.141`），必须与设备「设置 → 关于本机 → 版本信息 → 内核版本」一致。系统更新后内核版本可能变化，需重新核对。设备系统比一加最新源码旧、内核版本对不上时，构建会自动从源码历史里找内核版本相同的系统版本；建议同时填「系统版本」（版本信息 → 版本号里的数字，如 `16.0.2.402`），会选不早于它的最近一次。
2. **建议离线检查模块兼容性**：[`tools/kernel_compat_check.py`](tools/kernel_compat_check.py) 会用设备原厂内核和全部厂商模块做对照，检查新内核是否缺符号、CRC 不符或重复导出。第一阶段（vendor_boot）出现任何差异都会导致开机即崩，结果为 0 再刷。
3. **卸载 Magisk**：设备上有 Magisk 或其残留时刷入可能变砖，刷机脚本检测到会提示。
4. 开启 ZRAM 的，请在刷入后、重启前先安装 ZRAM 模块。

## 问题反馈

本仓库的问题请在本仓库提 [issue](../../issues)，附上构建运行链接和机型、系统版本。

## 致谢

- 构建流程基于 [Numbersf/Action-Build](https://github.com/Numbersf/Action-Build) 修改，原作者 Numbersf，遵循其 [LICENSE](LICENSE)
- [SukiSU-Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)、[susfs4ksu](https://gitlab.com/simonpunk/susfs4ksu)、[AnyKernel3](https://github.com/osm0sis/AnyKernel3)、[Baseband-guard](https://github.com/vc-teahouse/Baseband-guard) 等项目

## 免责声明

本项目按原样提供。刷入第三方内核有风险，造成的任何后果由使用者自行承担。
