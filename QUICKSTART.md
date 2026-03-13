# 快速开始指南

## 一、后端设置

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

**Windows 用户**：双击运行 `start.bat`，会自动创建配置文件

**Linux/Mac 用户**：
```bash
chmod +x start.sh
./start.sh
```

或手动配置：
```bash
cp .env.example .env
nano .env  # 编辑配置文件
```

### 3. 获取 API Key

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 注册/登录账号
3. 创建 API Key
4. 将 API Key 填入 `backend/.env` 文件中的 `DASHSCOPE_API_KEY`

### 4. 测试配置

```bash
# 测试 MinerU
python test_mineru.py

# 测试大模型连接
python test_llm.py
```

### 5. 启动后端

```bash
python main.py
```

或使用快速启动脚本：
- Windows: `start.bat`
- Linux/Mac: `./start.sh`

后端将在 http://localhost:8000 启动

## 二、前端设置

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

前端将在 http://localhost:5173 启动

## 三、使用说明

1. 确保后端服务正在运行 (http://localhost:8000)
2. 确保前端服务正在运行 (http://localhost:5173)
3. 在浏览器中打开 http://localhost:5173
4. 拖拽或点击上传 PDF 文件
5. 等待处理完成，查看生成的笔记

## 四、常见问题

### Q: MinerU 安装失败怎么办？

A: 如果 MinerU 安装失败，服务会自动使用模拟模式。功能仍然可用，但会使用模拟内容。生产环境请确保安装 MinerU：
```bash
pip install miner-u
```

### Q: API 调用失败？

A: 检查以下几点：
1. API Key 是否正确配置在 `.env` 文件中
2. API Key 是否有效（访问 [阿里云百炼](https://bailian.console.aliyun.com/) 检查）
3. 网络连接是否正常
4. 运行 `python test_llm.py` 测试连接

### Q: 文件上传失败？

A: 检查文件大小：
- 默认最大 10MB
- 可在 `.env` 中修改 `MAX_FILE_SIZE` 配置

### Q: CORS 错误？

A: 检查 `backend/.env` 中的 `CORS_ORIGINS` 配置是否包含前端地址：
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 五、API 文档

后端启动后，访问以下地址查看 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 六、生产部署

### 后端部署

```bash
# 使用 gunicorn + uvicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 前端部署

```bash
# 构建生产版本
npm run build

# 使用 nginx 或其他静态服务器托管 dist 目录
```

## 七、开发建议

1. **使用虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **启用自动重载**：后端默认使用 `--reload` 模式

3. **查看日志**：后端会在终端输出详细日志

4. **测试 API**：使用 Swagger UI 进行交互式测试

## 八、项目结构说明

```
scholar/
├── backend/              # 后端服务
│   ├── services/        # 核心业务逻辑
│   ├── main.py          # FastAPI 应用入口
│   ├── config.py        # 配置管理
│   └── .env             # 环境变量（需自行配置）
│
├── frontend/            # 前端应用
│   ├── src/            # React 组件
│   └── package.json
│
├── start.bat           # Windows 快速启动脚本
└── start.sh            # Linux/Mac 快速启动脚本
```

## 九、技术支持

如有问题，请检查：
1. Python 版本 >= 3.8
2. Node.js 版本 >= 16
3. 网络连接正常
4. API Key 有效

祝你使用愉快！