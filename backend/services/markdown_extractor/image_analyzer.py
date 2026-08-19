"""
读取 extracted_images.json 中的每个 chunk，结合图片和上下文文本，
调用通义千问多模态模型生成详细的图片介绍。
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dashscope import MultiModalConversation


@dataclass
class AnalysisResult:
    """单张图片的分析结果"""
    image_path: str
    image_caption: str
    section_number: str
    section_title: str
    description: str = ""  # 模型生成的图片介绍


def _get_mime_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith('.png'):
        return 'image/png'
    elif name.endswith('.gif'):
        return 'image/gif'
    elif name.endswith('.webp'):
        return 'image/webp'
    return 'image/jpeg'


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


class ImageAnalyzer:
    """
    逐个 chunk 调用 Qwen-VL 多模态模型，对论文图片生成详细描述。

    用法::

        analyzer = ImageAnalyzer(
            api_key="sk-xxx",
            images_base_dir="temp/mineru_output/.../auto",
        )
        results = analyzer.analyze_all("temp/extractor_output/extracted_images.json")
    """

    def __init__(self, api_key: str, model_name: str = "qwen-vl-plus",
                 images_base_dir: str = ""):
        self.api_key = api_key
        self.model_name = model_name
        self.images_base_dir = Path(images_base_dir)
        os.environ["DASHSCOPE_API_KEY"] = api_key

    def analyze_all(self, json_path: str | Path,
                    output_path: Optional[str | Path] = None) -> List[AnalysisResult]:
        """
        读取 JSON，逐条分析，返回结果列表。
        如果指定 output_path 则保存结果。
        """
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        results: List[AnalysisResult] = []

        total = len(data)
        for i, chunk in enumerate(data, 1):
            image_path = chunk["image_path"]
            print(f"\n[{i}/{total}] 分析图片: {image_path}")

            result = self._analyze_chunk(chunk)
            results.append(result)
            print(f"  生成描述 ({len(result.description)} 字符)")

        if output_path:
            save_results(results, output_path)

        return results

    def analyze_single(self, chunk: dict) -> AnalysisResult:
        """分析单个 chunk"""
        return self._analyze_chunk(chunk)

    def _analyze_chunk(self, chunk: dict) -> AnalysisResult:
        image_rel_path = chunk["image_path"]
        image_full_path = self.images_base_dir / image_rel_path

        # 读取图片
        if not image_full_path.exists():
            print(f"  警告: 图片不存在 {image_full_path}")
            return AnalysisResult(
                image_path=image_rel_path,
                image_caption=chunk.get("image_caption", ""),
                section_number=chunk.get("section_number", ""),
                section_title=chunk.get("section_title", ""),
                description=f"[图片文件不存在: {image_full_path}]",
            )

        with open(image_full_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        mime = _get_mime_type(image_rel_path)
        prompt_text = self._build_prompt(chunk)

        # 多模态消息：图片 + 文本
        content = [
            {'image': f"data:{mime};base64,{img_base64}"},
            {'text': prompt_text},
        ]
        messages = [{'role': 'user', 'content': content}]

        try:
            response = MultiModalConversation.call(
                api_key=self.api_key,
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
            )

            if response.status_code == 200:
                description = _extract_text_from_response(response)
            else:
                error_msg = getattr(response, 'message', '未知错误')
                print(f"  API 错误: {error_msg}")
                description = f"[API 调用失败: {error_msg}]"

        except Exception as e:
            print(f"  异常: {e}")
            description = f"[分析异常: {e}]"

        return AnalysisResult(
            image_path=image_rel_path,
            image_caption=chunk.get("image_caption", ""),
            section_number=chunk.get("section_number", ""),
            section_title=chunk.get("section_title", ""),
            description=description,
        )

    @staticmethod
    def _build_prompt(chunk: dict) -> str:
        """拼装发送给模型的 prompt"""
        parts = []

        parts.append("你是一个专业的学术论文图表分析专家。请仔细观察这张来自学术论文的图片，结合下方提供的上下文信息，生成一段详细的图片介绍。")
        parts.append("")
        parts.append("要求：")
        parts.append("1. 详细描述图片中展示的所有内容，包括文字、数据、结构、箭头、标签等")
        parts.append("2. 说明图片在论文中所表达的核心含义和学术观点")
        parts.append("3. 如果是架构图，说明各组件的名称、功能和数据流向")
        parts.append("4. 如果是流程图，按步骤说明流程的逻辑")
        parts.append("5. 如果是实验结果图/表，分析数据趋势、对比关系和关键发现")
        parts.append("6. 如果是示意图，说明其展示的原理或概念")
        parts.append("7. 用清晰、专业的学术语言描述，确保读者不看图也能理解图的内容")
        parts.append("")

        if chunk.get("image_caption"):
            parts.append(f"【图片标题】{chunk['image_caption']}")
            parts.append("")

        sec_label = f"{chunk.get('section_number', '')} {chunk.get('section_title', '')}".strip()
        if sec_label:
            parts.append(f"【所在章节】{sec_label}")
            parts.append("")

        if chunk.get("section_content"):
            parts.append("【所在章节内容】")
            parts.append(chunk["section_content"])
            parts.append("")

        parent_content = chunk.get("parent_content", "")
        if parent_content:
            parent_label = f"{chunk.get('parent_number', '')} {chunk.get('parent_title', '')}".strip()
            parts.append(f"【父章节 {parent_label} 内容】")
            parts.append(parent_content)
            parts.append("")

        parts.append("请基于以上信息，生成对该图片的详细介绍：")
        return "\n".join(parts)


def save_results(results: List[AnalysisResult], output_path: str | Path) -> None:
    """保存分析结果到 JSON"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            "image_path": r.image_path,
            "image_caption": r.image_caption,
            "section_number": r.section_number,
            "section_title": r.section_title,
            "description": r.description,
        }
        for r in results
    ]
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n已保存分析结果: {output_path} ({len(results)} 条)")
