"""
测试多模态图片分析是否正常工作
"""
import os
from pathlib import Path
from services.llm_service import LLMService

# 配置
API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
TASK_ID = "0be6ecd6-e7c5-4639-8b5b-3ce5489394cc"

def test_image_extraction():
    """测试图片提取功能"""
    print("=" * 60)
    print("测试 1: 图片提取功能")
    print("=" * 60)

    # 读取 markdown 文件
    md_file = Path(f"./temp/mineru_output/{TASK_ID}/auto/{TASK_ID}.md")

    if not md_file.exists():
        print(f"❌ Markdown 文件不存在: {md_file}")
        return

    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 创建 LLM 服务
    llm_service = LLMService(api_key=API_KEY, model_name="qwen-vl-plus")

    # 提取图片
    images = llm_service._extract_images_from_markdown(markdown_content, TASK_ID)

    print(f"\n✅ Markdown 文件大小: {len(markdown_content)} 字符")
    print(f"✅ 提取到 {len(images)} 张图片")

    if images:
        print("\n📸 图片列表:")
        for i, img in enumerate(images[:5], 1):
            print(f"  {i}. {img['name']}")
            print(f"     路径: {img['path']}")
            print(f"     Base64 长度: {len(img['base64'])} 字符")

        if len(images) > 5:
            print(f"  ... 还有 {len(images) - 5} 张图片")
    else:
        print("⚠️  没有提取到图片！")

    return len(images) > 0

def test_multimodal_call():
    """测试多模态调用"""
    print("\n" + "=" * 60)
    print("测试 2: 多模态消息构建")
    print("=" * 60)

    # 读取 markdown 文件
    md_file = Path(f"./temp/mineru_output/{TASK_ID}/auto/{TASK_ID}.md")

    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 创建 LLM 服务
    llm_service = LLMService(api_key=API_KEY, model_name="qwen-vl-plus")

    # 提取图片
    images = llm_service._extract_images_from_markdown(markdown_content, TASK_ID)

    if not images:
        print("❌ 没有图片，无法测试多模态调用")
        return False

    # 限制为 3 张图片用于测试
    test_images = images[:3]

    # 构建多模态消息
    multimodal_message = llm_service._build_multimodal_message(
        "测试内容",
        test_images
    )

    print(f"\n✅ 多模态消息构建成功")
    print(f"   消息包含 {len(multimodal_message)} 个部分")
    print(f"   - 1 个文本提示")
    print(f"   - {len(test_images)} 个图片 (data URL)")

    return True

def main():
    """主测试函数"""
    print("\n🧪 多模态图片分析测试")
    print(f"任务 ID: {TASK_ID}\n")

    # 测试 1: 图片提取
    has_images = test_image_extraction()

    if not has_images:
        print("\n❌ 图片提取失败，无法继续测试")
        return

    # 测试 2
    test_multimodal_call()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
