"""AI 报告分段解析与 Markdown 导出辅助。"""

import re
from html import escape
from typing import List

from app.schemas.ai_schema import ReportSection

SECTION_TITLES = [
    "试验概况",
    "关键数据",
    "异常记录",
    "可能原因",
    "改进建议",
]

_BRACKET_SECTION_RE = re.compile(r"【\s*([^】]+?)\s*】\s*")
_MD_HEADER_RE = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.MULTILINE)


def parse_sections_from_content(content: str) -> List[ReportSection]:
    """从 DeepSeek 单次回复中解析分段（支持【标题】与 Markdown 标题）。"""
    text = (content or "").strip()
    if not text:
        return []

    sections: List[ReportSection] = []
    if "【" in text and "】" in text:
        pos = 0
        for match in _BRACKET_SECTION_RE.finditer(text):
            if match.start() > pos:
                gap = text[pos:match.start()].strip()
                if gap and not sections:
                    sections.append(ReportSection(title="前言", content=gap))
            title = match.group(1).strip()
            start = match.end()
            next_match = _BRACKET_SECTION_RE.search(text, start)
            end = next_match.start() if next_match else len(text)
            body = text[start:end].strip()
            if title:
                sections.append(ReportSection(title=title, content=body))
            pos = end
        if sections:
            return sections

    matches = list(_MD_HEADER_RE.finditer(text))
    if matches:
        for i, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if title:
                sections.append(ReportSection(title=title, content=body))
        if sections:
            return sections

    return [ReportSection(title="分析报告", content=text)]


def parse_sections_from_stored(
    summary_text: str, analysis_text: str
) -> List[ReportSection]:
    """从数据库中的 summary / analysis 字段还原分段。"""
    sections: List[ReportSection] = []
    for block in (summary_text or "").split("【"):
        if "】" not in block:
            continue
        title, content = block.split("】", 1)
        sections.append(ReportSection(title=title.strip(), content=content.strip()))
    for block in (analysis_text or "").split("【"):
        if "】" not in block:
            continue
        title, content = block.split("】", 1)
        sections.append(ReportSection(title=title.strip(), content=content.strip()))
    if sections:
        return sections
    return [
        ReportSection(title="试验概况与数据摘要", content=(summary_text or "").strip()),
        ReportSection(title="分析与建议", content=(analysis_text or "").strip()),
    ]


def sections_to_text(sections: List[ReportSection]) -> tuple[str, str]:
    summary_titles = {"试验概况", "关键数据", "异常记录"}
    analysis_titles = {"可能原因", "改进建议"}
    summary_parts = [s for s in sections if s.title in summary_titles]
    analysis_parts = [s for s in sections if s.title in analysis_titles]
    if not summary_parts and not analysis_parts:
        mid = max(1, len(sections) // 2)
        summary_parts = sections[:mid]
        analysis_parts = sections[mid:]
    summary_text = "\n\n".join(f"【{s.title}】\n{s.content}" for s in summary_parts)
    analysis_text = "\n\n".join(f"【{s.title}】\n{s.content}" for s in analysis_parts)
    return summary_text, analysis_text


def sections_to_markdown(sections: List[ReportSection]) -> str:
    parts: List[str] = []
    for sec in sections:
        parts.append(f"## {sec.title}\n\n{sec.content.strip()}\n")
    return "\n".join(parts).strip()


def markdown_to_html(text: str) -> str:
    """将 Markdown 转为 HTML（用于导出）；优先使用 markdown 库。"""
    raw = (text or "").strip()
    if not raw:
        return ""
    try:
        import markdown as md_lib

        return md_lib.markdown(
            raw,
            extensions=["extra", "nl2br", "sane_lists"],
        )
    except ImportError:
        escaped = escape(raw)
        return f"<p>{escaped.replace(chr(10), '<br/>')}</p>"
