"""
测试 parent_extractor.py，将提取结果保存到文件。
"""

import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# test -> markdown_extractor -> services -> backend
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from services.markdown_extractor.parent_extractor import extract_parents

# ── 输入 ──
json_path = BACKEND_DIR / "temp/extractor_output/extracted_images.json"

# ── 提取 ──
parents = extract_parents(json_path)

# ── 控制台输出 ──
print(f"共提取 {len(parents)} 个父章节\n")
print("=" * 80)

for i, p in enumerate(parents, 1):
    print(f"【父章节 {i}】")
    print(f"  编号:     {p.parent_number}")
    print(f"  标题:     {p.parent_title}")
    print(f"  内容长度: {len(p.parent_content)} 字符")
    if p.parent_content:
        print(f"  内容预览:")
        for line in p.parent_content[:200].split("\n"):
            print(f"    {line}")
        if len(p.parent_content) > 200:
            print(f"    ...")
    else:
        print(f"  内容: (空)")
    print("-" * 80)

# ── 保存 JSON ──
output_dir = BACKEND_DIR / "temp/extractor_output"
output_dir.mkdir(parents=True, exist_ok=True)

json_out = output_dir / "parent_sections.json"
data = [
    {
        "parent_number": p.parent_number,
        "parent_title": p.parent_title,
        "parent_content": p.parent_content,
    }
    for p in parents
]
json_out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n已保存 JSON: {json_out}")

# ── 保存可读文本 ──
txt_out = output_dir / "parent_sections.txt"
lines = []
for i, p in enumerate(parents, 1):
    lines.append(f"{'=' * 80}")
    lines.append(f"父章节 {i}: {p.parent_number} {p.parent_title}")
    lines.append(f"{'=' * 80}")
    if p.parent_content:
        lines.append(p.parent_content)
    else:
        lines.append("(无内容)")
    lines.append("")
txt_out.write_text("\n".join(lines), encoding="utf-8")
print(f"已保存 TXT:  {txt_out}")
