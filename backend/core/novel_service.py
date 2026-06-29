import io
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models import Novel, Chapter, NovelStatus
from storage.file_manager import file_manager
from schemas.novel import NovelCreate
from utils.text_utils import split_into_chapters, count_words


_ENCODINGS = ["utf-8-sig", "utf-8", "gbk", "gb18030", "big5", "big5hkscs", "shift_jis", "euc-jp"]


def _detect_encoding(data: bytes) -> str:
    try:
        import chardet
        result = chardet.detect(data)
        if result and result.get("encoding") and result["confidence"] > 0.5:
            return result["encoding"]
    except ImportError:
        pass
    for enc in _ENCODINGS:
        try:
            data.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


class NovelService:
    async def upload(self, session: AsyncSession, content: bytes, filename: str, meta: NovelCreate) -> Novel:
        file_path = await file_manager.save_upload(content, filename)
        novel = Novel(
            title=meta.title,
            author=meta.author,
            file_path=file_path,
            file_size=len(content),
            status=NovelStatus.PARSING,
        )
        session.add(novel)
        await session.commit()
        await session.refresh(novel)
        return novel

    async def parse_chapters(self, session: AsyncSession, novel_id: int):
        novel = await session.get(Novel, novel_id)
        if not novel:
            return None
        content_bytes = await file_manager.read_file(novel.file_path)
        encoding = _detect_encoding(content_bytes)
        content = content_bytes.decode(encoding, errors="replace")
        chapters_data = split_into_chapters(content)

        for i, ch in enumerate(chapters_data):
            chapter = Chapter(
                novel_id=novel.id,
                title=ch["title"],
                order=i + 1,
                content=ch["content"],
                word_count=count_words(ch["content"]),
            )
            session.add(chapter)

        novel.total_chapters = len(chapters_data)
        novel.status = NovelStatus.READY
        await session.commit()
        return novel

    async def get_novel(self, session: AsyncSession, novel_id: int) -> Optional[Novel]:
        result = await session.execute(
            select(Novel).options(selectinload(Novel.chapters)).where(Novel.id == novel_id)
        )
        return result.scalar_one_or_none()

    async def list_novels(self, session: AsyncSession) -> list[Novel]:
        result = await session.execute(
            select(Novel).order_by(Novel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_chapter(self, session: AsyncSession, chapter_id: int) -> Optional[Chapter]:
        return await session.get(Chapter, chapter_id)

    async def delete_novel(self, session: AsyncSession, novel_id: int) -> bool:
        novel = await session.get(Novel, novel_id)
        if not novel:
            return False
        await session.delete(novel)
        await session.commit()
        return True


novel_service = NovelService()
