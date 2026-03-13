"""
测试前端到后端的完整流程
模拟前端调用 /api/generate-ppt-from-saved-content
"""
import asyncio
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx
from pathlib import Path


async def test_complete_flow():
    """完整流程测试"""
    print("=" * 60)
    print("完整流程测试：前端 -> 后端 -> PPT 生成")
    print("=" * 60)

    # 1. 确保有已保存的 PPT 内容
    print("\n1. 检查已保存的 PPT 内容")
    saved_content_dir = Path("./temp/saved_ppt_contents")

    if not saved_content_dir.exists():
        print("   ✗ 已保存内容目录不存在")
        return

    saved_files = list(saved_content_dir.glob("*.md"))
    if not saved_files:
        print("   ✗ 没有已保存的 PPT 内容")
        return

    # 使用第一个已保存的文件
    test_file = saved_files[0]
    task_id = test_file.stem.replace("_ppt_content", "")
    print(f"   ✓ 找到已保存内容: {test_file.name}")
    print(f"   ✓ 任务 ID: {task_id}")

    # 2. 调用 API（模拟前端请求）
    print("\n2. 模拟前端调用 API")
    print(f"   URL: POST http://localhost:8000/api/generate-ppt-from-saved-content?task_id={task_id}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/api/generate-ppt-from-saved-content",
                params={"task_id": task_id}
            )

            print(f"   状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"\n3. API 响应成功:")
                print(f"   ✓ status: {data['status']}")
                print(f"   ✓ task_id: {data['task_id']}")
                print(f"   ✓ download_url: {data['download_url']}")
                print(f"   ✓ slides_count: {data['metadata']['slides_count']}")
                print(f"   ✓ title: {data['metadata']['title']}")

                # 4. 验证 PPT 文件
                print("\n4. 验证生成的 PPT 文件")
                new_task_id = data['task_id']
                ppt_path = Path(f"./temp/ppt_output/{new_task_id}.pptx")

                if ppt_path.exists():
                    file_size = ppt_path.stat().st_size / 1024
                    print(f"   ✓ PPT 文件存在: {ppt_path}")
                    print(f"   ✓ 文件大小: {file_size:.2f} KB")
                    print(f"\n✓ 完整流程测试成功！")
                else:
                    print(f"   ✗ PPT 文件不存在: {ppt_path}")
            else:
                print(f"\n✗ API 调用失败:")
                print(f"   状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {error_data}")
                except:
                    print(f"   响应内容: {response.text}")

    except httpx.ConnectError:
        print("\n✗ 无法连接到后端服务")
        print("   请确保后端服务正在运行: cd backend && python main.py")
    except Exception as e:
        print(f"\n✗ 请求异常: {e}")
        import traceback
        traceback.print_exc()


async def test_saved_contents_list():
    """测试获取已保存内容列表"""
    print("\n" + "=" * 60)
    print("测试：获取已保存的 PPT 内容列表")
    print("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "http://localhost:8000/api/saved-ppt-contents"
            )

            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ API 调用成功:")
                print(f"   总数: {data['total']} 个已保存内容")

                for i, content in enumerate(data['contents'], 1):
                    print(f"\n   {i}. {content['title'][:50]}...")
                    print(f"      task_id: {content['task_id']}")
                    print(f"      幻灯片数: {content['slide_count']}")
                    print(f"      内容长度: {content['content_length']} 字符")
            else:
                print(f"\n✗ API 调用失败: {response.status_code}")

    except Exception as e:
        print(f"\n✗ 请求异常: {e}")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("前端到后端完整流程测试")
    print("=" * 60)

    # 测试 1: 获取已保存内容列表
    await test_saved_contents_list()

    # 测试 2: 完整流程
    await test_complete_flow()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
