"""
测试 image_analyzer.py，对第一张图片进行分析并保存结果。

运行方式:
  cd backend/services/markdown_extractor/test
  python -X utf8 test_image_analyzer.py
"""

import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# backend/ 目录  (test -> markdown_extractor -> services -> backend)
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from services.markdown_extractor.image_analyzer import ImageAnalyzer, save_results

# ── 从 .env 读取 API Key ──
from dotenv import load_dotenv
import os
load_dotenv(BACKEND_DIR / ".env")
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

IMAGES_BASE_DIR = BACKEND_DIR / "temp/mineru_output/2e13b80d-fd1d-4fc9-b26d-9579c7a80654/auto"
JSON_PATH = BACKEND_DIR / "temp/extractor_output/extracted_images.json"
OUTPUT_PATH = BACKEND_DIR / "temp/extractor_output/image_descriptions.json"

# ── 读取数据，先只测试第一张图片 ──
data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
print(f"共 {len(data)} 张图片，先测试第 1 张\n")
print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

analyzer = ImageAnalyzer(
    api_key=API_KEY,
    model_name="qwen-vl-plus",
    images_base_dir=str(IMAGES_BASE_DIR),
)

result = analyzer.analyze_single(data[0])

print(f"图片:   {result.image_path}")
print(f"标题:   {result.image_caption}")
print(f"章节:   {result.section_number} {result.section_title}")
print(f"\n{'=' * 70}")
print(result.description)
print("=" * 70)

# 保存单条测试结果
test_output = BACKEND_DIR / "temp/extractor_output/image_description_test.json"
save_results([result], test_output)
