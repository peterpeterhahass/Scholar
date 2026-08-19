"""
测试 MarkdownExtractor，将提取结果保存到文件。
"""

import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

from services.markdown_extractor.extractor import extract_paper

# ── 输入 ──
md_path = "temp/mineru_output/2e13b80d-fd1d-4fc9-b26d-9579c7a80654/auto/2e13b80d-fd1d-4fc9-b26d-9579c7a80654.md"

# ── 提取 ──
results = extract_paper(md_path)

# ── 控制台预览 ──
print(f"共提取 {len(results)} 张图片\n")
print("=" * 90)

for i, item in enumerate(results, 1):
    sec = f"{item.section_number} {item.section_title}" if item.section_number else item.section_title
    parent = f"{item.parent_number} {item.parent_title}" if item.parent_number else "(顶级章节，无父章节)"
    cap = f" — {item.image_caption}" if item.image_caption else ""

    print(f"【图片 {i}】{cap}")
    print(f"  image_path:     {item.image_path}")
    print(f"  section:        {sec}")
    print(f"  parent_section: {parent}")
    print(f"  section_content: ({len(item.section_content)} 字符)")
    print(f"  parent_content:  ({len(item.parent_content)} 字符)")
    print("-" * 90)

# ── 保存为 JSON ──
output_dir = Path("temp/extractor_output")
output_dir.mkdir(parents=True, exist_ok=True)

json_path = output_dir / "extracted_images.json"
data = []
for item in results:
    data.append({
        "image_path": item.image_path,
        "image_caption": item.image_caption,
        "section_number": item.section_number,
        "section_title": item.section_title,
        "section_content": item.section_content,
        "parent_number": item.parent_number,
        "parent_title": item.parent_title,
        "parent_content": item.parent_content,
    })

json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n已保存 JSON: {json_path}")

# ── 保存为可读 Markdown ──
md_out_path = output_dir / "extracted_images.md"
lines = ["# 图片提取结果\n"]

for i, item in enumerate(results, 1):
    sec = f"{item.section_number} {item.section_title}" if item.section_number else item.section_title
    parent = f"{item.parent_number} {item.parent_title}" if item.parent_number else "(顶级章节)"
    cap = f" — {item.image_caption}" if item.image_caption else ""

    lines.append(f"## 图片 {i}{cap}\n")
    lines.append(f"- **image_path**: `{item.image_path}`\n")
    lines.append(f"- **所在章节**: {sec}\n")
    lines.append(f"- **父章节**: {parent}\n")
    lines.append(f"### 所在章节完整内容\n")
    lines.append(f"```\n{item.section_content}\n```\n")
    if item.parent_content:
        lines.append(f"### 父章节完整内容\n")
        lines.append(f"```\n{item.parent_content}\n```\n")
    lines.append("---\n")

md_out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"已保存 Markdown: {md_out_path}")
