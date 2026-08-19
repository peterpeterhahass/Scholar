"""
学术笔记查看服务。

提供 API 获取学术笔记 Markdown 内容，并将图片路径转换为
前端可直接访问的 URL（/api/images/{task_id}/{image_name}）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/notes", tags=["学术笔记"])

_RE_IMAGE_PATH = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")


class NoteResponse(BaseModel):
    task_id: str
    content: str
    raw_content: str


def _resolve_image_urls(markdown: str, task_id: str) -> str:
    """将 images/xxx.jpg 转换为 /api/images/{task_id}/xxx.jpg"""
    def _replace(m: re.Match) -> str:
        alt = m.group(1)
        filename = m.group(2)
        return f"![{alt}](/api/images/{task_id}/{filename})"
    return _RE_IMAGE_PATH.sub(_replace, markdown)


def get_raw_notes_path() -> Path:
    return Path("temp/extractor_output/academic_notes.md")


@router.get("/{task_id}", response_model=NoteResponse)
async def get_academic_notes(task_id: str):
    notes_path = get_raw_notes_path()
    if not notes_path.exists():
        raise HTTPException(status_code=404, detail="学术笔记尚未生成")

    raw = notes_path.read_text(encoding="utf-8")
    content = _resolve_image_urls(raw, task_id)
    return NoteResponse(task_id=task_id, content=content, raw_content=raw)


@router.get("/{task_id}/raw")
async def get_raw_notes(task_id: str):
    notes_path = get_raw_notes_path()
    if not notes_path.exists():
        raise HTTPException(status_code=404, detail="学术笔记尚未生成")
    return {"task_id": task_id, "content": notes_path.read_text(encoding="utf-8")}
