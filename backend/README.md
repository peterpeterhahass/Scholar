# PDF 笔记生成后端服务

基于 FastAPI 的 PDF 解析和笔记生成服务，使用 MinerU 解析 PDF，调用通义千问生成易读笔记。

## 功能特性

- 上传 PDF 文件自动解析
- 使用 MinerU 提取 PDF 内容
- 调用通义千问（Qwen）生成结构化笔记
- 返回 Markdown 格式的笔记

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# MinerU 配置
MINERU_OUTPUT_DIR=./temp/mineru_output

# 大模型配置 (Qwen)
DASHSCOPE_API_KEY=your_dashscope_api_key_here
MODEL_NAME=qwen-plus

# 服务配置
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./temp/uploads
```

### 3. 获取通义千问 API Key

访问 [阿里云百炼平台](https://bailian.console.aliyun.com/) 获取 API Key

## 运行服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 http://localhost:8000 启动

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### POST /api/upload-pdf

上传 PDF 并生成笔记

**请求：**
- Method: POST
- Content-Type: multipart/form-data
- Body: PDF 文件

**响应：**
```json
{
  "status": "success",
  "task_id": "uuid",
  "notes": "生成的 Markdown 笔记",
  "metadata": {
    "original_filename": "example.pdf",
    "file_size": 12345,
    "model": "qwen-plus",
    "tokens_used": 1500
  }
}
```

### GET /health

健康检查

**响应：**
```json
{
  "status": "healthy",
  "services": {
    "mineru": "ok",
    "llm": "ok"
  }
}
```

## 项目结构

```
backend/
├── main.py                 # FastAPI 主应用
├── config.py              # 配置管理
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── services/
│   ├── mineru_service.py # MinerU 解析服务
│   └── llm_service.py    # 大模型调用服务
└── temp/                 # 临时文件目录
    ├── uploads/          # 上传的 PDF
    └── mineru_output/    # MinerU 输出
```

## 注意事项

1. **MinerU 安装**: 如果 MinerU 安装失败，服务会使用模拟模式进行开发测试
2. **文件大小限制**: 默认最大 10MB，可在 `.env` 中调整
3. **API Key**: 必须配置有效的通义千问 API Key
4. **临时文件**: 上传的文件会在任务完成后自动清理
