# PDF 笔记生成器

全栈应用：上传 PDF → 使用 MinerU 解析 → 调用大模型生成易读笔记 → 返回 Markdown 展示

## 系统架构

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │─────▶│   Backend    │─────▶│  MinerU     │
│  (React)    │◀─────│  (FastAPI)   │◀─────│  (PDF解析)  │
└─────────────┘      └──────────────┘      └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  通义千问     │
                    │  (Qwen)      │
                    └──────────────┘
```

## 功能特性

- 📄 支持拖拽上传 PDF 文件
- 🔍 使用 MinerU 提取 PDF 内容
- 🤖 调用通义千问生成结构化笔记
- 📝 美观的 Markdown 展示
- 📱 响应式设计
- ⚡ 异步处理，自动清理临时文件

## 快速开始

### 后端设置

1. 安装 Python 依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的通义千问 API Key：
```env
DASHSCOPE_API_KEY=your_api_key_here
```

3. 启动后端服务：
```bash
python main.py
```

服务将在 http://localhost:8000 启动

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

应用将在 http://localhost:5173 启动

## 使用说明

1. 打开前端应用 http://localhost:5173
2. 拖拽或点击上传 PDF 文件（最大 10MB）
3. 等待处理完成
4. 查看自动生成的 Markdown 笔记

## 项目结构

```
scholar/
├── backend/              # FastAPI 后端
│   ├── services/        # 业务逻辑
│   │   ├── mineru_service.py   # MinerU 集成
│   │   └── llm_service.py      # 大模型调用
│   ├── main.py          # FastAPI 应用
│   ├── config.py        # 配置管理
│   └── requirements.txt # Python 依赖
│
├── frontend/            # React 前端
│   ├── src/
│   │   └── components/
│   │       ├── FileUpload.tsx    # 文件上传
│   │       └── MarkdownViewer.tsx # Markdown 渲染
│   └── package.json
│
└── README.md           # 项目说明
```

## 技术栈

### 后端
- **框架**: FastAPI
- **PDF 解析**: MinerU
- **大模型**: 通义千问 (Qwen)
- **配置管理**: Pydantic Settings

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **Markdown**: react-markdown
- **样式**: CSS3 (无需 UI 框架)

## API 文档

后端启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置说明

### 后端配置 (.env)

```env
# MinerU 输出目录
MINERU_OUTPUT_DIR=./temp/mineru_output

# 通义千问配置
DASHSCOPE_API_KEY=your_key_here
MODEL_NAME=qwen-plus

# 服务配置
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173

# 文件上传配置
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./temp/uploads
```

## 注意事项

1. **MinerU**: 如果未安装，服务会使用模拟模式进行开发测试
2. **API Key**: 必须配置有效的通义千问 API Key 才能生成笔记
3. **文件大小**: 默认最大 10MB，可在配置中调整
4. **临时文件**: 上传的文件会在处理完成后自动清理

## 开发建议

- 安装 MinerU: `pip install miner-u`
- 获取 API Key: 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
- 查看 API 文档: http://localhost:8000/docs

## License

MIT