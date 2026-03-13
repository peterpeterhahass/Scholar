"""
测试通义千问 VL API 的正确调用方式
参考官方文档
"""
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()

def test_simple_call():
    """最简单的测试"""

    # 设置 API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("未设置 DASHSCOPE_API_KEY")
        return

    import dashscope
    dashscope.api_key = api_key

    # 测试图片
    test_image_path = Path("./temp/mineru_output/293fe2c5-57fa-42d8-9b4e-05fbf22d38a9/auto/images/016abb087e699b1ecc301d1cff2574ea663fe85cc6ee478b73257c7d683774bf.jpg")

    if not test_image_path.exists():
        print(f"测试图片不存在: {test_image_path}")
        return

    # 读取并编码图片
    with open(test_image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')

    print(f"图片 base64 长度: {len(image_base64)}")
    print(f"前100个字符: {image_base64[:100]}")

    # 方式1: 官方文档示例 - 直接传 base64
    print("\n=== 方式1: 直接传 base64 字符串 ===")
    try:
        response = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'image': image_base64},
                    {'text': '这张图片是什么？'}
                ]
            }],
            max_tokens=100
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"成功: {response.output.choices[0].message.content}")
        else:
            print(f"失败: {response.message}")
    except Exception as e:
        print(f"异常: {e}")

    # 方式2: 使用 data URL
    print("\n=== 方式2: data:image/jpeg;base64,xxx ===")
    try:
        response = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'image': f"data:image/jpeg;base64,{image_base64}"},
                    {'text': '这张图片是什么？'}
                ]
            }],
            max_tokens=100
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"成功: {response.output.choices[0].message.content}")
        else:
            print(f"失败: {response.message}")
    except Exception as e:
        print(f"异常: {e}")

if __name__ == "__main__":
    test_simple_call()
