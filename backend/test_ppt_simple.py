# -*- coding: utf-8 -*-
"""
简单测试 PPT 生成功能
"""
import asyncio
import sys
from pathlib import Path
from services.ppt_service import PPTService

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

async def test_ppt_generation():
    """测试 PPT 生成"""
    print("=" * 60)
    print("测试 PPT 生成功能")
    print("=" * 60)

    # 初始化服务
    ppt_service = PPTService(output_dir="./temp/ppt_output")
    print("[OK] PPT 服务初始化成功")

    # 使用测试的 Markdown 内容
    test_markdown = """# Attention Is All You Need

Ashish Vaswani Google Brain

Noam Shazeer Google Brain

## Abstract

The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.

## 1 Introduction

Recurrent neural networks have been firmly established as state of the art approaches.

## 2 Background

The goal of reducing sequential computation forms the foundation of the Extended Neural GPU.

## 3 Model Architecture

Most competitive neural sequence transduction models have an encoder-decoder structure.

## 4 Conclusion

We presented the Transformer, the first sequence transduction model based entirely on attention.
"""

    print(f"[INFO] 测试 Markdown 长度: {len(test_markdown)} 字符")
    print("\n开始生成 PPT...\n")

    # 生成 PPT
    result = await ppt_service.generate_ppt(
        markdown_content=test_markdown,
        task_id="test-123"
    )

    if result["status"] == "success":
        print("[SUCCESS] PPT 生成成功!")
        print(f"   [FILE] 文件路径: {result['ppt_path']}")
        print(f"   [INFO] 幻灯片数量: {result['slides_count']}")
        print(f"   [TITLE] 论文标题: {result['title']}")
        print(f"   [INFO] 章节数量: {result['sections_count']}")

        # 检查文件是否存在
        if Path(result['ppt_path']).exists():
            print(f"   [OK] 文件确实存在")
            print(f"   [SIZE] 文件大小: {Path(result['ppt_path']).stat().st_size} 字节")
        else:
            print(f"   [ERROR] 文件不存在!")
    else:
        print("[ERROR] PPT 生成失败!")
        print(f"   [ERROR] 错误信息: {result.get('error', '未知错误')}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ppt_generation())
