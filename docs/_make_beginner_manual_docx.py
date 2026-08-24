"""Generate CleanClient beginner Chinese DOCX manual (stable usable build)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parent / "CleanClient-小白完整使用手册.docx"
RELEASE_DOCS = Path(__file__).resolve().parents[1] / "release" / "CleanClient" / "docs"


def set_run(
    run: Any, size: float = 11, bold: bool = False, color: RGBColor | None = None
) -> None:
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "微软雅黑"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    if color is not None:
        run.font.color.rgb = color


def add_title(doc: Any, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run(r, 22, True)
    p.paragraph_format.space_after = Pt(6)


def add_center(
    doc: Any, text: str, size: float = 11, color: RGBColor | None = None
) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run(r, size, False, color)
    p.paragraph_format.space_after = Pt(4)


def h(doc: Any, text: str, level: int = 1) -> None:
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_run(run, 16 if level == 1 else 13, True)


def para(doc: Any, text: str, bold: bool = False, size: float = 11) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run(run, size, bold)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE


def bullets(doc: Any, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        run = p.add_run(item)
        set_run(run, 11)
        p.paragraph_format.space_after = Pt(2)


def numbered(doc: Any, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Number")
        run = p.add_run(item)
        set_run(run, 11)
        p.paragraph_format.space_after = Pt(2)


def table(doc: Any, headers: list[str], rows: list[list[str]]) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(header)
        set_run(run, 10.5, True)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val)
            set_run(run, 10.5)
    doc.add_paragraph()


def path_line(doc: Any, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run(run, 10.5)
    run.font.name = "Consolas"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Cm(0.5)


def build() -> Path:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.4)
    sec.right_margin = Cm(2.4)

    add_title(doc, "CleanClient 小白完整使用手册")
    add_center(
        doc,
        "稳定可用版（阶段 1–3 已完成）· 研究 / 开发向发版",
        12,
        RGBColor(0x55, 0x55, 0x55),
    )
    add_center(
        doc,
        "面向零基础用户 · 按步骤照做即可",
        10.5,
        RGBColor(0x77, 0x77, 0x77),
    )
    add_center(
        doc,
        r"文档：docs\CleanClient-小白完整使用手册.docx",
        10,
        RGBColor(0x88, 0x88, 0x88),
    )

    para(doc, "先看这四句（非常重要）", bold=True)
    bullets(
        doc,
        [
            "这是当前「稳定可用版」，不是永不改动的最终商业正式版；后续还可增强。",
            "默认「只记日志，不按键」。取消勾选时会弹确认框，确认后才会真按键。",
            r"发版包里有两样东西：CleanClient.exe（电脑软件）和 addon\AutoPlayer（魔兽插件）。插件必须手动复制进游戏。",
            "第一次请先干跑看日志出现「动作 法术ID=…」，确认无误后再考虑真按键。",
        ],
    )

    h(doc, "一、你需要准备什么")
    numbered(
        doc,
        [
            "能正常登录《魔兽世界》正式服 / 时光服的电脑。",
            "完整的 CleanClient 发版文件夹（不要只有单独一个 exe）。",
            "知道魔兽安装目录（要复制插件）。",
        ],
    )
    para(doc, "发版文件夹通常在：")
    path_line(doc, r"D:\project\World of Warcraft plugin new\release\CleanClient")
    para(doc, "正常应看到：")
    table(
        doc,
        ["名称", "是什么", "你要做什么"],
        [
            ["CleanClient.exe", "控制软件", "双击打开"],
            ["_internal", "运行依赖", "不要删、不要只拷 exe"],
            [r"addon\AutoPlayer", "魔兽插件", "复制到 AddOns"],
            ["docs", "说明文档", "不会用时查看"],
            ["请先读-安装说明.txt", "最短提醒", "建议先看"],
        ],
    )

    h(doc, "二、安装魔兽插件 AutoPlayer")
    numbered(
        doc,
        [
            "完全退出魔兽世界。",
            r"复制发版包里的 addon\AutoPlayer 到：",
        ],
    )
    path_line(doc, r"...\World of Warcraft\_retail_\Interface\AddOns\AutoPlayer")
    para(doc, "正确结果必须能看到：")
    path_line(
        doc,
        r"...\AddOns\AutoPlayer\AutoPlayer.toc",
    )
    para(doc, "错误示例（多套一层）：")
    path_line(doc, r"...\AddOns\AutoPlayer\AutoPlayer\AutoPlayer.toc")
    numbered(
        doc,
        [
            "重新打开魔兽，选人界面点「插件」，勾选 AutoPlayer。",
            "进游戏后应能看到协议相关色块/像素条（外观以插件为准）。",
        ],
    )

    h(doc, "三、打开软件")
    para(doc, "方式 A：双击 exe（推荐）", bold=True)
    path_line(
        doc,
        r"D:\project\World of Warcraft plugin new\release\CleanClient\CleanClient.exe",
    )
    bullets(
        doc,
        [
            "保持整个 CleanClient 文件夹完整。",
            "若杀毒误报，确认来源是你自己打包的结果后再放行。",
            "源码有更新后，请重新运行 scripts\\pack-CleanClient.bat 再发版。",
        ],
    )
    para(doc, "方式 B：源码启动", bold=True)
    path_line(doc, r'cd "D:\project\World of Warcraft plugin new"')
    path_line(doc, "python -m clean_client.app")

    h(doc, "四、界面说明")
    para(doc, "左侧四个页面：控制台 / 循环 / 识别 / 系统设置。")
    h(doc, "1. 控制台", 2)
    table(
        doc,
        ["控件", "作用", "建议"],
        [
            ["启动 / 停止", "开始或结束循环", "先勾选只记日志再启动"],
            ["只记日志，不按键", "不向游戏发键", "默认勾着；取消会确认"],
            ["优先高亮技能", "优先选高亮技能", "可保持默认"],
            ["截屏方式", "抓游戏画面方式", "实机用方式一/二/三，勿用空（测试）"],
            ["周期(ms)", "循环间隔", "默认约 30，先别改"],
            ["运行日志", "输出信息", "关注空闲 / 动作 / 提示 / 错误"],
        ],
    )
    h(doc, "2. 循环", 2)
    para(doc, "显示当前技能优先级（如邪恶 DK）。当前主要查看，一般不用改。")
    h(doc, "3. 识别（重点）", 2)
    table(
        doc,
        ["功能", "作用"],
        [
            ["模拟识别", "不读屏，调试用；日志多为空闲"],
            ["像素协议", "读取 AutoPlayer 色块（绑定行 + 冷却/高亮行）"],
            ["区域目录", "Skill/Target/Player/Buff 的 txt 所在文件夹"],
            ["打开区域标定器", "手动框选并保存区域"],
            ["自动建议 Skill 区域", "自动找品红色 START 条并写出 skill_region.txt"],
            ["抓取预览 / 自动刷新", "看截屏和区域框是否对准"],
        ],
    )
    h(doc, "4. 系统设置", 2)
    bullets(
        doc,
        [
            "窗口关键字默认含 World of Warcraft、魔兽世界。",
            "改完点保存；浏览区域目录后也会自动写入配置。",
        ],
    )

    h(doc, "五、推荐完整流程（实机）")
    numbered(
        doc,
        [
            "安装并启用 AutoPlayer。",
            "打开 CleanClient.exe。",
            "控制台：勾选「只记日志」；截屏选「方式二」（不行再换一/三）。",
            "识别页：模式选「像素协议」。",
            "点「自动建议 Skill 区域」，再点「抓取预览」，确认蓝框大致罩住色块条。",
            "框不准就打开标定器精修并保存（保存后会自动填回区域目录）。",
            "回到控制台点「启动」。",
            "看日志：先可能有一条「提示:…」；正常时应出现「动作 法术ID=… 按键=…」。",
            "确认按键字母/数字符合你的键位后，如需真按键：取消「只记日志」→ 确认 → 再启动。",
            "不用时点「停止」。",
        ],
    )

    h(doc, "六、截屏方式怎么选")
    table(
        doc,
        ["选项", "说明", "何时用"],
        [
            ["空（测试）", "不真截屏", "只测界面；像素协议下会拒绝启动"],
            ["方式一", "PrintWindow 抓窗口", "窗口模式可试；需找到魔兽窗口"],
            ["方式二", "MSS 抓可见画面", "通常最稳，优先"],
            ["方式三", "DXGI/dxcam", "更快；方式二不行时再试"],
        ],
    )

    h(doc, "七、现在能做什么 / 不能做什么")
    table(
        doc,
        ["事项", "状态"],
        [
            ["中文界面、启停、只记日志", "可以"],
            ["标定 / 自动建议 Skill / 预览", "可以"],
            ["像素协议读绑定 + 冷却/高亮（v1）", "可以（依赖插件编码一致）"],
            ["确认后真按键", "可以（有风险，需自行确认）"],
            ["免登录", "可以（暂无卡密）"],
            ["完整原版一切协议 / 自动找全区域", "未完全等价，后续可增强"],
            ["保证游戏安全 / 不封号", "无法保证；请自担风险"],
        ],
    )

    h(doc, "八、常见问题")
    faqs = [
        (
            "Q：这是最终版吗？",
            "A：是当前稳定可用发版，不是永远不再改的最终商业版。阶段1–3已完成，后续还可增强。",
        ),
        (
            "Q：日志一直空闲？",
            "A：若仍是模拟识别，正常。像素协议下请检查：插件启用、截屏方式、Skill 框是否对准、预览是否有色块。",
        ),
        (
            "Q：提示无法启动？",
            "A：像素协议必须：真实截屏方式 + 有效 Skill 区域；方式一还要找到魔兽窗口。",
        ),
        (
            "Q：会不会乱按键？",
            "A：默认不会。取消只记日志必须确认；建议先干跑看「按键=」是否正确。",
        ),
        (
            "Q：自动建议的框不准？",
            "A：它是粗定位。请用预览检查，再用标定器精修。",
        ),
        (
            "Q：朋友怎么用？",
            "A：发整个 CleanClient 文件夹；朋友先装插件，再开软件。私有 GitHub 需加协作者才能下 Releases。",
        ),
        (
            "Q：打包脚本双击没反应？",
            "A：请用 scripts\\pack-CleanClient.bat；正常会有黑窗口跑约 1.5–2 分钟。",
        ),
    ]
    for q, a in faqs:
        para(doc, q, bold=True)
        para(doc, a)

    h(doc, "九、验收清单")
    bullets(
        doc,
        [
            "已复制 AutoPlayer 到 _retail_\\Interface\\AddOns 并勾选",
            "已打开完整 CleanClient 文件夹中的 exe",
            "只记日志已勾选",
            "识别=像素协议，截屏=方式一/二/三",
            "已自动建议或手动标定 Skill，预览框大致正确",
            "启动后日志出现动作 法术ID=…，按键= 符合键位",
            "（可选）确认后才关闭只记日志尝试真按键",
        ],
    )

    h(doc, "十、相关路径")
    table(
        doc,
        ["内容", "路径"],
        [
            ["发版目录", r"release\CleanClient"],
            ["本手册", r"docs\CleanClient-小白完整使用手册.docx"],
            ["Markdown 手册", r"docs\使用手册-clean_client.md"],
            ["重新打包", r"scripts\pack-CleanClient.bat"],
            ["插件源", r"addon\AutoPlayer"],
        ],
    )
    para(
        doc,
        "—— 文档结束 —— 若某一步与屏幕不符，把截图发出来即可对照修改。",
        bold=True,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    if RELEASE_DOCS.parent.exists():
        RELEASE_DOCS.mkdir(parents=True, exist_ok=True)
        doc.save(str(RELEASE_DOCS / OUT.name))
    return OUT


if __name__ == "__main__":
    path = build()
    print(path)
    print("size=", path.stat().st_size)
