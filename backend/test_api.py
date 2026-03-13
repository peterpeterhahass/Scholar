"""
测试 API 脚本
用于测试任务列表和从已提取数据生成笔记的接口
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def list_tasks():
    """列出所有已提取的任务"""
    print("\n=== 获取任务列表 ===")
    response = requests.get(f"{BASE_URL}/api/tasks")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ 总任务数: {data['total_tasks']}")

        for task in data['tasks'][:5]:  # 只显示前5个
            print(f"\n任务 ID: {task['task_id']}")
            print(f"  - Markdown 存在: {task['markdown_exists']}")
            print(f"  - Markdown 大小: {task.get('markdown_size', 0)} bytes")
            print(f"  - 图片目录存在: {task['images_dir_exists']}")
            if 'image_count' in task:
                print(f"  - 图片数量: {task['image_count']}")

        return data['tasks']
    else:
        print(f"✗ 失败: {response.status_code}")
        print(response.text)
        return []


def generate_notes_from_task(task_id: str):
    """使用已提取的任务生成笔记"""
    print(f"\n=== 从任务 {task_id} 生成笔记 ===")
    response = requests.post(
        f"{BASE_URL}/api/generate-notes-from-task",
        params={"task_id": task_id}
    )

    if response.status_code == 200:
        data = response.json()
        print("✓ 笔记生成成功!")
        print(f"\n元数据:")
        print(f"  - 来源: {data['metadata']['source']}")
        print(f"  - Markdown 大小: {data['metadata']['markdown_size']} bytes")
        print(f"  - 模型: {data['metadata']['model']}")
        print(f"  - Token 使用: {data['metadata']['tokens_used']}")

        # 保存笔记到文件
        output_file = f"notes_{task_id[:8]}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(data['notes'])
        print(f"\n笔记已保存到: {output_file}")

        return data['notes']
    else:
        print(f"✗ 失败: {response.status_code}")
        print(response.text)
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("PDF 笔记生成 API - 测试工具")
    print("=" * 60)

    # 1. 列出所有任务
    tasks = list_tasks()

    if not tasks:
        print("\n没有找到已提取的任务。请先上传 PDF 文件。")
        return

    # 2. 选择第一个任务生成笔记
    first_task_id = tasks[0]['task_id']
    print(f"\n正在使用第一个任务生成笔记: {first_task_id}")

    notes = generate_notes_from_task(first_task_id)

    if notes:
        print("\n" + "=" * 60)
        print("笔记预览 (前500字符):")
        print("=" * 60)
        print(notes[:500])
        if len(notes) > 500:
            print("...")
        print("=" * 60)


if __name__ == "__main__":
    main()
