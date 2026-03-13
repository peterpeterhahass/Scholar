"""
测试 MinerU 是否正常工作
"""
import asyncio


async def test_mineru():
    """测试 MinerU 安装和基本功能"""
    print("正在测试 MinerU...")

    try:
        from miner_u import MinerU
        print("✓ MinerU 导入成功")

        # 创建实例
        mineru = MinerU()
        print("✓ MinerU 实例创建成功")

        # 注意：实际测试需要一个 PDF 文件
        print("\n提示：MinerU 已安装并可以使用")
        print("要完整测试，请准备一个 PDF 文件并运行上传功能")

        return True

    except ImportError as e:
        print("✗ MinerU 未安装")
        print("\n请运行以下命令安装：")
        print("  pip install miner-u")
        print("\n或使用项目中的模拟模式进行开发")
        return False
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_mineru())