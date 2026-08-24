# Nirvana30 Reverse Reconstruction

从 `Nirvana30`（Enigma Protector + **Nuitka** 客户端 + 游戏内 AutoPlayer 插件）逆向得到的重建工程。

## 目录

```text
addon/AutoPlayer/     # 从官方更新源下载的 retail.zip 游戏内插件（Lua 为 VM 混淆）
client/               # 由运行时元数据重建的 Python API 骨架（无函数体）
clean_client/         # 干净重写的协议驱动客户端（进行中，已有测试）
docs/                 # 逆向笔记 / 设计 / 实现计划
scripts/              # 脱壳/注入/生成骨架脚本
_analysis/            # 原始分析产物（常量、签名、内存 dump、远程包）
```

## 架构结论

1. **外置客户端 `Nirvana.exe`**
   - Enigma Protector 加壳
   - 业务逻辑为 **Nuitka** 编译模块（`nuitka_module_loader`）
   - UI: PySide6 + qfluentwidgets（`FluentPrototypeWindow`）
   - 采集: `dxcam` / `mss` / `PrintWindow`
   - 输入: `SendInput` / `keybd_event`
   - 更新源: `http://36.138.222.171:3000`

2. **游戏内插件**
   - 包名实际是更新通道里的 `retail.zip`（不是 `Nirvana.zip`；`Nirvana.zip` 通道返回的是客户端本体）
   - TOC Title: AutoPlayer，`## Interface: 120000+`
   - Lua 主体为 VM/字符串表混淆（非简单 Base64）

## 已恢复内容

| 内容 | 位置 | 完整度 |
| --- | --- | --- |
| 插件目录与 TOC/资源 | `addon/AutoPlayer/` | 文件完整，Lua 仍混淆 |
| 模块常量/枚举/URL | `client/*.py`、`_analysis/recovered/constants.json` | 高 |
| 函数形参/局部名（co_varnames） | `client/` stubs、`signature_index.json` | 中高 |
| Nuitka 函数体 | — | **不可恢复**（native） |
| Lua 明文逻辑 | — | 需单独 Lua VM 脱壳 |

## 关键模块

- `fluent_ui.prototype_window`：主窗口、登录、循环选择、热键、自动更新
- `fluent_ui.fluent_windows`：条件编辑器/在线循环对话框
- `window_capture`：三种截屏方式
- `skill_conditions` / `skill_cycle_config`：技能条件与循环配置
- `addon_update` / `update_checker`：插件与客户端更新

## 重要说明

- `client/` 下是 **API 重建骨架**，直接运行会 `NotImplementedError`。
- 原崩溃点 `_do_quit_for_update` 实际在 `BackgroundSettingsPage`，不在 `FluentPrototypeWindow`。
- Defender 可能将 `Nirvana.exe` 报为 `Trojan:Win32/Wacatac.B!ml`（Enigma 启发式常见）。

## clean_client（重写中）

**详细中文使用手册：** [docs/使用手册-clean_client.md](docs/使用手册-clean_client.md)

**双击运行（已打包）：** `release\CleanClient\CleanClient.exe`  
**一键重新打包：** 双击 `scripts\一键打包-CleanClient.bat`

见 `clean_client/README.md`。当前已完成：

- 数据模型 / RGB 编码 / 键位行解析 / ready 选择器（**15 tests passing**）
- 截屏后端骨架、SendInput、dry-run 引擎循环、MockVision 入口

```bash
python -m pytest clean_client/tests -v
python -m clean_client.app   # MockVision dry-run
```

设计与计划：

- `docs/superpowers/specs/2026-08-21-clean-autounholy-client-design.md`
- `docs/superpowers/plans/2026-08-21-clean-autounholy-client.md`
- 像素协议：`_analysis/lua_deobf/PIXEL_PROTOCOL_RECOVERED.md`

## 卡密登录（延期）

原版有远程后台发卡 + 卡密/账密登录 + 心跳（`prod-api`）。
当前 `clean_client` **先免登录**；完整计划见 `docs/auth-cardkey-plan.md`。

## 下一步可选

1. 补齐 `PixelProtocolVision` + PySide6 UI + 区域标定
2. 继续 Lua VM 拿精确坐标（或从实机导出 `skill_region.txt`）
3. 以后再做卡密后台（见 auth 计划文档）
4. 若你还有 `D:\project\dmProject\AutoPlayer` 原源码，可直接替换 stub 为真源码
