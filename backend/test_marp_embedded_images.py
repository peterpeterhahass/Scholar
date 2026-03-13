"""
测试 Marp 嵌入图片功能
"""
import asyncio
import sys
from pathlib import Path
from services.marp_service import MarpService

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_embedded_images():
    """测试生成带嵌入式图片的 PPT"""

    # 初始化服务
    marp_service = MarpService()

    # 测试文件路径
    markdown_path = "d:\\Project\\scholar\\backend\\temp\\marp_markdowns\\ce8fa506-2166-404d-a5cc-ed8cd1d0f392_marp.md"
    images_dir = Path("d:\\Project\\scholar\\backend\\temp\\marp_markdowns\\images")
    task_id = "test_embedded_images"

    print("=" * 60)
    print("测试 Marp 嵌入 Base64 图片功能")
    print("=" * 60)

    # 生成 PPT（默认嵌入图片）
    result = await marp_service.convert_marp_to_ppt(
        markdown_path=markdown_path,
        task_id=task_id,
        images_dir=images_dir,
        embed_images=True  # 嵌入图片
    )

    print("\n" + "=" * 60)
    print("转换结果:")
    print("=" * 60)
    print(f"状态: {result.get('status')}")
    print(f"PPT 路径: {result.get('ppt_path')}")
    print(f"图片已嵌入: {result.get('images_embedded', False)}")

    if result.get('status') == 'success':
        print("\n[成功] 图片已嵌入到 PPT 中，PPT 文件完全独立，可以分发！")
        print(f"\nPPT 文件大小: {Path(result['ppt_path']).stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"\n[失败] {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_embedded_images())
