from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from schemas.novel import NovelCreate, NovelOut, NovelDetail, ChapterOut
from core.novel_service import novel_service

router = APIRouter(prefix="/api/novels", tags=["novels"])


@router.post("/upload", response_model=NovelOut)
async def upload_novel(
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith((".txt", ".text", ".md")):
        raise HTTPException(400, "only .txt/.md files are supported")
    content = await file.read()
    meta = NovelCreate(title=title or Path(file.filename).stem, author=author)
    novel = await novel_service.upload(session, content, file.filename, meta)
    await novel_service.parse_chapters(session, novel.id)
    return novel


@router.get("", response_model=list[NovelOut])
async def list_novels(session: AsyncSession = Depends(get_session)):
    return await novel_service.list_novels(session)


@router.get("/{novel_id}", response_model=NovelDetail)
async def get_novel(novel_id: int, session: AsyncSession = Depends(get_session)):
    novel = await novel_service.get_novel(session, novel_id)
    if not novel:
        raise HTTPException(404, "novel not found")
    return novel


@router.delete("/{novel_id}")
async def delete_novel(novel_id: int, session: AsyncSession = Depends(get_session)):
    ok = await novel_service.delete_novel(session, novel_id)
    if not ok:
        raise HTTPException(404, "novel not found")
    return {"ok": True}


@router.get("/{novel_id}/chapters/{chapter_id}", response_model=ChapterOut)
async def get_chapter(
    novel_id: int, chapter_id: int, session: AsyncSession = Depends(get_session)
):
    chapter = await novel_service.get_chapter(session, chapter_id)
    if not chapter or chapter.novel_id != novel_id:
        raise HTTPException(404, "chapter not found")
    return chapter
