"""
测试大模型连接
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_llm():
    """测试通义千问 API 连接"""
    print("正在测试通义千问 API 连接...")

    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key or api_key == "your_dashscope_api_key_here":
        print("✗ 未配置 DASHSCOPE_API_KEY")
        print("\n请在 backend/.env 文件中设置有效的 API Key")
        print("获取 API Key: https://bailian.console.aliyun.com/")
        return False

    try:
        from dashscope import Generation
        print("✓ dashscope 导入成功")

        # 测试调用
        print("\n正在发送测试请求...")
        response = Generation.call(
            model="qwen-plus",
            prompt="你好",
            max_tokens=10
        )

        if response.status_code == 200:
            print("✓ API 连接成功")
            print(f"✓ 响应: {response.output.choices[0].message.content}")
            print(f"✓ 用量: {response.usage.total_tokens} tokens")
            return True
        else:
            print(f"✗ API 错误: {response.message}")
            return False

    except ImportError:
        print("✗ dashscope 未安装")
        print("\n请运行: pip install dashscope")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_llm())