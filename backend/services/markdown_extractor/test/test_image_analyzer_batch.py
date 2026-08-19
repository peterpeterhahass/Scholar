"""
批量分析所有图片，为每张生成 description 并保存。

运行方式:
  cd backend/services/markdown_extractor/test
  python -X utf8 test_image_analyzer_batch.py
"""

import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
import os
load_dotenv(BACKEND_DIR / ".env")

from services.markdown_extractor.image_analyzer import ImageAnalyzer, save_results

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
IMAGES_BASE_DIR = BACKEND_DIR / "temp/mineru_output/2e13b80d-fd1d-4fc9-b26d-9579c7a80654/auto"
JSON_PATH = BACKEND_DIR / "temp/extractor_output/extracted_images.json"
OUTPUT_PATH = BACKEND_DIR / "temp/extractor_output/image_descriptions.json"

print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"图片基础目录: {IMAGES_BASE_DIR}")

analyzer = ImageAnalyzer(
    api_key=API_KEY,
    model_name="qwen-vl-plus",
    images_base_dir=str(IMAGES_BASE_DIR),
)

results = analyzer.analyze_all(JSON_PATH, output_path=OUTPUT_PATH)

print(f"\n{'=' * 70}")
print("全部完成，摘要:")
print(f"{'=' * 70}")
for i, r in enumerate(results, 1):
    desc_preview = r.description[:60].replace("\n", " ") if r.description else "(空)"
    print(f"  {i:2d}. {r.image_caption or r.image_path[:30]}")
    print(f"      {desc_preview}...")
