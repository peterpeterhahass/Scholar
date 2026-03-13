# PDF 笔记生成器前端

基于 React + TypeScript + Vite 的前端应用，提供 PDF 上传和笔记展示功能。

## 功能特性

- 拖拽上传 PDF 文件
- 实时显示处理进度
- 美观的 Markdown 笔记展示
- 响应式设计

## 安装步骤

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置后端地址

如果后端不在 `http://localhost:8000`，修改 [vite.config.ts](vite.config.ts) 中的 proxy 配置。

## 运行项目

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

应用将在 http://localhost:5173 启动

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── FileUpload.tsx       # 文件上传组件
│   │   ├── FileUpload.css
│   │   ├── MarkdownViewer.tsx   # Markdown 展示组件
│   │   └── MarkdownViewer.css
│   ├── App.tsx                  # 主应用组件
│   ├── App.css
│   ├── main.tsx                 # 应用入口
│   └── index.css                # 全局样式
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 组件说明

### FileUpload 组件

支持拖拽和点击上传 PDF 文件，包含文件验证和加载状态。

### MarkdownViewer 组件

使用 `react-markdown` 渲染 Markdown 内容，支持 GFM（GitHub Flavored Markdown）。

## 技术栈

- **框架**: React 18
- **语言**: TypeScript
- **构建工具**: Vite
- **Markdown 渲染**: react-markdown + remark-gfm
- **HTTP 客户端**: Fetch API

## 样式特性

- 渐变背景头部
- 拖拽区域动画效果
- 加载状态动画
- 响应式布局
- 优雅的 Markdown 样式

## API 集成

通过 Vite proxy 代理到后端 API：

```typescript
// 上传 PDF
POST /api/upload-pdf
Content-Type: multipart/form-data

// 响应
{
  "status": "success",
  "notes": "Markdown 内容",
  "metadata": { ... }
}
```