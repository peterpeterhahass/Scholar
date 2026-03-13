"""
GAMMA API PPT 生成器
使用 GAMMA Generate API 自动创建演示文稿
"""

import requests
import time
import json

# GAMMA API 配置
API_KEY = "REDACTED"
BASE_URL = "https://public-api.gamma.app/v1.0"

# 代理设置（如果不需要代理，设置为 None）
PROXIES = {
    "http": "http://127.0.0.1:20809",
    "https": "http://127.0.0.1:20809"
}

# 如果不需要代理，将 PROXIES 设置为 None：
# PROXIES = None

# API 端点
GENERATE_URL = f"{BASE_URL}/generations"


def create_ppt(input_text, num_cards=10, language="zh-cn", export_format="pptx", theme_id=None, image_source="placeholder"):
    """
    创建 PPT 生成任务

    参数:
        input_text: 输入的内容/主题
        num_cards: 幻灯片数量 (1-75)
        language: 语言 ('zh-cn' 简体中文, 'zh-tw' 繁体中文, 'en' 英文)
        export_format: 导出格式 ('pptx' 或 'pdf')
        theme_id: 主题ID (可选)
        image_source: 图片来源 ('placeholder'=占位符, 'noImages'=无图片, 'aiGenerated'=AI生成)

    返回:
        generation_id: 生成任务ID
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY
    }

    # 构建请求体
    payload = {
        "inputText": input_text,
        "textMode": "generate",
        "format": "presentation",
        "numCards": num_cards,
        "cardSplit": "inputTextBreaks",
        "additionalInstructions": "Keep all text content exactly as provided. Do not modify, rephrase or add any text. Use the exact structure and headings from input. Process and display all image URLs from input. Use --- to separate slides.",
        "exportAs": export_format,
        "textOptions": {
            "amount": "detailed",
            "tone": "professional",
            "audience": "general",
            "language": language
        },
        "imageOptions": {
            "source": image_source
        },
        "cardOptions": {
            "dimensions": "16x9"
        },
        "sharingOptions": {
            "workspaceAccess": "view",
            "externalAccess": "noAccess"
        }
    }

    # 如果指定了主题ID，添加到请求中
    if theme_id:
        payload["themeId"] = theme_id

    try:
        print(f"🚀 正在创建 PPT 生成任务...")
        print(f"📝 主题: {input_text[:50]}...")
        print(f"📊 幻灯片数量: {num_cards}")
        if PROXIES:
            print(f"🔗 使用代理: {PROXIES['http']}")

        response = requests.post(GENERATE_URL, headers=headers, json=payload, proxies=PROXIES)
        response.raise_for_status()

        result = response.json()
        generation_id = result.get("generationId")

        print(f"✅ 任务创建成功! Generation ID: {generation_id}")
        return generation_id

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 错误: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"❌ 创建任务失败: {e}")
        return None


def get_themes():
    """
    获取工作区的主题列表

    返回:
        list: 主题列表
    """
    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json"
    }

    url = f"{BASE_URL}/themes"

    try:
        print(f"🔍 正在获取主题列表...")
        print(f"📡 API URL: {url}")
        response = requests.get(url, headers=headers, proxies=PROXIES, timeout=30)
        response.raise_for_status()
        result = response.json()

        # 智能解析：检查响应结构
        print(f"📦 API 响应结构:")
        if isinstance(result, list):
            print(f"   类型: 数组，长度: {len(result)}")
            themes = result
        elif isinstance(result, dict):
            print(f"   类型: 对象")
            print(f"   键: {list(result.keys())}")
            # 尝试不同的键名
            themes = result.get("themes") or result.get("data") or result.get("results") or []
        else:
            print(f"   未知类型: {type(result)}")
            themes = []

        if not themes:
            print("\n⚠️ 未找到主题")
            print("可能原因：")
            print("1. API 响应格式不匹配")
            print("2. 响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
            return []

        # 保存主题到文件
        themes_json_file = "gamma_themes.json"
        themes_txt_file = "gamma_themes.txt"

        # 保存 JSON 格式（完整数据）
        with open(themes_json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # 保存文本格式（简化版，方便阅读）
        with open(themes_txt_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("GAMMA 主题列表\n")
            f.write("=" * 80 + "\n\n")

            for i, theme in enumerate(themes, 1):
                theme_id = theme.get("id", "N/A")
                theme_name = theme.get("name", "未命名主题")
                theme_type = theme.get("type", "standard")

                # 颜色关键词
                color_keywords = theme.get("colorKeywords", [])
                # 风格关键词
                tone_keywords = theme.get("toneKeywords", [])

                f.write(f"{i}. {theme_name}\n")
                f.write(f"   ID: {theme_id}\n")
                f.write(f"   类型: {theme_type}\n")

                if color_keywords:
                    f.write(f"   配色: {', '.join(color_keywords[:5])}\n")

                if tone_keywords:
                    f.write(f"   风格: {', '.join(tone_keywords[:5])}\n")

                f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("使用方法：\n")
            f.write('  generate_ppt(..., theme_id="主题ID")\n')
            f.write("=" * 80 + "\n")

        print(f"\n✅ 找到 {len(themes)} 个主题")
        print(f"📁 已保存到：")
        print(f"   - {themes_json_file} (JSON格式，完整数据)")
        print(f"   - {themes_txt_file} (文本格式，方便阅读)")
        print()

        print("=" * 60)
        for i, theme in enumerate(themes, 1):
            theme_id = theme.get("id", "N/A")
            theme_name = theme.get("name", "未命名主题")
            print(f"{i}. {theme_name} (ID: {theme_id})")
        print("=" * 60)

        return themes

    except requests.exceptions.HTTPError as e:
        print(f"❌ 获取主题失败: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"❌ 获取主题出错: {e}")
        return None


def check_status(generation_id):
    """
    查询生成任务状态

    参数:
        generation_id: 生成任务ID

    返回:
        dict: 包含状态和结果的字典
    """
    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json"
    }

    url = f"{GENERATE_URL}/{generation_id}"

    try:
        response = requests.get(url, headers=headers, timeout=30, proxies=PROXIES)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ 查询状态失败: {e}")
        print(f"响应内容: {response.text}")
        return None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"❌ 网络连接错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 查询状态出错: {e}")
        return None


def wait_for_completion(generation_id, check_interval=10, timeout=600):
    """
    等待生成完成

    参数:
        generation_id: 生成任务ID
        check_interval: 检查间隔(秒)
        timeout: 超时时间(秒)

    返回:
        dict: 完成后的结果，或 None(超时/失败)
    """
    print(f"⏳ 等待生成完成...")
    print(f"💡 您也可以稍后使用 Generation ID: {generation_id} 查询结果")
    start_time = time.time()
    consecutive_errors = 0
    max_consecutive_errors = 5

    while time.time() - start_time < timeout:
        result = check_status(generation_id)

        if not result:
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                print(f"\n❌ 连续 {max_consecutive_errors} 次查询失败")
                print(f"💡 任务可能仍在后台处理，请稍后使用以下命令查询结果:")
                print(f"   python gamma_ppt_generator.py --check {generation_id}")
                return None
            print(f"⚠️ 网络不稳定，{check_interval} 秒后重试... ({consecutive_errors}/{max_consecutive_errors})")
            time.sleep(check_interval)
            continue

        # 重置错误计数
        consecutive_errors = 0

        status = result.get("status")
        print(f"📊 当前状态: {status}")

        if status == "completed":
            print(f"✅ 生成完成!")
            return result
        elif status == "failed":
            print(f"❌ 生成失败")
            return result
        elif status in ["pending", "processing"]:
            # 显示剩余积分
            credits = result.get("credits", {})
            if credits:
                print(f"   剩余积分: {credits.get('remaining', 'N/A')}")

        time.sleep(check_interval)

    print(f"⏰ 等待超时 ({timeout}秒)")
    print(f"💡 任务可能仍在后台处理，Generation ID: {generation_id}")
    return None


def generate_ppt(input_text, num_cards=10, language="zh-cn", export_format="pptx", theme_id=None, image_source="placeholder"):
    """
    完整的 PPT 生成流程

    参数:
        input_text: 输入的内容/主题
        num_cards: 幻灯片数量
        language: 语言
        export_format: 导出格式
        theme_id: 主题ID
        image_source: 图片来源 ('placeholder', 'noImages', 'aiGenerated')

    返回:
        dict: 包含 Gamma URL 和下载链接的结果
    """
    # 创建生成任务
    generation_id = create_ppt(input_text, num_cards, language, export_format, theme_id, image_source)

    if not generation_id:
        return None

    # 等待生成完成
    result = wait_for_completion(generation_id)

    if result and result.get("status") == "completed":
        print("\n" + "="*50)
        print("🎉 PPT 生成成功!")
        print("="*50)
        print(f"🌐 Gamma 在线链接: {result.get('gammaUrl')}")

        export_url = result.get('exportUrl')

        print(f"📥 下载链接: {export_url if export_url else '正在生成...'}")

        credits = result.get('credits', {})
        print(f"\n💰 积分使用情况:")
        print(f"   已扣除: {credits.get('deducted', 'N/A')}")
        print(f"   剩余: {credits.get('remaining', 'N/A')}")

        # 等待导出链接生成
        if not export_url:
            print("\n⏳ 等待导出链接生成...")
            wait_start = time.time()
            max_wait = 120  # 最多等待2分钟

            while time.time() - wait_start < max_wait:
                time.sleep(5)  # 每5秒查询一次
                check_result = check_status(generation_id)

                if check_result:
                    export_url = check_result.get('exportUrl')

                    if export_url:
                        print(f"✅ 导出链接已生成！")
                        result.update(check_result)  # 更新结果
                        break
                    else:
                        print(f"   仍在处理... ({int(time.time() - wait_start)}秒)")

        # 自动下载
        export_url = result.get('exportUrl')
        if export_url:
            print("\n" + "="*50)
            # 根据导出格式确定文件扩展名
            file_ext = "pdf" if export_format == "pdf" else "pptx"
            filename = f"gamma_ppt_{result.get('generationId', 'output')}.{file_ext}"
            download_file(export_url, filename)
        else:
            print("\n⚠️ 导出链接生成超时")
            print(f"💡 请稍后访问 Gamma 在线链接手动下载: {result.get('gammaUrl')}")

        print("="*50)

        return result

    return None


def download_file(url, filename):
    """
    下载文件到本地

    参数:
        url: 下载链接
        filename: 保存的文件名

    返回:
        bool: 下载是否成功
    """
    try:
        print(f"📥 正在下载: {filename}")
        response = requests.get(url, proxies=PROXIES, timeout=60, stream=True)
        response.raise_for_status()

        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))

        # 下载文件
        with open(filename, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 显示进度
                        percent = (downloaded / total_size) * 100
                        print(f"\r   进度: {percent:.1f}%", end='')

        print(f"\n✅ 下载完成: {filename}")
        return True

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False


# ==================== 使用示例 ====================

if __name__ == "__main__":
    import sys

    # 支持命令行参数获取主题列表
    if len(sys.argv) > 1 and sys.argv[1] == "--themes":
        get_themes()
        sys.exit(0)

    # 支持命令行参数查询已有任务
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if len(sys.argv) > 2:
            generation_id = sys.argv[2]
            print("=" * 60)
            print(f"查询任务状态: {generation_id}")
            print("=" * 60)

            result = check_status(generation_id)
            if result:
                status = result.get("status")
                print(f"📊 当前状态: {status}")

                if status == "completed":
                    print("\n" + "="*50)
                    print("🎉 PPT 生成成功!")
                    print("="*50)
                    print(f"🌐 Gamma 在线链接: {result.get('gammaUrl')}")
                    print(f"📥 PPTX 下载链接: {result.get('pptxUrl', '暂无')}")
                    print(f"📄 PDF 下载链接: {result.get('pdfUrl', '暂无')}")

                    credits = result.get('credits', {})
                    print(f"\n💰 积分使用情况:")
                    print(f"   已扣除: {credits.get('deducted', 'N/A')}")
                    print(f"   剩余: {credits.get('remaining', 'N/A')}")
                    print("="*50)
                elif status == "failed":
                    print(f"❌ 任务失败")
                else:
                    print(f"⏳ 任务仍在处理中...")
            else:
                print(f"❌ 无法查询任务状态")
        else:
            print("用法: python gamma_ppt_generator.py --check <generation_id>")
        sys.exit(0)

    # 示例 1: 使用详细内容生成 PPT
    print("=" * 60)
    print("示例 1: 人工智能的发展历程和应用前景")
    print("=" * 60)

    content = """
# 人工智能的发展历程和应用前景

---
## 人工智能概述

- 定义：模拟人类智能的技术系统
- 核心领域：机器学习、深度学习、自然语言处理
- 发展意义：改变人类生产生活方式

https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800
---


## 人工智能发展历程：诞生期（1950-1970年代）

- 1950年：图灵测试提出
- 1956年：达特茅斯会议，AI概念诞生
- 早期专家系统出现

https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800

---

## 人工智能发展历程：发展期（1980-2000年代）

- 机器学习算法兴起
- 神经网络研究复苏
- 深蓝战胜国际象棋冠军

https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800

---

## 人工智能发展历程：爆发期（2010年代至今）

- 2012年：AlexNet在ImageNet获胜
- 2016年：AlphaGo战胜李世石
- 2022年：ChatGPT引发AI革命

https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800

---

## 核心技术突破：深度学习

- 卷积神经网络（CNN）：图像识别
- 循环神经网络（RNN）：序列数据
- Transformer：大语言模型基础

https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800
"""

    result1 = generate_ppt(
        input_text=content,
        num_cards=13,
        language="zh-cn",
        export_format="pptx",
        #image_source="placeholder",
        image_source="noImages",
        theme_id="aurora"
    )

    
