"""
测试PPT左文字右图片布局功能
"""

import asyncio
from pathlib import Path
from services.ppt_service import PPTService

# 测试用的笔记内容
TEST_NOTES = '''
# 深度学习模型优化研究

## 第1页：研究背景

**标题**：研究背景

- 深度学习在各领域广泛应用
- 模型规模持续增长
- 推理效率成为关键问题

**图片**：![](images/deep_learning.png)

## 第2页：现有方法

**标题**：现有方法的局限性

- 模型压缩技术
  - 量化：降低精度
  - 剪枝：移除冗余连接
- 知识蒸馏：teacher-student框架
- 存在的问题：精度损失较大

## 第3页：方法概述

**标题**：我们的方法

- 自适应量化策略
- 动态剪枝算法
- 端到端优化框架

**图片**：![](images/method_framework.png)

## 第4页：实验结果

**标题**：实验对比

| 模型 | 精度 | 速度 |
|------|------|------|
| ResNet-50 | 76.15% | 1x |
| Ours | 76.02% | 2.3x |

**图片**：![](images/results.png)

## 第5页：结论

**标题**：未来工作

- 扩展到更多模型架构
- 硬件加速优化
- 自动化搜索空间设计
'''


async def main():
    print("=" * 60)
    print("测试PPT左文字右图片布局功能")
    print("=" * 60)

    # 创建PPT服务实例
    ppt_service = PPTService()

    # 解析笔记内容
    print("\n1. 解析笔记内容...")
    structure = ppt_service.parse_ppt_content(TEST_NOTES)

    print(f"   标题: {structure['title']}")
    print(f"   幻灯片数量: {len(structure['slides'])}")

    for i, slide in enumerate(structure['slides'], 1):
        has_image = "[Y]" if slide['image'] else "[N]"
        print(f"   Slide {i}: {slide['title'][:30]} | Points: {len(slide['points'])} | Image: {has_image}")
        if slide['image']:
            print(f"              -> Image file: {slide['image']}")

    # 生成PPT（不带图片）
    print("\n2. 生成PPT文件...")
    task_id = "test_layout_001"
    result = await ppt_service.generate_ppt_from_notes(
        notes_content=TEST_NOTES,
        task_id=task_id,
        images_dir=None  # 暂时不使用图片
    )

    if result["status"] == "success":
        print(f"   [OK] PPT generated successfully!")
        print(f"   File path: {result['ppt_path']}")
        print(f"   Slides count: {result['slides_count']}")
        print(f"   Title: {result['title']}")

        # 检查文件是否存在
        ppt_file = Path(result['ppt_path'])
        if ppt_file.exists():
            file_size = ppt_file.stat().st_size
            print(f"   File size: {file_size:,} bytes")
        else:
            print("   [WARN] File does not exist!")
    else:
        print(f"   [ERROR] PPT generation failed: {result.get('error')}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
