import os
import shutil
from pathlib import Path
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json


class MinerUService:
    """MinerU 解析服务"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.executor = ThreadPoolExecutor(max_workers=4)
        os.makedirs(output_dir, exist_ok=True)

    async def parse_pdf(self, pdf_path: str, task_id: str) -> dict:
        """
        使用 MinerU 解析 PDF 文件，提取文本、图片、表格、公式等

        Args:
            pdf_path: PDF 文件路径
            task_id: 任务 ID

        Returns:
            解析结果，包含 Markdown 内容和资源文件路径
        """
        try:
            # 设置环境变量以允许加载模型（PyTorch 2.6+ 兼容性）
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

            # 导入 MinerU 相关模块
            from mineru.cli.common import aio_do_parse, read_fn
            from mineru.data.data_reader_writer import FileBasedDataWriter

            # 为每个任务创建独立的输出目录
            task_output_dir = os.path.join(self.output_dir, task_id)
            os.makedirs(task_output_dir, exist_ok=True)

            # 读取 PDF 文件
            pdf_file_name = os.path.splitext(os.path.basename(pdf_path))[0]
            pdf_bytes = read_fn(pdf_path)

            # 使用 MinerU 异步解析
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: asyncio.run(
                    aio_do_parse(
                        output_dir=self.output_dir,
                        pdf_file_names=[task_id],
                        pdf_bytes_list=[pdf_bytes],
                        p_lang_list=["en"],  # 默认英语，可根据需要调整
                        backend="pipeline",  # 使用 pipeline 模式
                        parse_method="auto",
                        formula_enable=True,  # 启用公式识别
                        table_enable=True,   # 启用表格识别
                        f_draw_layout_bbox=False,
                        f_draw_span_bbox=False,
                        f_dump_md=True,      # 生成 Markdown
                        f_dump_middle_json=False,
                        f_dump_model_output=False,
                        f_dump_orig_pdf=False,
                        f_dump_content_list=False,
                        f_make_md_mode="mm_markdown",  # 多模态 Markdown
                    )
                )
            )

            # MinerU 会创建 {output_dir}/{task_id}/auto/{task_id}.md
            # 以及 images 目录
            mineru_output_dir = os.path.join(self.output_dir, task_id, "auto")
            markdown_file = os.path.join(mineru_output_dir, f"{task_id}.md")
            images_dir = os.path.join(mineru_output_dir, "images")

            # 读取生成的 Markdown
            if os.path.exists(markdown_file):
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # 返回结果
                result = {
                    "status": "success",
                    "task_id": task_id,
                    "markdown_content": markdown_content,
                    "output_dir": mineru_output_dir,
                    "markdown_file": markdown_file,
                    "images_dir": images_dir if os.path.exists(images_dir) else None
                }

                # 统计资源文件
                if result["images_dir"]:
                    images = os.listdir(result["images_dir"])
                    result["image_count"] = len(images)
                    result["images"] = images

                return result
            else:
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error": f"Markdown 文件未生成: {markdown_file}"
                }

        except ImportError as e:
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"MinerU 依赖缺失: {str(e)}，请运行: pip install mineru[full]"
            }
        except Exception as e:
            return {
                "status": "error",
                "task_id": task_id,
                "error": f"MinerU 解析异常: {str(e)}"
            }

    async def parse_pdf_simple(self, pdf_path: str) -> str:
        """
        简单解析 PDF，返回 Markdown 内容

        Args:
            pdf_path: PDF 文件路径

        Returns:
            Markdown 内容
        """
        import uuid
        task_id = str(uuid.uuid4())
        result = await self.parse_pdf(pdf_path, task_id)

        if result["status"] == "success":
            return result["markdown_content"]
        else:
            raise Exception(f"PDF 解析失败: {result.get('error')}")

    def cleanup_task_files(self, task_id: str, keep_markdown: bool = True):
        """
        清理任务相关文件

        Args:
            task_id: 任务 ID
            keep_markdown: 是否保留 Markdown 文件，默认保留
        """
        task_dir = os.path.join(self.output_dir, task_id)
        if os.path.exists(task_dir):
            if keep_markdown:
                # 只保留 Markdown 文件和 images 目录
                auto_dir = os.path.join(task_dir, "auto")
                if os.path.exists(auto_dir):
                    # 保留 .md 文件和 images 目录
                    for item in os.listdir(auto_dir):
                        item_path = os.path.join(auto_dir, item)
                        if os.path.isfile(item_path) and not item.endswith('.md'):
                            os.remove(item_path)
                        elif os.path.isdir(item_path) and item != "images":
                            shutil.rmtree(item_path)
            else:
                # 删除整个任务目录
                shutil.rmtree(task_dir)

    def get_task_resources(self, task_id: str) -> dict:
        """
        获取任务的资源信息

        Args:
            task_id: 任务 ID

        Returns:
            资源信息字典
        """
        task_dir = os.path.join(self.output_dir, task_id, "auto")
        if not os.path.exists(task_dir):
            return {"exists": False}

        markdown_file = os.path.join(task_dir, f"{task_id}.md")
        images_dir = os.path.join(task_dir, "images")

        result = {
            "exists": True,
            "task_id": task_id,
            "markdown_file": markdown_file if os.path.exists(markdown_file) else None,
            "images_dir": images_dir if os.path.exists(images_dir) else None,
        }

        if result["images_dir"]:
            images = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))]
            result["images"] = images
            result["image_count"] = len(images)

        return result
