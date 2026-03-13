# PDF 笔记生成器 - 使用指南

## 功能说明

本项目支持两种方式生成笔记：

### 1. 上传新 PDF（首次提取）
- 点击上传区域选择 PDF 文件
- MinerU 自动提取文本、图片、表格、公式
- 大模型生成专业学术笔记
- **耗时**：30秒 - 5分钟（取决于PDF复杂度）

### 2. 使用已提取文档（快速生成）⭐
- 点击顶部 "📋 查看已提取文档" 按钮
- 选择已提取的任务
- 直接生成笔记（无需重复提取）
- **耗时**：5-15秒

## 推荐工作流程

### 开发/测试阶段：
1. **首次上传** PDF（使用 MinerU 提取）
2. **查看已提取文档**列表
3. **反复生成笔记**（调整提示词或参数时）
4. 对比不同版本的笔记质量

### 正常使用：
1. 上传新 PDF → 生成笔记
2. 保存笔记结果
3. 需要重新生成时，使用"已提取文档"功能

## API 接口

### 1. 上传 PDF
```bash
POST /api/upload-pdf
Content-Type: multipart/form-data

# 参数
file: PDF 文件
```

### 2. 查看任务列表
```bash
GET /api/tasks

# 返回
{
  "status": "success",
  "total_tasks": 3,
  "tasks": [
    {
      "task_id": "xxx-xxx-xxx",
      "markdown_exists": true,
      "markdown_size": 15234,
      "images_dir_exists": true,
      "image_count": 5
    }
  ]
}
```

### 3. 从任务生成笔记
```bash
POST /api/generate-notes-from-task?task_id=xxx-xxx-xxx

# 返回
{
  "status": "success",
  "task_id": "xxx-xxx-xxx",
  "notes": "# 笔记内容...",
  "metadata": {
    "source": "existing_task",
    "markdown_size": 15234,
    "model": "qwen-plus",
    "tokens_used": 1234
  }
}
```

## 测试脚本

运行测试脚本快速测试：
```bash
cd backend
python test_api.py
```

## 数据存储

### 目录结构
```
backend/temp/mineru_output/
  └── {task_id}/
      └── auto/
          ├── {task_id}.md       ← MinerU 提取的 Markdown
          └── images/            ← 图片、表格、公式资源
```

### 资源保留
- ✅ Markdown 文件永久保存
- ✅ 图片/表格/公式永久保存
- ✅ 可重复使用生成笔记

## 优势

### 使用已提取文档功能：
- ✅ **快速**：5-15秒 vs 30秒-5分钟
- ✅ **节省成本**：不消耗 MinerU 计算资源
- ✅ **方便测试**：快速验证不同提示词效果
- ✅ **一致性**：使用相同的提取结果

## 注意事项

1. **首次提取**：必须使用"上传 PDF"功能
2. **数据持久化**：提取的数据会永久保存
3. **Token 消耗**：每次生成笔记都会消耗 API tokens
4. **清理数据**：如需清理，手动删除 `mineru_output` 目录

## 常见问题

### Q: 为什么有些任务没有图片？
A: 该 PDF 可能只包含文本，没有图片、表格或公式。

### Q: 可以删除已提取的任务吗？
A: 可以，手动删除 `mineru_output/{task_id}` 目录。

### Q: 笔记质量不满意怎么办？
A: 使用"已提取文档"功能反复测试，调整 `services/llm_service.py` 中的提示词。

### Q: 如何查看原始提取的 Markdown？
A: 直接打开 `mineru_output/{task_id}/auto/{task_id}.md` 文件。
