"""
测试基于已保存内容生成 PPT 的功能
"""
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
import asyncio

# 模拟已保存的 PPT 内容
MOCK_SAVED_PPT_CONTENT = """# 论文标题 - 深度学习在图像识别中的应用

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
"""


async def test_generate_from_saved_content():
    """测试从已保存内容生成 PPT"""
    from services.ppt_service import PPTService

    print("=" * 60)
    print("测试：基于已保存内容生成 PPT")
    print("=" * 60)

    # 1. 创建模拟的已保存内容文件
    saved_content_dir = Path("./temp/saved_ppt_contents")
    saved_content_dir.mkdir(parents=True, exist_ok=True)

    test_task_id = "test_saved_001"
    saved_content_path = saved_content_dir / f"{test_task_id}_ppt_content.md"

    print(f"\n1. 创建模拟的已保存内容文件: {saved_content_path}")
    with open(saved_content_path, 'w', encoding='utf-8') as f:
        f.write(MOCK_SAVED_PPT_CONTENT)
    print("   ✓ 已保存内容文件创建成功")

    # 2. 读取已保存的内容
    print(f"\n2. 读取已保存的 PPT 内容")
    with open(saved_content_path, 'r', encoding='utf-8') as f:
        ppt_content = f.read()
    print(f"   ✓ 内容长度: {len(ppt_content)} 字符")

    # 3. 生成新的 PPT
    print(f"\n3. 基于已保存内容生成 PPT")
    ppt_service = PPTService()
    new_task_id = "test_new_001"

    ppt_result = await ppt_service.generate_ppt_from_notes(
        ppt_content,
        new_task_id,
        images_dir=None  # 测试时不使用真实图片
    )

    if ppt_result["status"] == "success":
        print(f"   ✓ PPT 生成成功:")
        print(f"     - 文件路径: {ppt_result['ppt_path']}")
        print(f"     - 幻灯片数量: {ppt_result['slides_count']}")
        print(f"     - 标题: {ppt_result['title']}")

        # 检查文件是否存在
        ppt_path = Path(ppt_result['ppt_path'])
        if ppt_path.exists():
            file_size = ppt_path.stat().st_size / 1024
            print(f"     - 文件大小: {file_size:.2f} KB")
            print(f"\n✓ 测试通过！")
        else:
            print(f"\n✗ 警告: PPT 文件不存在")
    else:
        print(f"\n✗ PPT 生成失败: {ppt_result.get('error', '未知错误')}")


async def test_api_endpoint():
    """测试 API 端点"""
    import httpx

    print("\n" + "=" * 60)
    print("测试：API 端点")
    print("=" * 60)

    # 1. 创建测试数据
    saved_content_dir = Path("./temp/saved_ppt_contents")
    test_task_id = "test_api_001"
    saved_content_path = saved_content_dir / f"{test_task_id}_ppt_content.md"

    print(f"\n1. 创建测试数据")
    with open(saved_content_path, 'w', encoding='utf-8') as f:
        f.write(MOCK_SAVED_PPT_CONTENT)
    print(f"   ✓ 已保存内容文件: {saved_content_path}")

    # 2. 调用 API
    print(f"\n2. 调用 API 端点: POST /api/generate-ppt-from-saved-content")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/generate-ppt-from-saved-content",
                params={"task_id": test_task_id},
                timeout=60.0
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ API 调用成功:")
                print(f"     - status: {data['status']}")
                print(f"     - task_id: {data['task_id']}")
                print(f"     - download_url: {data['download_url']}")
                print(f"     - slides_count: {data['metadata']['slides_count']}")
                print(f"\n✓ API 测试通过！")
            else:
                print(f"\n✗ API 调用失败:")
                print(f"     - 状态码: {response.status_code}")
                print(f"     - 响应: {response.text}")
    except Exception as e:
        print(f"\n✗ API 调用异常: {e}")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("已保存 PPT 内容生成功能测试")
    print("=" * 60)

    try:
        # 测试 1: 直接调用服务
        await test_generate_from_saved_content()

        # 测试 2: API 端点（需要后端服务运行）
        print("\n提示：如需测试 API 端点，请确保后端服务正在运行")
        print("运行命令: cd backend && python main.py")
        # await test_api_endpoint()

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

    except Exception as e:
        import traceback
        print(f"\n✗ 测试失败:")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
