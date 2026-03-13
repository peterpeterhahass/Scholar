"""
测试通义千问 VL API 使用 URL 格式
"""
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from dashscope import Generation
import http.server
import socketserver
import threading

load_dotenv()

def start_simple_server():
    """启动简单的 HTTP 服务器提供图片"""
    PORT = 8765
    Handler = http.server.SimpleHTTPRequestHandler

    # 切换到图片目录
    image_dir = Path("./temp/mineru_output/293fe2c5-57fa-42d8-9b4e-05fbf22d38a9/auto/images")
    os.chdir(image_dir)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"HTTP 服务器启动在端口 {PORT}")
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return PORT

def test_with_url():
    """使用 URL 格式测试"""

    # 设置 API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    import dashscope
    dashscope.api_key = api_key

    # 启动 HTTP 服务器
    port = start_simple_server()

    import time
    time.sleep(1)  # 等待服务器启动

    # 测试使用 URL
    image_url = f"http://localhost:{port}/016abb087e699b1ecc301d1cff2574ea663fe85cc6ee478b73257c7d683774bf.jpg"

    print(f"\n=== 使用 URL: {image_url} ===")
    try:
        response = Generation.call(
            model='qwen-vl-max',
            messages=[{
                'role': 'user',
                'content': [
                    {'image': image_url},
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

    input("按 Enter 停止服务器...")

if __name__ == "__main__":
    test_with_url()
