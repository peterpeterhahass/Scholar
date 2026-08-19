"""
使用大模型对 paper_with_descriptions.md 进行总结，生成学术笔记。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import dashscope
from dashscope import Generation


def _extract_text_from_response(response) -> str:
    """从 API 响应中提取文本"""
    content = response.output.choices[0].message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
            elif isinstance(item, str):
                texts.append(item)
        return ''.join(texts)
    return str(content)


def generate_notes(
    md_path: str | Path,
    api_key: str,
    model_name: str = "qwen-plus",
    output_path: Optional[str | Path] = None,
) -> str:
    """
    读取 paper_with_descriptions.md，调用大模型生成学术笔记。

    Args:
        md_path: paper_with_descriptions.md 文件路径
        api_key: DashScope API Key
        model_name: 模型名称，默认 qwen-plus（纯文本模型即可）
        output_path: 输出文件路径

    Returns:
        生成的学术笔记 Markdown 文本
    """
    os.environ["DASHSCOPE_API_KEY"] = api_key

    paper_content = Path(md_path).read_text(encoding="utf-8")

    prompt = f"""你是一名经验丰富的学术导师，请为以下论文生成通俗易懂的学术笔记，帮助读者快速理解论文的核心贡献。

【核心原则】
- 语言通俗易懂，用类比和直观解释帮助理解，避免堆砌术语
- 重点突出论文的主要方法和创新点，让读者一眼看出"这篇论文新在哪里"
- 每个关键概念先给直觉理解，再补充技术细节

【结构要求】
按以下结构输出，各部分以通俗语言阐述：

## 一句话总结
用一两句话概括论文做了什么、解决了什么问题。

## 研究背景与动机
- 这个问题为什么重要？
- 现有方法有什么不足？
- 论文想解决的核心痛点是什么？

## 核心创新点
用列表明确列出论文的主要创新/贡献（通常2-4点），每点说清：
- 创新是什么（用通俗语言）
- 为什么这个创新有价值

## 主要方法
这是笔记的重点，必须讲清楚：
- 整体思路：输入是什么，输出是什么，中间怎么处理
- 关键技术模块：每个模块做什么，模块之间如何配合
- 用流程化的语言描述：输入 → 处理步骤 → 输出
- 对关键设计决策解释"为什么要这样设计"

## 实验结果
- 在哪些数据集上做了验证
- 与哪些方法做了对比
- 主要结论：效果提升了多少，在哪些方面有明显优势
- 是否有消融实验证明各模块的有效性

## 总结与思考
- 论文的主要贡献总结
- 方法可能的局限性
- 对后续研究的启发

【图片处理规则】
1. 输入内容中包含图片路径（![](images/xxx.jpg)），图片路径后面紧跟了该图片的详细描述文字
2. 保留图片时必须遵守以下格式，在图片路径的正下方写上该图片的 caption（如 "Fig. 1. P4 architecture."），格式为：
   ![](images/xxx.jpg)
   *Fig. N. caption 内容*
3. 只有当你在笔记正文中提到了某张图片并讨论了其内容时，才保留该图片。不要出现"如Fig.X所示"但笔记中没有该图片的情况
4. 不要保留你没有在正文中讨论的图片
5. 不要修改图片路径，原样保留 ![](images/xxx.jpg) 格式
6. 图片应出现在与其内容对应的笔记段落附近，不要集中堆砌

【公式和表格的保留原则】
- 对理解方法核心思想有帮助的保留，无关的不保留
- 保留的公式必须配上通俗解释，说明公式的物理/直观含义
- 保留的公式和表格必须有对应的正文讨论，不能孤立出现

【输入】
{paper_content}

【输出要求】
- 结构清晰，重点突出创新点和方法
- 语言通俗易懂，像给同行讲论文一样自然
- 图片必须有 caption，且有正文讨论与之呼应
- 如果你提到"如图X所示"，则该图必须出现在笔记中
- 不要出现"该论文说..."这种空洞表达，要直接说具体内容"""

    messages = [{'role': 'user', 'content': prompt}]

    response = Generation.call(
        api_key=api_key,
        model=model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=8000,
        result_format='message',
    )

    if response.status_code == 200:
        notes = _extract_text_from_response(response)
    else:
        error_msg = getattr(response, 'message', '未知错误')
        raise RuntimeError(f"API 调用失败: {error_msg}")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(notes, encoding="utf-8")
        print(f"已保存学术笔记: {out} ({len(notes)} 字符)")

    return notes


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    from dotenv import load_dotenv

    BACKEND = Path(__file__).resolve().parents[2]
    load_dotenv(BACKEND / ".env")

    md_path = BACKEND / "temp/extractor_output/paper_with_descriptions.md"
    output_path = BACKEND / "temp/extractor_output/academic_notes.md"
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")

    notes = generate_notes(md_path, api_key, "qwen-plus", output_path)
    print(f"\n生成完毕，共 {len(notes)} 字符")
