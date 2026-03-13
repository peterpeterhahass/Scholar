"""
最小化测试：只发送图片和简单文本
"""
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()

def test_minimal():
    """最小化测试"""

    api_key = os.getenv("DASHSCOPE_API_KEY")
    import dashscope
    dashscope.api_key = api_key

    test_image_path = Path("./temp/mineru_output/293fe2c5-57fa-42d8-9b4e-05fbf22d38a9/auto/images/016abb087e699b1ecc301d1cff2574ea663fe85cc6ee478b73257c7d683774bf.jpg")

    with open(test_image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')

    print("测试1: 单张图片 + 短文本")
    try:
        response = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'image': image_base64},
                    {'text': '描述这张图片'}
                ]
            }],
            max_tokens=50
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"成功: {response.output.choices[0].message.content}")
        else:
            print(f"失败: {response.message}")
            print(f"Code: {response.code}")
    except Exception as e:
        print(f"异常: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_minimal()
