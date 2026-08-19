"""
MinerU 生成的 Markdown 论文内容提取器。

按论文结构拆分 Markdown，只提取包含图片的章节及其父章节。
每条输出包含：图片原始链接、图片所在章节完整内容、父章节信息。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class ImageSection:
    """每张图片及其所在章节上下文"""
    image_path: str           # md 中图片原始链接，如 images/xxx.jpg
    image_caption: str = ""   # Fig. N 描述
    section_title: str = ""   # 图片所在章节标题
    section_number: str = ""  # 章节编号，如 "4.1"
    section_content: str = "" # 图片所在章节的完整原始 Markdown
    parent_title: str = ""    # 父章节标题
    parent_number: str = ""   # 父章节编号
    parent_content: str = ""  # 父章节完整原始 Markdown


# ── 正则预编译 ────────────────────────────────────────────

_RE_H1 = re.compile(r"^# (.+)$", re.MULTILINE)
_RE_H2 = re.compile(r"^## (.+)$", re.MULTILINE)
_RE_H3 = re.compile(r"^### (.+)$", re.MULTILINE)
_RE_IMAGE = re.compile(r"!\[.*?\]\(([^)]+)\)")
_RE_FIGURE_CAPTION = re.compile(r"^(Fig\.\s*\d+[a-z]?\.?\s*.+?)\s*$")
_RE_SECTION_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.\s*(.+)$")
_RE_REF_SECTION = re.compile(r"^References|Bibliography", re.IGNORECASE)


# ── 提取器 ────────────────────────────────────────────────

class MarkdownExtractor:
    """
    提取论文 Markdown 中所有图片，并附带图片所在章节及父章节的完整内容。

    用法::

        results = MarkdownExtractor().extract("path/to/paper.md")
        for item in results:
            print(item.image_path, item.section_title)
    """

    def extract(self, md_path: str | Path) -> List[ImageSection]:
        md_path = Path(md_path)
        markdown = md_path.read_text(encoding="utf-8")
        return self.extract_from_text(markdown)

    def extract_from_text(self, markdown: str) -> List[ImageSection]:
        # 1. 按 ## 拆分出所有章节块
        sections = self._split_sections(markdown)
        # 2. 按章节编号建立父子关系
        parent_map = self._build_parent_map(sections)
        # 3. 收集有图片的章节
        return self._collect_image_sections(sections, parent_map)

    # ── 拆分章节 ──

    def _split_sections(self, md: str) -> list[dict]:
        """
        将 markdown 按 ## 拆分为有序章节列表。
        每个元素: {"number": str, "title": str, "raw": str}
        """
        h2_matches = list(_RE_H2.finditer(md))

        # 找正文起点（第一个带编号的 ##）
        body_start = None
        for i, m in enumerate(h2_matches):
            if _RE_SECTION_NUM.match(m.group(1).strip()):
                body_start = i
                break
        if body_start is None:
            return []

        sections: list[dict] = []
        for i in range(body_start, len(h2_matches)):
            cur = h2_matches[i]
            nxt = h2_matches[i + 1] if i + 1 < len(h2_matches) else None
            end = nxt.start() if nxt else len(md)
            title_raw = cur.group(1).strip()

            if _RE_REF_SECTION.match(title_raw):
                break

            num, title = self._parse_section_title(title_raw)
            sections.append({
                "number": num,
                "title": title,
                "raw": md[cur.end():end],
            })

        return sections

    @staticmethod
    def _parse_section_title(title: str) -> tuple[str, str]:
        m = _RE_SECTION_NUM.match(title)
        if m:
            return m.group(1), m.group(2)
        return "", title

    # ── 按编号建立父子关系 ──

    @staticmethod
    def _build_parent_map(sections: list[dict]) -> dict[int, int]:
        """
        返回 {子章节索引 -> 父章节索引} 的映射。

        规则：去掉编号最后一段即为父编号。
        例如 "4.2.1" → 父编号 "4.2"，"5.1" → 父编号 "5"。
        """
        # 编号 → 索引
        num_to_idx: dict[str, int] = {}
        for idx, sec in enumerate(sections):
            if sec["number"]:
                num_to_idx[sec["number"]] = idx

        parent_map: dict[int, int] = {}
        for idx, sec in enumerate(sections):
            num = sec["number"]
            if not num or "." not in num:
                continue  # 顶级章节无父
            # "4.2.1" → "4.2"，"5.1" → "5"
            parent_num = num.rsplit(".", 1)[0]
            if parent_num in num_to_idx:
                parent_map[idx] = num_to_idx[parent_num]

        return parent_map

    # ── 收集图片结果 ──

    def _collect_image_sections(
        self, sections: list[dict], parent_map: dict[int, int]
    ) -> List[ImageSection]:
        results: List[ImageSection] = []

        for idx, sec in enumerate(sections):
            images = self._find_images(sec["raw"])
            if not images:
                continue

            # 父章节信息
            parent_idx = parent_map.get(idx)
            if parent_idx is not None:
                parent = sections[parent_idx]
                parent_title = parent["title"]
                parent_number = parent["number"]
                parent_content = parent["raw"].strip()
            else:
                parent_title = ""
                parent_number = ""
                parent_content = ""

            for img_path, caption in images:
                results.append(ImageSection(
                    image_path=img_path,
                    image_caption=caption,
                    section_title=sec["title"],
                    section_number=sec["number"],
                    section_content=sec["raw"].strip(),
                    parent_title=parent_title,
                    parent_number=parent_number,
                    parent_content=parent_content,
                ))

        return results

    @staticmethod
    def _find_images(block: str) -> list[tuple[str, str]]:
        """从 block 中提取所有图片 (path, caption)"""
        results: list[tuple[str, str]] = []
        lines = block.split("\n")
        for i, line in enumerate(lines):
            m = _RE_IMAGE.search(line)
            if m:
                path = m.group(1)
                caption = ""
                if i + 1 < len(lines):
                    cap_m = _RE_FIGURE_CAPTION.search(lines[i + 1])
                    if cap_m:
                        caption = cap_m.group(1).strip()
                results.append((path, caption))
        return results


# ── 便捷入口 ──────────────────────────────────────────────

def extract_paper(md_path: str | Path) -> List[ImageSection]:
    """快捷函数：提取论文中所有图片及其章节上下文"""
    return MarkdownExtractor().extract(md_path)
