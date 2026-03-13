"""
测试新的基于笔记的 PPT 生成功能
"""

import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
from pathlib import Path
from services.llm_service import LLMService
from services.ppt_service import PPTService
from config import settings


# 模拟的笔记内容（用于测试解析逻辑）
MOCK_NOTES = """# 论文标题 - 深度学习在图像识别中的应用

## 作者信息
张三, 李四, 王五

## 目录
1. 问题定义
2. 研究动机
3. 核心方法
4. 关键创新
5. 实验结果
6. 总结评价

## 第1页：问题定义
**标题**：研究背景与核心问题
**要点**：
- 图像识别是计算机视觉的核心任务
- 传统方法在复杂场景下表现不佳
- 需要更强大的特征提取能力

## 第2页：研究动机
**标题**：为什么需要这项研究
**要点**：
- 深度学习能够自动学习特征
- 卷积神经网络在视觉任务中表现优异
- 现有方法在计算效率上还有提升空间

## 第3页：核心方法（上）
**标题**：方法框架概述
**要点**：
- 提出改进的卷积神经网络架构
- 引入注意力机制增强特征表达
- 采用多尺度融合策略
**图片**：![](images/architecture.png)

## 第4页：核心方法（下）
**标题**：关键技术创新
**要点**：
- 自适应卷积核设计
- 残差连接优化
- 动态权重分配机制

## 第5页：关键创新点
**标题**：主要贡献
**要点**：
- 首次将注意力机制引入该领域
- 计算效率提升30%
- 在多个数据集上达到SOTA性能

## 第6页：实验设置
**标题**：实验设计
**要点**：
- 数据集：ImageNet、COCO
- 对比方法：ResNet、VGG、Inception
- 评估指标：准确率、召回率、F1分数

## 第7页：实验结果
**标题**：主要实验结果
**要点**：
- 在ImageNet上准确率达到95.2%
- 比ResNet-50提升3.5个百分点
- 推理速度提升40%
**图片**：![](images/results.png)

## 第8页：总结评价
**标题**：优点与局限
**要点**：
- 优点：性能优异、计算高效
- 优点：易于集成到现有系统
- 局限：对GPU资源有一定要求
- 局限：小样本场景下表现一般

## 第9页：启发思考
**标题**：我的思考
**要点**：
- 可以尝试将该方法应用到视频分析
- 进一步优化模型以减少资源消耗
- 探索在移动设备上的部署方案
"""


async def test_ppt_parsing():
    """测试 PPT 内容解析"""
    print("=" * 60)
    print("测试 1: PPT 内容解析")
    print("=" * 60)

    ppt_service = PPTService()

    # 解析模拟的 PPT 内容
    structure = ppt_service.parse_ppt_content(MOCK_NOTES)

    print(f"\n✓ 解析完成:")
    print(f"  - 标题: {structure['title']}")
    print(f"  - 幻灯片数量: {len(structure['slides'])}")

    # 打印每张幻灯片的信息
    for i, slide in enumerate(structure['slides'], 1):
        print(f"\n  幻灯片 {i}:")
        print(f"    - 标题: {slide['title']}")
        print(f"    - 要点数量: {len(slide['points'])}")
        if slide['image']:
            print(f"    - 图片: {slide['image']}")

    return structure


async def test_ppt_creation(structure):
    """测试 PPT 文件创建"""
    print("\n" + "=" * 60)
    print("测试 2: PPT 文件创建")
    print("=" * 60)

    ppt_service = PPTService()
    task_id = "test_v2_001"

    # 创建 PPT (不是异步方法)
    result = ppt_service.create_ppt_from_content(structure, task_id)

    if result["status"] == "success":
        print(f"\n✓ PPT 创建成功:")
        print(f"  - 文件路径: {result['ppt_path']}")
        print(f"  - 幻灯片数量: {result['slides_count']}")
        print(f"  - 标题: {result['title']}")

        # 检查文件是否存在
        ppt_path = Path(result['ppt_path'])
        if ppt_path.exists():
            print(f"  - 文件大小: {ppt_path.stat().st_size / 1024:.2f} KB")
            print(f"\n✓ 文件验证通过！")
        else:
            print(f"\n✗ 警告: 文件不存在")
    else:
        print(f"\n✗ PPT 创建失败: {result['error']}")


async def test_notes_based_generation():
    """测试基于笔记的完整生成流程"""
    print("\n" + "=" * 60)
    print("测试 3: 基于笔记的完整生成流程")
    print("=" * 60)

    ppt_service = PPTService()
    task_id = "test_v2_002"

    # 使用笔记内容生成 PPT
    result = await ppt_service.generate_ppt_from_notes(MOCK_NOTES, task_id)

    if result["status"] == "success":
        print(f"\n✓ 基于笔记生成 PPT 成功:")
        print(f"  - 文件路径: {result['ppt_path']}")
        print(f"  - 幻灯片数量: {result['slides_count']}")
        print(f"  - 标题: {result['title']}")

        # 检查文件是否存在
        ppt_path = Path(result['ppt_path'])
        if ppt_path.exists():
            print(f"  - 文件大小: {ppt_path.stat().st_size / 1024:.2f} KB")
            print(f"\n✓ 完整流程测试通过！")
        else:
            print(f"\n✗ 警告: 文件不存在")
    else:
        print(f"\n✗ 生成失败: {result['error']}")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("新的 PPT 生成功能测试")
    print("=" * 60)

    try:
        # 测试 1: 解析 PPT 内容
        structure = await test_ppt_parsing()

        # 测试 2: 创建 PPT 文件
        await test_ppt_creation(structure)

        # 测试 3: 完整流程
        await test_notes_based_generation()

        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)

        print("\n使用说明:")
        print("1. 旧版接口（直接解析原始 Markdown）:")
        print("   - POST /api/upload-pdf-ppt")
        print("   - POST /api/generate-ppt-from-task")
        print("\n2. 新版接口（基于笔记生成，推荐）:")
        print("   - POST /api/upload-pdf-ppt-v2")
        print("   - POST /api/generate-ppt-from-notes")
        print("\n3. 新版优势:")
        print("   - 内容更精炼（经过 LLM 提炼）")
        print("   - 结构更清晰（适合演讲展示）")
        print("   - 质量更高（专门为 PPT 优化的内容）")

    except Exception as e:
        import traceback
        print(f"\n✗ 测试失败:")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
