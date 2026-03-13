# PPT 生成功能使用指南

## 功能概述

新增的 PPT 生成功能允许用户从 PDF 论文自动生成 PowerPoint 演示文稿,与现有的笔记生成功能完全独立,互不冲突。

## 架构设计

```
PDF 上传
   ↓
选择输出模式
   ├─ 📝 仅生成笔记 (原有功能)
   ├─ 📊 仅生成PPT (新功能)
   └─ 📚 笔记 + PPT (组合功能)
```

## 后端实现

### 新增文件

1. **`backend/services/ppt_service.py`**
   - PPT 生成服务
   - 解析论文 Markdown 结构
   - 自动生成标题页、目录页、章节页、总结页

### 修改文件

1. **`backend/main.py`**
   - 新增 API 端点:
     - `POST /api/upload-pdf-ppt` - 上传 PDF 并生成 PPT
     - `POST /api/generate-ppt-from-task` - 从已有任务生成 PPT
     - `GET /api/download-ppt/{task_id}` - 下载生成的 PPT

2. **`backend/requirements.txt`**
   - 新增依赖: `python-pptx==1.0.2`

## 前端实现

### 新增组件

1. **`frontend/src/components/FileUploadWithMode.tsx`**
   - 支持选择输出模式的文件上传组件
   - 三种模式: 仅笔记、仅PPT、笔记+PPT

2. **`frontend/src/components/PPTViewer.tsx`**
   - PPT 预览和下载组件
   - 显示 PPT 元信息
   - 提供下载按钮

### 修改文件

1. **`frontend/src/App.tsx`**
   - 集成新的文件上传组件
   - 支持多种输出模式
   - 同时处理笔记和 PPT 数据

2. **`frontend/src/App.css`**
   - 新增 PPT 相关样式
   - 模式选择器样式
   - PPT 预览卡片样式

## 安装和使用

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动服务

```bash
# 启动后端 (终端1)
cd backend
python main.py

# 启动前端 (终端2)
cd frontend
npm run dev
```

### 3. 使用功能

1. 打开浏览器访问 `http://localhost:5173`
2. 选择输出模式:
   - **📝 仅生成笔记**: 生成 Markdown 格式的学术笔记
   - **📊 仅生成PPT**: 生成 PowerPoint 演示文稿
   - **📚 笔记 + PPT**: 同时生成两种格式
3. 上传 PDF 文件
4. 等待处理完成
5. 查看/下载生成的内容

## API 端点

### 生成 PPT

```bash
# 上传 PDF 并生成 PPT
curl -X POST http://localhost:8000/api/upload-pdf-ppt \
  -F "file=@paper.pdf"

# 从已有任务生成 PPT
curl -X POST "http://localhost:8000/api/generate-ppt-from-task?task_id=xxx"

# 下载 PPT
curl -O http://localhost:8000/api/download-ppt/xxx
```

### 响应示例

```json
{
  "status": "success",
  "task_id": "uuid",
  "download_url": "/api/download-ppt/uuid",
  "metadata": {
    "original_filename": "paper.pdf",
    "file_size": 1234567,
    "slides_count": 12,
    "title": "Attention Is All You Need"
  }
}
```

## PPT 结构

生成的 PPT 自动包含以下页面:

1. **标题页**
   - 论文标题
   - 作者列表

2. **目录页**
   - 各章节标题列表

3. **章节内容页** (每个章节一张)
   - 章节标题
   - 要点列表
   - 关键内容

4. **总结页**
   - 论文信息总结
   - 下一步工作建议

## 特点

### ✅ 完全独立
- PPT 生成功能与笔记生成功能完全独立
- 用户可以自由选择需要的输出格式
- 互不干扰,独立运行

### ✅ 智能解析
- 自动提取论文标题、作者
- 识别章节结构
- 提取关键要点

### ✅ 专业设计
- 16:9 宽屏布局
- 统一的配色方案
- 清晰的层次结构

### ✅ 灵活组合
- 支持单独生成笔记或 PPT
- 支持同时生成两种格式
- 满足不同使用场景

## 文件存储

```
backend/
├── temp/
│   ├── mineru_output/     # MinerU 提取的 Markdown 和图片
│   ├── ppt_output/        # 生成的 PPT 文件
│   └── uploads/           # 上传的 PDF 文件
```

## 注意事项

1. **文件清理**:
   - 上传的 PDF 和 MinerU 提取的文件会自动清理
   - PPT 文件会保留,供用户下载后手动删除

2. **文件大小限制**:
   - 默认最大 10MB
   - 可在 `.env` 文件中配置

3. **性能考虑**:
   - 大型论文可能需要较长处理时间
   - 建议先处理较小的文件测试

4. **PPT 编辑**:
   - 生成的 PPT 可在 PowerPoint/Keynote/WPS 中进一步编辑
   - 提供基础框架,用户可根据需要美化

## 扩展开发

### 自定义 PPT 样式

编辑 `backend/services/ppt_service.py`:

```python
# 修改颜色主题
title_para.font.color.rgb = RGBColor(31, 78, 120)  # 标题颜色

# 修改字体大小
title_para.font.size = Pt(44)

# 添加 Logo
slide.shapes.add_picture(
    'logo.png',
    left=Inches(8),
    top=Inches(0.5)
)
```

### 添加更多页面类型

```python
def create_image_slide(self, prs, image_path):
    """创建图片展示页"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # 添加图片和说明...
```

## 常见问题

### Q: 生成的 PPT 如何进一步编辑?
A: 下载后使用 PowerPoint、Keynote 或 WPS 打开即可编辑。

### Q: 可以自定义 PPT 模板吗?
A: 可以修改 `ppt_service.py` 中的样式代码,或加载自定义 `.pptx` 模板文件。

### Q: 支持哪些语言?
A: 支持中文、英文等多种语言,基于论文内容自动识别。

### Q: PPT 文件保存在哪里?
A: 保存在 `backend/temp/ppt_output/` 目录下,文件名为 `{task_id}.pptx`。

## 技术栈

- **后端**: FastAPI + python-pptx
- **前端**: React + TypeScript
- **样式**: CSS3 (无需额外 UI 库)
- **PDF 解析**: MinerU
- **大模型**: 通义千问 (用于笔记生成)

## 许可证

MIT
