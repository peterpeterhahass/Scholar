"""
从 extracted_images.json 中提取所有 parent_content 和 parent_title 字段，
去重后输出。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ParentSection:
    """父章节信息"""
    parent_number: str
    parent_title: str
    parent_content: str


def extract_parents(json_path: str | Path) -> List[ParentSection]:
    """
    读取 extracted_images.json，提取去重后的 parent_title + parent_content。

    Args:
        json_path: extracted_images.json 的路径

    Returns:
        去重后的父章节列表
    """
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    seen: dict[str, ParentSection] = {}  # number -> ParentSection
    for item in data:
        key = item.get("parent_number", "")
        content = item.get("parent_content", "")
        if not key or key in seen or not content:
            continue
        seen[key] = ParentSection(
            parent_number=key,
            parent_title=item.get("parent_title", ""),
            parent_content=item.get("parent_content", ""),
        )

    return list(seen.values())


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    json_path = "temp/extractor_output/extracted_images.json"
    parents = extract_parents(json_path)

    print(f"共提取 {len(parents)} 个父章节\n")
    print("=" * 80)
    for p in parents:
        content_preview = p.parent_content[:120].replace("\n", " ") if p.parent_content else "(空)"
        print(f"  {p.parent_number} {p.parent_title}")
        print(f"    内容: {content_preview}...")
        print(f"    长度: {len(p.parent_content)} 字符")
        print("-" * 80)

    # 保存结果
    output_path = Path("temp/extractor_output/parent_sections.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_data = [
        {
            "parent_number": p.parent_number,
            "parent_title": p.parent_title,
            "parent_content": p.parent_content,
        }
        for p in parents
    ]
    output_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已保存: {output_path}")
