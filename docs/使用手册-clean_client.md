# clean_client 使用手册（当前版本）

适用目录：`D:\project\World of Warcraft plugin new`

> 当前是 **研究/开发版**：默认 **dry-run（只记日志，不真按键）**，默认用 **MockVision（假识别）**。  
> **免登录**。卡密方案以后再做，见 `docs/auth-cardkey-plan.md`。

---

## 0. 两个概念先搞懂

### A. 「标定结果接到主界面」是什么意思？

现在有两个程序：

1. **主界面** `python -m clean_client.app`：负责开始/停止自动循环  
2. **标定工具** `python -m clean_client.tools.calibrate_regions`：在截图上框出 Skill/Target/Player/Buff 四个区域，并保存成 txt

目前它们是**分开的**：标定工具存了文件，主界面**还不会自动去读这些文件**。

「接到主界面」= 以后在主界面里选一个区域文件夹，启动时自动加载那 4 个 txt。

### B. 「接真实 PixelProtocolVision」是什么意思？

- **MockVision（现在）**：不看屏幕，假装没有技能可读 → 日志里多半是 `idle`  
- **PixelProtocolVision（下一步）**：真的去截屏，按 AutoPlayer 插件画的色块读技能 ID，再决定按哪个键

所以：即使你现在点「开始」，**也不会自动打怪**，这是正常的。

---

## 1. 环境准备（只需做一次）

1. 打开 PowerShell 或终端  
2. 进入项目目录：

```powershell
cd "D:\project\World of Warcraft plugin new"
```

1. 安装依赖：

```powershell
pip install -r clean_client/requirements.txt
```

1. 跑测试确认环境正常（可选但推荐）：

```powershell
python -m pytest clean_client/tests -q
```

看到 `passed` 即可。

---

## 2. 启动主界面（日常入口）

### 方式 A：双击 exe（已打包）

打开并双击：

`D:\project\World of Warcraft plugin new\release\CleanClient\CleanClient.exe`

> 请保持整个 `CleanClient` 文件夹完整，不要只拷贝单个 exe。

以后重新打包：双击 `scripts\一键打包-CleanClient.bat`

### 方式 B：源码启动（开发）

```powershell
cd "D:\project\World of Warcraft plugin new"
python -m clean_client.app
```

你会看到窗口，大致有：

| 控件 | 作用 |
| --- | --- |
| 启动 / 停止 | 开始/停止循环线程 |
| 只记日志，不按键 | **务必先勾着**：只写日志，不向游戏按键 |
| 截屏方式 | 见下方「截屏方式说明」 |
| 周期(ms) | 循环间隔（默认约 30） |
| 运行日志 | 输出 `空闲` / `动作 ...` / `错误` |

### 截屏方式说明

| 界面选项 | 技术 | 含义 |
| --- | --- | --- |
| 空（测试·不截屏） | null | 不真正截屏，联调用 |
| 方式一 · 窗口打印（PrintWindow） | PrintWindow | 抓指定窗口内容，窗口模式常用 |
| 方式二 · 屏幕截取（MSS） | MSS | 抓屏幕上实际显示的画面，简单稳定 |
| 方式三 · 高速复制（DXGI） | dxcam | DirectX 桌面复制，通常更快 |

某种方式黑屏/失败时，换另外一种即可。

### 现在点 Start 会发生什么？

- 后台线程开始转  
- 因为还是 **MockVision**，通常日志是 `idle`  
- 因为 **dry_run**，即使将来识别到技能也**不会真按键**

### 命令行模式（不弹窗）

```powershell
python -m clean_client.app --cli
```

`Ctrl+C` 结束。

---

## 3. 使用区域标定工具（为以后真实识别做准备）

```powershell
cd "D:\project\World of Warcraft plugin new"
python -m clean_client.tools.calibrate_regions
```

可选参数：

```powershell
python -m clean_client.tools.calibrate_regions --dir .\regions --capture null
```

### 建议流程

1. 先用 `null` 练习：点 **Grab frame** 看合成图  
2. 选择区域类型：`Skill` / `Target` / `Player` / `Buff`  
3. 在图上拖拽框选，或改坐标数字  
4. **Save regions…** 存到例如：

```text
D:\project\World of Warcraft plugin new\regions\
  skill_region.txt
  target_region.txt
  player_region.txt
  buff_region.txt
```

每个文件一行：`x1 y1 x2 y2`

### 实机标定（以后要真识别时）

1. 打开魔兽世界，加载 **AutoPlayer** 插件  
2. 标定工具截屏模式改成 `mss` / `dxcam` / `printwindow`（对应方式二/三/一，仍可能需微调）  
3. Grab frame 后，框住插件画的像素条/色块区域（尤其是 **Skill**）  
4. 保存到 `regions\`  

> 注意：主界面**当前还不会自动读**这个文件夹；这是下一步要接的功能。

---

## 4. 游戏内还需要什么？

若目标是「真自动」：

1. 魔兽里安装并启用 `addon/AutoPlayer`（来自 retail 插件包）  
2. 分辨率 / UI 缩放尽量固定（协议依赖像素对齐）  
3. 标定好 Skill 等区域  
4. 主界面改用 PixelProtocolVision，并在确认日志正确后，再取消 dry_run  

当前版本**还没走到第 4 步**。

---

## 5. 你现在就能做的最小试用清单

- [ ] `pip install -r clean_client/requirements.txt`  
- [ ] `python -m pytest clean_client/tests -q`  
- [ ] `python -m clean_client.app` 打开主界面，点 Start，看日志  
- [ ] 确认 dry_run 勾选  
- [ ] `python -m clean_client.tools.calibrate_regions` 练习框选并保存  
- [ ] （可选）游戏开着时试一次真实截屏 Grab  

---

## 6. 常见问题

**Q: 为什么一直 idle？**  
A: MockVision 不读屏，属于正常。

**Q: 会不会帮我按键？**  
A: dry_run 勾选时不会。即使取消勾选，没有真实识别也基本无有效按键。

**Q: 要不要登录卡密？**  
A: 现在不要。以后要做，计划在 `docs/auth-cardkey-plan.md`。

**Q: 标定了为什么主界面没变化？**  
A: 还没接线。告诉我「接上标定+真实识别」就可以继续开发。

---

## 7. 相关文档

- 设计：`docs/superpowers/specs/2026-08-21-clean-autounholy-client-design.md`  
- 计划：`docs/superpowers/plans/2026-08-21-clean-autounholy-client.md`  
- 像素协议：`_analysis/lua_deobf/PIXEL_PROTOCOL_RECOVERED.md`  
- 卡密延期：`docs/auth-cardkey-plan.md`  
- 简版说明：`clean_client/README.md`
