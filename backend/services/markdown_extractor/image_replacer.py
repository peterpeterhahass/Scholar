"""
读取 image_descriptions.json，在原始论文 Markdown 的图片行和 caption 行之后，
追加模型生成的详细描述信息。不删除、不替换任何原始内容。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional


_RE_IMAGE_LINE = re.compile(r"^!\[.*?\]\((images/[^)]+)\)\s*$")
_RE_FIG_CAPTION = re.compile(r"^Fig\.\s*\d+[a-z]?\.?\s*")


def append_descriptions(
    md_path: str | Path,
    descriptions_path: str | Path,
    output_path: Optional[str | Path] = None,
) -> str:
    """
    在 markdown 的图片行和 caption 行之后，追加对应的 description 文本。
    保留所有原始内容不变。

    Args:
        md_path: 原始论文 Markdown 文件路径
        descriptions_path: image_descriptions.json 路径
        output_path: 输出文件路径，为 None 则不写文件

    Returns:
        处理后的 Markdown 文本
    """
    descs = json.loads(Path(descriptions_path).read_text(encoding="utf-8"))
    # image_path -> description
    desc_map = {item["image_path"]: item["description"] for item in descs}

    md_text = Path(md_path).read_text(encoding="utf-8")
    lines = md_text.split("\n")
    result_lines: list[str] = []

    i = 0
    appended = 0
    while i < len(lines):
        m = _RE_IMAGE_LINE.match(lines[i])
        if m:
            img_path = m.group(1)

            # 保留原始图片行
            result_lines.append(lines[i])
            i += 1

            # 保留 caption 行（如果有）
            if i < len(lines) and _RE_FIG_CAPTION.match(lines[i].strip()):
                result_lines.append(lines[i])
                i += 1

            # 在图片行 + caption 行之后追加描述
            if img_path in desc_map:
                result_lines.append("")
                result_lines.append(desc_map[img_path])
                result_lines.append("")
                appended += 1

            continue

        result_lines.append(lines[i])
        i += 1

    output = "\n".join(result_lines)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
        print(f"已保存: {out} (追加了 {appended} 张图片的描述)")

    return output


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    BACKEND = Path(__file__).resolve().parents[2]

    md_path = BACKEND / "temp/mineru_output/2e13b80d-fd1d-4fc9-b26d-9579c7a80654/auto/2e13b80d-fd1d-4fc9-b26d-9579c7a80654.md"
    desc_path = BACKEND / "temp/extractor_output/image_descriptions.json"
    output_path = BACKEND / "temp/extractor_output/paper_with_descriptions.md"

    append_descriptions(md_path, desc_path, output_path)
