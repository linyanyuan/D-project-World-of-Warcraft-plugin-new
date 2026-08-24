# AutoPlayer 插件协议草稿（Lua 动态脱壳阶段）

> 来源：对 `addon/AutoPlayer/*.lua` 做 Lua 5.1 沙箱执行，在 VM 解密阶段截获的字符串/符号。  
> 完整源码尚未还原（Luraph 类 VM + 反调试，执行中途因算术/环境检查失败）。

## 1. 插件角色

- TOC 名：`AutoPlayer`
- 可选依赖：`Hekili`
- 作者字段：`cengxi`
- 与外置 Nirvana 客户端配合：游戏内计算技能可用性/状态，外置程序截屏识别并按键

## 2. 从符号推断的功能模块

### 2.1 判断引擎（Judgment / Laminar）

| 符号 | 推测 |
| --- | --- |
| `AreaSpellJudgment` | AOE 技能判定 |
| `HealingSpellJudgment` | 治疗技能判定 |
| `MiniBloodJudgment` | 小技能/血量相关判定 |
| `TargetStatusJudgment` | 目标状态判定 |
| `TimingJudgment` | 时机/GCD/施法时机 |
| `ProcessSpellConfig` / `ProcessSpellTarget` | 按配置处理技能与目标 |
| `ProcessGroupTarget` / `ProcessMemberTarget` / `ProcessSingleTarget` | 单/小队目标选择 |
| `CheckSpellConditions` / `CheckSpellUsage` / `IsSpellAvailable` | 技能条件与可用性 |
| `judgeItIsLighted` | 技能高亮/可点判定（常见于像素辅助） |
| `getSpellCD` / `GetSpellCooldownRemaining` / `CheckSpellCooldown` | CD 检测 |

### 2.2 状态检查

- 生命：`CheckHealthCondition` / `CheckHealthStatus` / `GetHealthLossPercent`
- 资源：`CheckPowerPercentage` / `CheckResource` / `UnitPower*`
- Buff/Debuff：`CheckGroupBuffStatus` / `CompareFateBuff*` / `UnitBuff` / `UnitDebuff` / `CountEnemiesWithDebuff`
- 目标：`IsTargetEnemy` / `CompareTargetDistance` / `UnitCastingInfo` / `CheckEnemyCountInRange`
- 场景：`CheckZoneCondition` / `IsInInstance` / `IsInBossFight`

### 2.3 模式开关（外置 UI 很可能同步这些）

- `ToggleAOEMode` / `SetAOEMode`
- `ToggleBurstMode` / `SetBurstMode`
- `ToggleMinorBurstMode` / `SetMinorBurstMode`
- `ToggleDefensiveMode` / `SetDefensiveMode`
- `ToggleDispelMode` / `SetDispelMode`
- `ToggleInterruptMode` / `SetInterruptMode`
- `TogglePause` / `ToggleApPause` / `SwitchApPause`

### 2.4 宏与按键

- `BuildMacroText` / `ApplyMacroToButton` / `GetMacroStore` / `GetDefaultMacro`
- `InitializeKeybindingSystem` / `ApplyKeybindings` / `HandleKeyPress`
- `StartKeyListener` / `StopKeyListener`
- `keyBindingSpellSulo` / `addRaidMacroSulo`

### 2.5 像素/绘制相关（对外置客户端最关键）

插件侧符号（Lua dump）：

- `CreateTexture` / `SetTexture` / `SetColorTexture`
- `SetVertexColor` / `SetTextColor` / `SetBackdropColor`
- `HexToRGB` / `SetAlpha`
- `CreateCenterMessageFrame` / `initPositionIcon` / `initSpellsTga`
- `ChangeSimpleActionBar` / `initializeTheActionBar`
- TOC SavedVariables 含 `PixelPerfectUIScaleDB`（必须像素对齐）

### 2.6 RGB 像素行协议（客户端二进制已证实）

> 详表见 `_analysis/lua_deobf/PIXEL_PROTOCOL_RECOVERED.md` 与 `RGB_MARKERS.json`。

外置 `SkillBotRuntimeCore` 对 Skill 区域截屏后按行解析（`visualize_pixel_row`）：

| 步 | 内容 | 解析函数 |
| --- | --- | --- |
| 1/5 | Header (Row 0) | `_parse_header_rgb_protocol` |
| 2/5 | 血条 | `parse_dynamic_health_bars` |
| 3/5 | 键位绑定 | `parse_row_data2_key_bindings` |
| 4/5 | CD / 高亮 | `parse_row_data3_cooldowns` |
| 5/5 | Buff 图标 | `recognize_all_buffs_dynamic`（OpenCV，非色块） |

**区域文件：** `skill_region.txt` / `target_region.txt` / `player_region.txt` / `buff_region.txt`  
键：`Skill` / `Target` / `Player` / `Buff` → `(x1,y1,x2,y2)`

**标记色：**

| 常量 | 色 |
| --- | --- |
| `_MARKER_START` | `#ff00ff` |
| `_MARKER_END` | `#ff8000` |
| `_MARKER_SEP` | `#808080` |
| `_MARKER_ITEM` | `#ffff00` |
| `_MARKER_SPELL` | `#ffffff` |
| `_MARKER_ETC` | `#2a5938` |
| `_MARKER_RED` | `#ff0000` |
| `_MARKER_RES` | `#ffff80` |

**技能 ID 编码（硬证据）：**

```
RGB 12ca33 -> 0x12ca33 -> 1231411
spell_id = (R << 16) | (G << 8) | B
```

**Header：** 含 `team_type`（0=solo,1=party,2=raid）、`member_count`、`spec`、`GCD`、若干 bool/spell 字段。  
**键位行：** 标记扫描 → `Alt`/`Ctrl`/`main_key`/`is_item`；与循环 `pixel_keys` 对齐后按键。  
**CD 行：** `highlighted` ↔ 插件 `judgeItIsLighted`；`cd_remain_*` / `charge_*` / `unusable`；R 通道区分 kind（R=1/2/3…）。  
**Buff：** 独立区域，模板匹配，`buff_match_threshold` 默认 0.7。

## 3. 与客户端侧的对应关系

| 客户端（已恢复） | 插件侧符号 |
| --- | --- |
| `skill_conditions.evaluate_*` | `CheckSpellConditions` / `CheckHealth*` / buff/count 检查 |
| `_parse_header_rgb_protocol` / `parse_row_data2_*` / `parse_row_data3_*` | `SetColorTexture` / `initPositionIcon` / `HexToRGB` |
| `highlighted` / `require_highlight` | `judgeItIsLighted` |
| `cd_remain_*` / `charge_*` | `getSpellCD` / `GetSpellCooldownRemaining` |
| `DataRecogPage` / `append_recog` | 纹理/色块识别结果展示 |
| `capture_mode` 方式一/二/三 | `PrintWindow` / `mss` / `dxcam` 对应窗口捕获 |
| `FluentSkillCycleDialog` / `pixel_keys` | 循环/技能列表；插件侧 `addSkillNamesData` |
| Hekili 可选依赖 | 字符串 `Hekili` 明确出现 |

## 4. 产物文件

- `_analysis/lua_deobf/CLEAN_symbols.txt` — 清洗后的符号
- `_analysis/lua_deobf/API_idents.txt` — API 风格标识符
- `_analysis/lua_deobf/ALL_keyword_hits.txt` — 关键词命中原文
- `_analysis/lua_deobf/CHINESE_strings.txt` — 中文串（若有）
- `_analysis/lua_deobf/*_strings.txt` — 各文件原始转储
- `_analysis/lua_deobf/PIXEL_PROTOCOL_RECOVERED.md` — RGB 协议还原笔记
- `_analysis/lua_deobf/RGB_MARKERS.json` — 标记色/行解析机读表
- `scripts/lua51_pixel_trace.lua` — 增强版动态 API/色块调用追踪器
- `_analysis/lua_deobf/*_pixel_{strings,calls,frames}.txt` — 追踪器输出

## 5. 未完成

1. 完整 Lua 源码还原（Luraph VM anti-tamper：nil 毒化寄存器；0/stub 中和会破坏函数或数值路径）
2. Skill 区域精确像素坐标与 frame/texture 名字（需活体 `/fstack`、客户端 `skill_region.txt`，或 VM 跑通后打 `SetPoint`/`SetColorTexture` 日志）
3. Header 字段名与顺序的完整对照表；CD kind 的 G/B 载荷字典
4. `BUFF_ICON_*` / `AURA_*` 布局常量的数值
5. 各专精循环默认数据（云端 `skill_cycles` / online cycles）
