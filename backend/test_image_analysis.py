"""
测试大模型对图片的实际分析
"""
import os
import asyncio
from pathlib import Path
from services.llm_service import LLMService

# 配置
API_KEY = os.getenv("DASHSCOPE_API_KEY", "your-api-key-here")
TASK_ID = "0be6ecd6-e7c5-4639-8b5b-3ce5489394cc"

async def test_image_analysis():
    """测试大模型对图片的分析能力"""
    print("=" * 70)
    print("测试大模型对图片的分析")
    print("=" * 70)

    # 读取 markdown 文件
    md_file = Path(f"./temp/mineru_output/{TASK_ID}/auto/{TASK_ID}.md")

    if not md_file.exists():
        print(f"错误: Markdown 文件不存在: {md_file}")
        return

    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # 创建 LLM 服务
    llm_service = LLMService(api_key=API_KEY, model_name="qwen-vl-plus")

    # 先检查图片提取
    images = llm_service._extract_images_from_markdown(markdown_content, TASK_ID)
    print(f"\n从 Markdown 中提取到 {len(images)} 张图片")

    if not images:
        print("没有提取到图片，无法测试")
        return

    # 调用大模型生成笔记（包含图片分析）
    print(f"\n正在调用大模型 {llm_service.model_name}...")
    print("(这可能需要几秒钟)\n")

    result = await llm_service.generate_notes(markdown_content, task_id=TASK_ID, temperature=0.7)

    if result["status"] == "success":
        notes = result["notes"]
        print(f"\n{'='*70}")
        print(f"生成成功！笔记长度: {len(notes)} 字符")
        print(f"使用 Token: {result.get('tokens_used', 0)}")
        print(f"{'='*70}\n")

        # 保存笔记到文件
        output_file = Path(f"./temp/test_image_analysis_output.md")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(notes)

        print(f"笔记已保存到: {output_file}")
        print("\n" + "="*70)
        print("笔记内容预览（前2000字符）:")
        print("="*70)
        print(notes[:2000])
        if len(notes) > 2000:
            print(f"\n... (还有 {len(notes)-2000} 个字符)")
        
        # 查找图片相关的描述
        print("\n" + "="*70)
        print("查找图片相关内容:")
        print("="*70)
        
        lines = notes.split('\n')
        image_sections = []
        current_section = []
        
        for line in lines:
            if '![](images/' in line:
                if current_section:
                    image_sections.append('\n'.join(current_section))
                    current_section = []
                current_section.append(line)
            elif current_section or any(img['name'] in line for img in images):
                current_section.append(line)
        
        if current_section:
            image_sections.append('\n'.join(current_section))
        
        if image_sections:
            print(f"\n找到 {len(image_sections)} 个包含图片或图片描述的段落:\n")
            for i, section in enumerate(image_sections[:3], 1):  # 只显示前3个
                print(f"[段落 {i}]")
                print(section[:500])
                if len(section) > 500:
                    print("...")
                print()

    else:
        print(f"\n错误: {result.get('error', '未知错误')}")
        if 'code' in result:
            print(f"错误代码: {result['code']}")

if __name__ == "__main__":
    asyncio.run(test_image_analysis())
