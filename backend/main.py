from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pathlib import Path
import shutil
import uuid
from typing import Optional
import os
import json

from config import settings
from services.mineru_service import MinerUService
from services.llm_service import LLMService
from services.ppt_service import PPTService
from services.marp_service import MarpService
from services.markdown_extractor.note_viewer import router as notes_router

# 初始化 FastAPI 应用
app = FastAPI(
    title="PDF 笔记生成 API",
    description="上传 PDF，使用 MinerU 解析并调用大模型生成易读笔记",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
mineru_service = MinerUService(output_dir=settings.MINERU_OUTPUT_DIR)
llm_service = LLMService(
    api_key=settings.DASHSCOPE_API_KEY,
    model_name=settings.MODEL_NAME
)
ppt_service = PPTService(output_dir="./temp/ppt_output")
marp_service = MarpService(output_dir="./temp/marp_output")

# 创建必要的目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MINERU_OUTPUT_DIR, exist_ok=True)
os.makedirs("./temp/ppt_output", exist_ok=True)
os.makedirs("./temp/saved_ppt_contents", exist_ok=True)
os.makedirs("./temp/marp_output", exist_ok=True)
os.makedirs("./temp/marp_markdowns", exist_ok=True)
os.makedirs("./temp/extractor_output", exist_ok=True)

# 注册学术笔记路由
app.include_router(notes_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "PDF 笔记生成 API",
        "version": "1.0.0",
        "endpoints": {
            "upload_pdf": "/api/upload-pdf",
            "upload_pdf_ppt": "/api/upload-pdf-ppt",
            "upload_pdf_ppt_v2": "/api/upload-pdf-ppt-v2 (推荐 - 基于笔记生成)",
            "list_tasks": "/api/tasks",
            "generate_notes_from_task": "/api/generate-notes-from-task",
            "generate_notes_from_task_stream": "/api/generate-notes-from-task-stream",
            "generate_ppt_from_task": "/api/generate-ppt-from-task (旧版 - 直接解析)",
            "generate_ppt_from_notes": "/api/generate-ppt-from-notes (推荐 - 基于笔记)",
            "download_ppt": "/api/download-ppt/{task_id}",
            "health": "/health",
            "saved_ppt_contents": "/api/saved-ppt-contents (获取已保存的 PPT 内容列表)",
            "get_saved_ppt_content": "/api/saved-ppt-content/{task_id} (获取指定的 PPT 内容)",
            "generate_ppt_from_saved": "/api/generate-ppt-from-saved-content (基于已保存内容快速生成 PPT)",
            "delete_saved_ppt_content": "/api/saved-ppt-content/{task_id} (删除已保存的 PPT 内容)",
            "generate_marp_ppt": "/api/generate-marp-ppt (使用 Marp 生成 PPT - 推荐)",
            "download_marp_ppt": "/api/download-marp-ppt/{task_id} (下载 Marp PPT)",
            "download_marp_markdown": "/api/download-marp-markdown/{task_id} (下载 Marp Markdown)",
            "marp_markdowns": "/api/marp-markdowns (获取 Marp Markdown 列表)",
            "get_marp_markdown": "/api/marp-markdown/{task_id} (获取指定的 Marp Markdown 内容)"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "mineru": "ok",
            "llm": "ok"
        }
    }


@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传 PDF 并生成笔记

    Args:
        file: 上传的 PDF 文件
        background_tasks: 后台任务

    Returns:
        生成的笔记和任务信息
    """
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="只支持 PDF 文件"
        )

    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
        )

    # 生成任务 ID
    task_id = str(uuid.uuid4())

    # 保存文件
    file_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        # 步骤 1: 使用 MinerU 解析 PDF
        parse_result = await mineru_service.parse_pdf(file_path, task_id)

        if parse_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PDF 解析失败: {parse_result['error']}"
            )

        pdf_markdown = parse_result["markdown_content"]

        # 步骤 2: 调用大模型生成笔记（传递 task_id 以支持多模态）
        notes_result = await llm_service.generate_notes(pdf_markdown, task_id=task_id)

        if notes_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"笔记生成失败: {notes_result['error']}"
            )

        # 添加后台清理任务
        if background_tasks:
            background_tasks.add_task(cleanup_files, task_id, file_path)

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "notes": notes_result["notes"],
                "metadata": {
                    "original_filename": file.filename,
                    "file_size": len(file_content),
                    "model": notes_result["model"],
                    "tokens_used": notes_result["tokens_used"]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


def cleanup_files(task_id: str, pdf_path: str):
    """清理临时文件"""
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        mineru_service.cleanup_task_files(task_id)
    except Exception as e:
        print(f"清理文件失败: {e}")


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态（预留接口，用于未来实现异步处理）

    Args:
        task_id: 任务 ID

    Returns:
        任务状态信息
    """
    # 这个接口预留用于未来实现异步任务处理
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "当前版本为同步处理，任务立即完成"
    }


@app.get("/api/tasks")
async def list_tasks():
    """
    列出所有已提取的任务（用于测试）

    Returns:
        任务列表和资源信息
    """
    try:
        tasks = []
        output_dir = Path(settings.MINERU_OUTPUT_DIR)

        if not output_dir.exists():
            return {"tasks": []}

        for task_dir in output_dir.iterdir():
            if task_dir.is_dir():
                task_id = task_dir.name
                auto_dir = task_dir / "auto"

                if auto_dir.exists():
                    md_file = auto_dir / f"{task_id}.md"
                    images_dir = auto_dir / "images"

                    task_info = {
                        "task_id": task_id,
                        "markdown_exists": md_file.exists(),
                        "images_dir_exists": images_dir.exists(),
                    }

                    if md_file.exists():
                        # 读取文件大小
                        task_info["markdown_size"] = md_file.stat().st_size

                    if images_dir.exists():
                        # 统计图片数量
                        images = list(images_dir.glob("*.*"))
                        task_info["image_count"] = len(images)
                        task_info["images"] = [img.name for img in images[:10]]  # 只返回前10个

                    tasks.append(task_info)

        return {
            "status": "success",
            "total_tasks": len(tasks),
            "tasks": sorted(tasks, key=lambda x: x["task_id"], reverse=True)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )


@app.post("/api/generate-notes-from-task")
async def generate_notes_from_task(task_id: str):
    """
    使用已提取的任务数据生成笔记（用于测试，避免重复提取）

    Args:
        task_id: 已存在的任务 ID

    Returns:
        生成的笔记
    """
    try:
        # 检查任务是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        md_file = auto_dir / f"{task_id}.md"

        if not md_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Markdown 文件不存在"
            )

        # 读取 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 调用大模型生成笔记（传递 task_id 以支持多模态）
        notes_result = await llm_service.generate_notes(markdown_content, task_id=task_id)

        if notes_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"笔记生成失败: {notes_result['error']}"
            )

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "notes": notes_result["notes"],
                "metadata": {
                    "source": "existing_task",
                    "markdown_size": len(markdown_content),
                    "model": notes_result["model"],
                    "tokens_used": notes_result["tokens_used"]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成笔记失败: {str(e)}"
        )


@app.post("/api/generate-notes-from-task-stream")
async def generate_notes_from_task_stream(task_id: str):
    """
    使用已提取的任务数据流式生成笔记（实时显示进度）

    Args:
        task_id: 已存在的任务 ID

    Returns:
        流式生成的笔记
    """
    try:
        # 检查任务是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        md_file = auto_dir / f"{task_id}.md"

        if not md_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Markdown 文件不存在"
            )

        # 读取 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        async def generate():
            """流式生成器"""
            try:
                # 发送开始标记
                yield f"data: {json.dumps({'type': 'start', 'task_id': task_id})}\n\n"

                # 流式生成笔记（传递 task_id 以支持多模态）
                async for chunk in llm_service.generate_notes_stream(markdown_content, task_id=task_id):
                    # 发送内容块
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

                # 发送完成标记
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                # 发送错误标记
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"流式生成笔记失败: {str(e)}"
        )


@app.get("/api/images/{task_id}/{image_name}")
async def get_image(task_id: str, image_name: str):
    """
    获取任务的图片文件

    Args:
        task_id: 任务 ID
        image_name: 图片文件名

    Returns:
        图片文件
    """
    try:
        image_path = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto" / "images" / image_name

        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"图片不存在: {image_name}"
            )

        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取图片失败: {str(e)}"
        )


# ==================== PPT 生成相关接口 ====================

@app.post("/api/upload-pdf-ppt")
async def upload_pdf_ppt(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传 PDF 并生成 PPT（独立功能，不生成笔记）

    Args:
        file: 上传的 PDF 文件
        background_tasks: 后台任务

    Returns:
        生成的 PPT 信息和下载链接
    """
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="只支持 PDF 文件"
        )

    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
        )

    # 生成任务 ID
    task_id = str(uuid.uuid4())

    # 保存文件
    file_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        # 使用 MinerU 解析 PDF
        parse_result = await mineru_service.parse_pdf(file_path, task_id)

        if parse_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PDF 解析失败: {parse_result['error']}"
            )

        pdf_markdown = parse_result["markdown_content"]

        # 生成 PPT
        ppt_result = await ppt_service.generate_ppt(pdf_markdown, task_id)

        if ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 生成失败: {ppt_result['error']}"
            )

        # 添加后台清理任务
        if background_tasks:
            background_tasks.add_task(cleanup_files_with_ppt, task_id, file_path)

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "download_url": f"/api/download-ppt/{task_id}",
                "metadata": {
                    "original_filename": file.filename,
                    "file_size": len(file_content),
                    "slides_count": ppt_result["slides_count"],
                    "title": ppt_result["title"]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


def cleanup_files_with_ppt(task_id: str, pdf_path: str):
    """清理临时文件（包括 PPT）"""
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        mineru_service.cleanup_task_files(task_id)
        # 注意：PPT 文件不自动清理，让用户下载后手动删除
        # ppt_service.cleanup_task_files(task_id)
    except Exception as e:
        print(f"清理文件失败: {e}")


@app.post("/api/generate-ppt-from-task")
async def generate_ppt_from_task(task_id: str):
    """
    使用已提取的任务数据生成 PPT（用于测试，避免重复提取）

    Args:
        task_id: 已存在的任务 ID

    Returns:
        生成的 PPT 信息
    """
    try:
        # 检查任务是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        md_file = auto_dir / f"{task_id}.md"

        if not md_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Markdown 文件不存在"
            )

        # 读取 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # 生成 PPT
        ppt_result = await ppt_service.generate_ppt(markdown_content, task_id)

        if ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 生成失败: {ppt_result['error']}"
            )

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "download_url": f"/api/download-ppt/{task_id}",
                "metadata": {
                    "source": "existing_task",
                    "markdown_size": len(markdown_content),
                    "slides_count": ppt_result["slides_count"],
                    "title": ppt_result["title"],
                    "sections_count": ppt_result["sections_count"]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成 PPT 失败: {str(e)}"
        )


@app.get("/api/download-ppt/{task_id}")
async def download_ppt(task_id: str):
    """
    下载生成的 PPT 文件

    Args:
        task_id: 任务 ID

    Returns:
        PPT 文件
    """
    try:
        ppt_path = Path("./temp/ppt_output") / f"{task_id}.pptx"

        if not ppt_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"PPT 文件不存在: {task_id}"
            )

        return FileResponse(
            path=str(ppt_path),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"{task_id}.pptx",
            headers={
                "Content-Disposition": f"attachment; filename={task_id}.pptx"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载 PPT 失败: {str(e)}"
        )


@app.post("/api/generate-ppt-from-notes")
async def generate_ppt_from_notes(task_id: str):
    """
    使用已生成的笔记创建 PPT（推荐方法）
    先生成笔记，再基于笔记生成 PPT

    Args:
        task_id: 已存在的任务 ID

    Returns:
        生成的 PPT 信息
    """
    try:
        # 检查任务是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        md_file = auto_dir / f"{task_id}.md"

        if not md_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Markdown 文件不存在"
            )

        # 读取原始 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            pdf_markdown = f.read()

        # 步骤 1: 生成笔记
        print(f"任务 {task_id}: 开始生成笔记...")
        notes_result = await llm_service.generate_notes(pdf_markdown, task_id=task_id)

        if notes_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"笔记生成失败: {notes_result['error']}"
            )

        notes = notes_result["notes"]
        print(f"任务 {task_id}: 笔记生成完成，长度 {len(notes)} 字符")

        # 步骤 2: 基于笔记生成 PPT 内容
        print(f"任务 {task_id}: 开始生成 PPT 内容...")
        ppt_content_result = await llm_service.generate_ppt_content(notes, task_id=task_id)

        if ppt_content_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 内容生成失败: {ppt_content_result['error']}"
            )

        ppt_content = ppt_content_result["ppt_content"]
        print(f"任务 {task_id}: PPT 内容生成完成，长度 {len(ppt_content)} 字符")

        # 步骤 2.5: 保存 PPT 内容到文件
        saved_content_path = Path("./temp/saved_ppt_contents") / f"{task_id}_ppt_content.md"
        with open(saved_content_path, 'w', encoding='utf-8') as f:
            f.write(ppt_content)
        print(f"任务 {task_id}: PPT 内容已保存到 {saved_content_path}")

        # 步骤 3: 创建 PPT 文件
        print(f"任务 {task_id}: 开始创建 PPT 文件...")
        images_dir = auto_dir / "images"
        ppt_result = await ppt_service.generate_ppt_from_notes(
            ppt_content,
            task_id,
            images_dir=images_dir if images_dir.exists() else None
        )

        if ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 文件创建失败: {ppt_result['error']}"
            )

        print(f"任务 {task_id}: PPT 生成完成，共 {ppt_result['slides_count']} 页")

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "download_url": f"/api/download-ppt/{task_id}",
                "metadata": {
                    "source": "notes_based",
                    "method": "generate_ppt_from_notes",
                    "slides_count": ppt_result["slides_count"],
                    "title": ppt_result["title"],
                    "notes_tokens": notes_result.get("tokens_used", 0),
                    "ppt_content_tokens": ppt_content_result.get("tokens_used", 0)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"生成 PPT 失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"生成 PPT 失败: {str(e)}"
        )


@app.post("/api/upload-pdf-ppt-v2")
async def upload_pdf_ppt_v2(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    上传 PDF 并生成 PPT（新版本 - 基于笔记）

    与旧版本的区别：
    - 旧版本：直接从原始 Markdown 生成 PPT（内容冗余、质量低）
    - 新版本：先生成笔记，再基于笔记生成 PPT（内容精炼、质量高）

    Args:
        file: 上传的 PDF 文件
        background_tasks: 后台任务

    Returns:
        生成的 PPT 信息和下载链接
    """
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="只支持 PDF 文件"
        )

    # 检查文件大小
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
        )

    # 生成任务 ID
    task_id = str(uuid.uuid4())

    # 保存文件
    file_path = os.path.join(settings.UPLOAD_DIR, f"{task_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(file_content)

    try:
        # 步骤 1: 使用 MinerU 解析 PDF
        parse_result = await mineru_service.parse_pdf(file_path, task_id)

        if parse_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PDF 解析失败: {parse_result['error']}"
            )

        pdf_markdown = parse_result["markdown_content"]

        # 步骤 2: 生成笔记
        print(f"任务 {task_id}: 开始生成笔记...")
        notes_result = await llm_service.generate_notes(pdf_markdown, task_id=task_id)

        if notes_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"笔记生成失败: {notes_result['error']}"
            )

        notes = notes_result["notes"]
        print(f"任务 {task_id}: 笔记生成完成，长度 {len(notes)} 字符")

        # 步骤 3: 基于笔记生成 PPT 内容
        print(f"任务 {task_id}: 开始生成 PPT 内容...")
        ppt_content_result = await llm_service.generate_ppt_content(notes, task_id=task_id)

        if ppt_content_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 内容生成失败: {ppt_content_result['error']}"
            )

        ppt_content = ppt_content_result["ppt_content"]
        print(f"任务 {task_id}: PPT 内容生成完成，长度 {len(ppt_content)} 字符")

        # 步骤 3.5: 保存 PPT 内容到文件
        saved_content_path = Path("./temp/saved_ppt_contents") / f"{task_id}_ppt_content.md"
        with open(saved_content_path, 'w', encoding='utf-8') as f:
            f.write(ppt_content)
        print(f"任务 {task_id}: PPT 内容已保存到 {saved_content_path}")

        # 步骤 4: 创建 PPT 文件
        print(f"任务 {task_id}: 开始创建 PPT 文件...")
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        images_dir = auto_dir / "images"
        ppt_result = await ppt_service.generate_ppt_from_notes(
            ppt_content,
            task_id,
            images_dir=images_dir if images_dir.exists() else None
        )

        if ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 文件创建失败: {ppt_result['error']}"
            )

        print(f"任务 {task_id}: PPT 生成完成，共 {ppt_result['slides_count']} 页")

        # 添加后台清理任务
        if background_tasks:
            background_tasks.add_task(cleanup_files_with_ppt, task_id, file_path)

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "download_url": f"/api/download-ppt/{task_id}",
                "metadata": {
                    "original_filename": file.filename,
                    "file_size": len(file_content),
                    "slides_count": ppt_result["slides_count"],
                    "title": ppt_result["title"],
                    "notes_tokens": notes_result.get("tokens_used", 0),
                    "ppt_content_tokens": ppt_content_result.get("tokens_used", 0)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )


# ==================== PPT 内容管理接口 ====================

@app.get("/api/saved-ppt-contents")
async def list_saved_ppt_contents():
    """
    获取已保存的 PPT 内容列表

    Returns:
        已保存的 PPT 内容列表
    """
    try:
        contents_dir = Path("./temp/saved_ppt_contents")

        if not contents_dir.exists():
            return {
                "status": "success",
                "contents": []
            }

        contents = []
        for file_path in contents_dir.glob("*.md"):
            task_id = file_path.stem.replace("_ppt_content", "")

            # 读取文件获取标题和预览
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取标题（第一行以 # 开头的）
                lines = content.split('\n')
                title = "未命名"
                for line in lines:
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break

                # 统计幻灯片数量
                slide_count = content.count('## 第')

                # 获取文件修改时间
                import time
                mtime = file_path.stat().st_mtime

            contents.append({
                "task_id": task_id,
                "title": title,
                "slide_count": slide_count,
                "content_length": len(content),
                "modified_time": mtime,
                "file_path": str(file_path)
            })

        # 按修改时间倒序排列
        contents.sort(key=lambda x: x['modified_time'], reverse=True)

        return {
            "status": "success",
            "total": len(contents),
            "contents": contents
        }

    except Exception as e:
        import traceback
        print(f"获取已保存的 PPT 内容失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"获取已保存的 PPT 内容失败: {str(e)}"
        )


@app.get("/api/saved-ppt-content/{task_id}")
async def get_saved_ppt_content(task_id: str):
    """
    获取指定任务的已保存 PPT 内容

    Args:
        task_id: 任务 ID

    Returns:
        已保存的 PPT 内容
    """
    try:
        content_path = Path("./temp/saved_ppt_contents") / f"{task_id}_ppt_content.md"

        if not content_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的已保存 PPT 内容不存在"
            )

        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "status": "success",
            "task_id": task_id,
            "content": content,
            "content_length": len(content)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"获取已保存的 PPT 内容失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"获取已保存的 PPT 内容失败: {str(e)}"
        )


@app.post("/api/generate-ppt-from-saved-content")
async def generate_ppt_from_saved_content(task_id: str):
    """
    基于已保存的 PPT 内容生成 PPT 文件（快速测试）
    跳过笔记生成和 PPT 内容转换步骤,直接使用已保存的内容

    Args:
        task_id: 已保存 PPT 内容对应的任务 ID

    Returns:
        生成的 PPT 信息
    """
    try:
        # 读取已保存的 PPT 内容
        content_path = Path("./temp/saved_ppt_contents") / f"{task_id}_ppt_content.md"

        if not content_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的已保存 PPT 内容不存在"
            )

        with open(content_path, 'r', encoding='utf-8') as f:
            ppt_content = f.read()

        print(f"任务 {task_id}: 读取已保存的 PPT 内容，长度 {len(ppt_content)} 字符")

        # 检查对应的图片目录是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        images_dir = auto_dir / "images"

        print(f"DEBUG: images_dir={images_dir}, exists={images_dir.exists()}")

        # 生成新的 task_id 用于这次 PPT 生成
        import uuid
        new_task_id = str(uuid.uuid4())

        # 创建 PPT 文件
        print(f"任务 {new_task_id}: 开始创建 PPT 文件...")
        ppt_result = await ppt_service.generate_ppt_from_notes(
            ppt_content,
            new_task_id,
            images_dir=images_dir if images_dir.exists() else None
        )

        if ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"PPT 文件创建失败: {ppt_result['error']}"
            )

        print(f"任务 {new_task_id}: PPT 生成完成，共 {ppt_result['slides_count']} 页")

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": new_task_id,
                "download_url": f"/api/download-ppt/{new_task_id}",
                "metadata": {
                    "source": "saved_content",
                    "original_task_id": task_id,
                    "slides_count": ppt_result["slides_count"],
                    "title": ppt_result["title"]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"基于已保存内容生成 PPT 失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"生成 PPT 失败: {str(e)}"
        )


@app.delete("/api/saved-ppt-content/{task_id}")
async def delete_saved_ppt_content(task_id: str):
    """
    删除已保存的 PPT 内容

    Args:
        task_id: 任务 ID

    Returns:
        删除结果
    """
    try:
        content_path = Path("./temp/saved_ppt_contents") / f"{task_id}_ppt_content.md"

        if not content_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的已保存 PPT 内容不存在"
            )

        content_path.unlink()

        return {
            "status": "success",
            "message": f"任务 {task_id} 的已保存 PPT 内容已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"删除已保存的 PPT 内容失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


# ==================== Marp PPT 生成相关接口 ====================

@app.post("/api/generate-marp-ppt")
async def generate_marp_ppt(task_id: str):
    """
    使用 Marp 从已有任务生成 PPT

    流程：
    1. 读取 mineru_output 中的 Markdown 内容
    2. 调用大模型生成 Marp 格式的 Markdown
    3. 保存 Marp Markdown 到文件夹
    4. 使用 Marp CLI 转换为 PPT

    Args:
        task_id: 已存在的任务 ID

    Returns:
        生成的 PPT 信息和下载链接
    """
    try:
        # 步骤 1: 检查任务是否存在
        auto_dir = Path(settings.MINERU_OUTPUT_DIR) / task_id / "auto"
        md_file = auto_dir / f"{task_id}.md"

        if not md_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Markdown 文件不存在"
            )

        # 读取原始 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            pdf_markdown = f.read()

        print(f"任务 {task_id}: 读取 PDF Markdown，长度 {len(pdf_markdown)} 字符")

        # 步骤 2: 调用大模型生成 Marp 格式内容
        print(f"任务 {task_id}: 开始生成 Marp 内容...")
        marp_result = await llm_service.generate_marp_content(pdf_markdown, task_id=task_id)

        if marp_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Marp 内容生成失败: {marp_result['error']}"
            )

        marp_content = marp_result["marp_content"]
        print(f"任务 {task_id}: Marp 内容生成完成，长度 {len(marp_content)} 字符")

        # 步骤 3: 保存 Marp Markdown 到文件夹
        marp_md_dir = Path("./temp/marp_markdowns")
        marp_md_dir.mkdir(exist_ok=True)
        marp_md_path = marp_md_dir / f"{task_id}_marp.md"

        with open(marp_md_path, 'w', encoding='utf-8') as f:
            f.write(marp_content)
        print(f"任务 {task_id}: Marp Markdown 已保存到 {marp_md_path}")

        # 步骤 4: 使用 Marp 转换为 PPT
        print(f"任务 {task_id}: 开始使用 Marp 转换为 PPT...")
        images_dir = auto_dir / "images"
        marp_ppt_result = await marp_service.convert_marp_to_ppt(
            markdown_path=str(marp_md_path),
            task_id=task_id,
            images_dir=images_dir if images_dir.exists() else None,
            embed_images=True  # 将图片嵌入到 PPT 中，使 PPT 文件完全独立
        )

        if marp_ppt_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Marp PPT 转换失败: {marp_ppt_result['error']}"
            )

        print(f"任务 {task_id}: Marp PPT 生成完成")

        # 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "task_id": task_id,
                "download_url": f"/api/download-marp-ppt/{task_id}",
                "marp_markdown_url": f"/api/download-marp-markdown/{task_id}",
                "metadata": {
                    "source": "marp_based",
                    "method": "generate_marp_ppt",
                    "marp_markdown_path": str(marp_md_path),
                    "ppt_path": marp_ppt_result["ppt_path"],
                    "tokens_used": marp_result.get("tokens_used", 0)
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"生成 Marp PPT 失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"生成 Marp PPT 失败: {str(e)}"
        )


@app.get("/api/download-marp-ppt/{task_id}")
async def download_marp_ppt(task_id: str):
    """
    下载 Marp 生成的 PPT 文件

    Args:
        task_id: 任务 ID

    Returns:
        PPT 文件
    """
    try:
        ppt_path = Path("./temp/marp_output") / f"{task_id}.pptx"

        if not ppt_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Marp PPT 文件不存在: {task_id}"
            )

        return FileResponse(
            path=str(ppt_path),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"{task_id}_marp.pptx",
            headers={
                "Content-Disposition": f"attachment; filename={task_id}_marp.pptx"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载 Marp PPT 失败: {str(e)}"
        )


@app.get("/api/download-marp-markdown/{task_id}")
async def download_marp_markdown(task_id: str):
    """
    下载 Marp Markdown 文件

    Args:
        task_id: 任务 ID

    Returns:
        Markdown 文件
    """
    try:
        md_path = Path("./temp/marp_markdowns") / f"{task_id}_marp.md"

        if not md_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Marp Markdown 文件不存在: {task_id}"
            )

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={task_id}_marp.md"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载 Marp Markdown 失败: {str(e)}"
        )


@app.get("/api/marp-markdowns")
async def list_marp_markdowns():
    """
    获取已生成的 Marp Markdown 列表

    Returns:
        Marp Markdown 文件列表
    """
    try:
        marp_md_dir = Path("./temp/marp_markdowns")

        if not marp_md_dir.exists():
            return {
                "status": "success",
                "markdowns": []
            }

        markdowns = []
        for file_path in marp_md_dir.glob("*.md"):
            task_id = file_path.stem.replace("_marp", "")

            # 读取文件获取信息
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 统计幻灯片数量
                slide_count = content.count('---') - 1 if content.startswith('---') else content.count('---')

                # 提取标题（第一个 # 标题）
                lines = content.split('\n')
                title = "未命名"
                for line in lines:
                    if line.strip().startswith('# '):
                        title = line.strip()[2:].strip()
                        break

                # 获取文件修改时间
                import time
                mtime = file_path.stat().st_mtime

            markdowns.append({
                "task_id": task_id,
                "title": title,
                "slide_count": max(0, slide_count),
                "content_length": len(content),
                "modified_time": mtime,
                "file_path": str(file_path)
            })

        # 按修改时间倒序排列
        markdowns.sort(key=lambda x: x['modified_time'], reverse=True)

        return {
            "status": "success",
            "total": len(markdowns),
            "markdowns": markdowns
        }

    except Exception as e:
        import traceback
        print(f"获取 Marp Markdown 列表失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"获取 Marp Markdown 列表失败: {str(e)}"
        )


@app.get("/api/marp-markdown/{task_id}")
async def get_marp_markdown(task_id: str):
    """
    获取指定任务的 Marp Markdown 内容

    Args:
        task_id: 任务 ID

    Returns:
        Marp Markdown 内容
    """
    try:
        md_path = Path("./temp/marp_markdowns") / f"{task_id}_marp.md"

        if not md_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 的 Marp Markdown 不存在"
            )

        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "status": "success",
            "task_id": task_id,
            "content": content,
            "content_length": len(content)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"获取 Marp Markdown 失败:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"获取 Marp Markdown 失败: {str(e)}"
        )
