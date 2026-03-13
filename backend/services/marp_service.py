"""
Marp 服务
使用 Marp CLI 将 Markdown 转换为 PPT
"""

import os
import re
import subprocess
import base64
from pathlib import Path
from typing import Dict, Optional


class MarpService:
    """Marp 转换服务"""

    def __init__(self, output_dir: str = "./temp/marp_output"):
        """
        初始化 Marp 服务

        Args:
            output_dir: PPT 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _image_to_base64(self, image_path: Path) -> Optional[str]:
        """
        将图片转换为 Base64 编码的 Data URI

        Args:
            image_path: 图片文件路径

        Returns:
            Base64 编码的 Data URI 字符串，如果失败返回 None
        """
        try:
            # 读取图片文件
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            # 转换为 base64
            base64_str = base64.b64encode(img_data).decode('utf-8')

            # 获取 MIME 类型
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp'
            }.get(image_path.suffix.lower(), 'image/jpeg')

            # 返回 Data URI
            return f"data:{mime_type};base64,{base64_str}"

        except Exception as e:
            print(f"[ERROR] Failed to convert image to Base64 {image_path}: {e}")
            return None

    def _convert_markdown_images_to_base64(
        self,
        markdown_content: str,
        images_dir: Path
    ) -> str:
        """
        将 Markdown 中的图片路径转换为 Base64 Data URI

        支持两种格式:
        1. ![](images/xxx.jpg)
        2. <img src="images/xxx.jpg" />

        Args:
            markdown_content: Markdown 内容
            images_dir: 图片目录

        Returns:
            转换后的 Markdown 内容
        """
        print(f"[DEBUG] 开始转换图片，images_dir: {images_dir}, exists: {images_dir.exists()}")

        if not images_dir.exists():
            print(f"[ERROR] 图片目录不存在: {images_dir}")
            return markdown_content

        # 列出所有图片文件
        try:
            img_files = list(images_dir.iterdir())
            print(f"[DEBUG] 图片目录包含 {len(img_files)} 个文件")
            for f in img_files[:5]:  # 只打印前5个
                print(f"[DEBUG]   - {f.name}")
        except Exception as e:
            print(f"[ERROR] 列出图片文件失败: {e}")
            return markdown_content

        new_content = markdown_content

        # 1. 先处理 <img src="images/xxx.jpg" /> 格式
        def replace_img_tag(match):
            img_filename = match.group(1).strip()

            # 去除可能包含的尺寸参数
            if '=' in img_filename:
                img_filename = img_filename.split('=')[0].strip()

            print(f"[DEBUG] 处理 <img> 标签: {img_filename}")
            img_path = images_dir / img_filename

            if not img_path.exists():
                print(f"[SKIP] Image not found: {img_path}")
                return match.group(0)  # 保持原样

            # 转换为 Base64
            base64_uri = self._image_to_base64(img_path)
            if base64_uri:
                print(f"[OK] Converted <img> tag: {img_filename}, base64 length: {len(base64_uri)}")
                return f'<img src="{base64_uri}" />'
            else:
                print(f"[FAIL] Failed to convert: {img_filename}")
                return match.group(0)  # 转换失败，保持原样

        # 匹配 <img src="images/xxx.jpg" /> 或 <img src="images/xxx.jpg">
        img_pattern = r'<img\s+src="(images/[^"]+)"\s*/?>'
        matches = re.findall(img_pattern, new_content)
        print(f"[DEBUG] 找到 {len(matches)} 个 <img> 标签")
        new_content = re.sub(img_pattern, replace_img_tag, new_content)

        # 2. 再处理 ![](images/xxx.jpg) 格式（向后兼容）
        def replace_markdown_img(match):
            img_filename = match.group(2).strip()

            # 处理可能包含的尺寸参数
            if '=' in img_filename:
                img_filename = img_filename.split('=')[0].strip()

            print(f"[DEBUG] 处理 ![] 格式: {img_filename}")
            img_path = images_dir / img_filename

            if not img_path.exists():
                print(f"[SKIP] Image not found: {img_path}")
                return match.group(0)  # 保持原样

            # 转换为 Base64
            base64_uri = self._image_to_base64(img_path)
            if base64_uri:
                print(f"[OK] Converted ![]: {img_filename}, base64 length: {len(base64_uri)}")
                return f'![]({base64_uri})'
            else:
                print(f"[FAIL] Failed to convert: {img_filename}")
                return match.group(0)  # 转换失败，保持原样

        # 匹配 ![](images/xxx.jpg) 或 ![](./images/xxx.jpg) 或 ![](/images/xxx.jpg) 格式
        md_pattern = r'!\[\]\((\.?/)?images/([^)]+?)(?:\s*=\s*[\d%]+x)?\s*\)'
        matches = re.findall(md_pattern, new_content)
        print(f"[DEBUG] 找到 {len(matches)} 个 ![] 格式图片")
        new_content = re.sub(md_pattern, replace_markdown_img, new_content)

        return new_content

    def check_marp_installed(self) -> bool:
        """
        检查 Marp CLI 是否已安装

        Returns:
            是否已安装
        """
        try:
            # Windows 上需要使用 shell=True 或 marp.cmd
            if os.name == "nt":
                result = subprocess.run(
                    "marp.cmd --version",
                    capture_output=True,
                    timeout=10,
                    shell=True,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                result = subprocess.run(
                    ["marp", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def convert_marp_to_ppt(
        self,
        markdown_path: str,
        task_id: str,
        images_dir: Optional[Path] = None,
        embed_images: bool = True
    ) -> Dict:
        """
        使用 Marp 将 Markdown 转换为 PPT

        Args:
            markdown_path: Markdown 文件路径
            task_id: 任务 ID
            images_dir: 图片目录（用于嵌入或复制图片）
            embed_images: 是否将图片以 Base64 形式嵌入到 PPT 中（默认 True）

        Returns:
            转换结果和 PPT 文件路径
        """
        try:
            # 检查 Marp 是否安装
            if not self.check_marp_installed():
                return {
                    "status": "error",
                    "error": "Marp CLI 未安装，请先安装: npm install -g @marp-team/marp-cli"
                }

            markdown_path = Path(markdown_path)
            if not markdown_path.exists():
                return {
                    "status": "error",
                    "error": f"Markdown 文件不存在: {markdown_path}"
                }

            # 读取 Markdown 内容
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # 如果需要嵌入图片且有图片目录
            if embed_images and images_dir and images_dir.exists():
                print("开始将图片转换为 Base64 并嵌入到 Markdown...")
                markdown_content = self._convert_markdown_images_to_base64(
                    markdown_content,
                    images_dir
                )
                print("图片嵌入完成！")

                # 创建新的 Markdown 文件（带嵌入式图片）
                embedded_markdown_path = markdown_path.parent / f"{markdown_path.stem}_embedded.md"
                with open(embedded_markdown_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                # 使用嵌入图片的 Markdown 文件
                markdown_path = embedded_markdown_path

            elif images_dir and images_dir.exists():
                # 不嵌入图片，复制图片到 Markdown 同目录
                images_output_dir = markdown_path.parent / "images"
                images_output_dir.mkdir(exist_ok=True)

                # 复制所有图片
                import shutil
                for img_file in images_dir.iterdir():
                    if img_file.is_file():
                        shutil.copy2(img_file, images_output_dir / img_file.name)

                print(f"已复制 {len(list(images_dir.iterdir()))} 张图片到 {images_output_dir}")

            # 输出 PPT 路径
            output_path = self.output_dir / f"{task_id}.pptx"

            # 构建 Marp 命令
            # Windows 上使用 marp.cmd 并通过 shell 执行
            # 注意：--images 和 --pptx 是互斥的，不能同时使用
            # 将路径转换为正斜杠格式，避免 shell 转义问题
            if os.name == "nt":
                cmd_str = f'marp.cmd "{markdown_path.resolve().as_posix()}" --pptx -o "{output_path.resolve().as_posix()}" --allow-local-files'
                print(f"执行 Marp 命令: {cmd_str}")
                result = subprocess.run(
                    cmd_str,
                    capture_output=True,
                    timeout=60,
                    shell=True,
                    cwd=str(markdown_path.parent),  # 设置工作目录为 Markdown 文件所在目录
                    encoding='utf-8',
                    errors='replace'  # 遇到编码错误时替换而不是报错
                )
            else:
                cmd = [
                    "marp",
                    str(markdown_path),
                    "--pptx",
                    "-o", str(output_path),
                    "--allow-local-files"
                ]
                print(f"执行 Marp 命令: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(markdown_path.parent)
                )

            if result.returncode != 0:
                print(f"Marp 错误输出: {result.stderr}")
                return {
                    "status": "error",
                    "error": f"Marp 转换失败: {result.stderr}"
                }

            # 检查输出文件是否存在
            if not output_path.exists():
                return {
                    "status": "error",
                    "error": f"PPT 文件未生成: {output_path}"
                }

            print(f"Marp 转换成功: {output_path}")

            # 清理临时嵌入图片的 Markdown 文件
            if embed_images and 'embedded_markdown_path' in locals():
                try:
                    embedded_markdown_path.unlink()
                    print(f"已清理临时文件: {embedded_markdown_path}")
                except Exception as e:
                    print(f"清理临时文件失败: {e}")

            return {
                "status": "success",
                "ppt_path": str(output_path),
                "markdown_path": str(markdown_path),
                "images_embedded": embed_images and images_dir is not None
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Marp 转换超时（60秒）"
            }
        except Exception as e:
            import traceback
            print(f"Marp 转换异常:\n{traceback.format_exc()}")
            return {
                "status": "error",
                "error": f"Marp 转换失败: {str(e)}"
            }

    def cleanup_task_files(self, task_id: str):
        """
        清理任务相关文件

        Args:
            task_id: 任务 ID
        """
        try:
            ppt_file = self.output_dir / f"{task_id}.pptx"
            if ppt_file.exists():
                ppt_file.unlink()
        except Exception as e:
            print(f"清理 Marp 文件失败: {e}")
