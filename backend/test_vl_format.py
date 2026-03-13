"""
测试通义千问 VL 多模态 API 的图片格式
"""
import os
import base64
from pathlib import Path
from dashscope import Generation


def test_image_format():
    """测试不同的图片格式"""

    # 读取一张测试图片
    test_image_path = Path("./temp/mineru_output/293fe2c5-57fa-42d8-9b4e-05fbf22d38a9/auto/images/016abb087e699b1ecc301d1cff2574ea663fe85cc6ee478b73257c7d683774bf.jpg")

    if not test_image_path.exists():
        print(f"测试图片不存在: {test_image_path}")
        return

    # 读取并编码图片
    with open(test_image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("未设置 DASHSCOPE_API_KEY")
        return

    # 设置环境变量
    os.environ["DASHSCOPE_API_KEY"] = api_key

    # 同时也设置给 dashscope 模块
    import dashscope
    dashscope.api_key = api_key

    # 测试格式 1: 直接 base64
    print("\n=== 测试格式 1: 直接 base64 ===")
    try:
        response1 = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'text': '请描述这张图片'},
                    {'image': image_base64}
                ]
            }],
            max_tokens=100
        )
        print(f"状态码: {response1.status_code}")
        if response1.status_code == 200:
            print(f"✓ 成功! 响应: {response1.output.choices[0].message.content[:100]}")
        else:
            print(f"✗ 失败! 错误: {response1.message}")
    except Exception as e:
        print(f"✗ 异常: {e}")

    # 测试格式 2: data URL
    print("\n=== 测试格式 2: data URL ===")
    try:
        response2 = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'text': '请描述这张图片'},
                    {'image': f"data:image/jpeg;base64,{image_base64}"}
                ]
            }],
            max_tokens=100
        )
        print(f"状态码: {response2.status_code}")
        if response2.status_code == 200:
            print(f"✓ 成功! 响应: {response2.output.choices[0].message.content[:100]}")
        else:
            print(f"✗ 失败! 错误: {response2.message}")
    except Exception as e:
        print(f"✗ 异常: {e}")

    # 测试格式 3: URL (如果支持)
    print("\n=== 测试格式 3: base64 URL ===")
    try:
        response3 = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'text': '请描述这张图片'},
                    {'image': f"image/jpeg;base64,{image_base64}"}
                ]
            }],
            max_tokens=100
        )
        print(f"状态码: {response3.status_code}")
        if response3.status_code == 200:
            print(f"✓ 成功! 响应: {response3.output.choices[0].message.content[:100]}")
        else:
            print(f"✗ 失败! 错误: {response3.message}")
    except Exception as e:
        print(f"✗ 异常: {e}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_image_format()
