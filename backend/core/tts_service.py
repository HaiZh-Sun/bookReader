import os
import tempfile
import zipfile
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import async_session as async_session_factory
from db.models import DialogueLine, AudioRecord, AudioStatus, Chapter
from tts.registry import get_tts
from config import settings
from storage.file_manager import file_manager


_tts_progress: dict[int, dict] = {}
_tts_cancel: set[int] = set()


class TTSService:
    async def generate_chapter(
        self,
        chapter_id: int,
        provider: str = "",
        voice_overrides: dict[int, str] = {},
    ) -> dict:
        async with async_session_factory() as session:
            chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "chapter not found"}

        _tts_progress[chapter_id] = {
            "status": "pending",
            "total": 0,
            "completed": 0,
            "failed": 0,
        }

        asyncio.create_task(
            self._do_generate(chapter_id, provider, voice_overrides)
        )
        return {"status": "started", "chapter_id": chapter_id}

    def cancel(self, chapter_id: int):
        _tts_cancel.add(chapter_id)

    @staticmethod
    def _is_cancelled(chapter_id: int) -> bool:
        return chapter_id in _tts_cancel

    async def _do_generate(
        self,
        chapter_id: int,
        provider: str = "",
        voice_overrides: dict[int, str] = {},
    ):
        try:
            async with async_session_factory() as session:
                await self._run_generate(session, chapter_id, provider, voice_overrides)
        except Exception as e:
            if self._is_cancelled(chapter_id):
                return
            _tts_progress[chapter_id] = {
                "status": "error",
                "error": str(e),
                "total": _tts_progress.get(chapter_id, {}).get("total", 0),
                "completed": _tts_progress.get(chapter_id, {}).get("completed", 0),
                "failed": _tts_progress.get(chapter_id, {}).get("failed", 0),
            }

    async def _run_generate(
        self,
        session: AsyncSession,
        chapter_id: int,
        provider: str = "",
        voice_overrides: dict[int, str] = {},
    ):
        tts_provider = provider or settings.tts_provider
        tts_kwargs = {"default_voice": settings.tts_edge_voice}
        if tts_provider in ("cosyvoice", "cosyvoice_gradio"):
            tts_kwargs["api_base"] = settings.tts_cosyvoice_api_base
            tts_kwargs["default_voice"] = settings.tts_cosyvoice_default_voice
        tts = get_tts(tts_provider, **tts_kwargs)
        if not tts:
            raise ValueError(f"TTS provider '{tts_provider}' not available")

        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError("chapter not found")

        old_records = await session.execute(
            select(AudioRecord).where(AudioRecord.chapter_id == chapter_id)
        )
        for rec in old_records.scalars().all():
            if rec.file_path and os.path.exists(rec.file_path):
                os.remove(rec.file_path)
            await session.delete(rec)
        await session.commit()

        lines_result = await session.execute(
            select(DialogueLine)
            .where(DialogueLine.chapter_id == chapter_id)
            .order_by(DialogueLine.order)
        )
        lines = list(lines_result.scalars().all())

        total = len(lines)
        _tts_progress[chapter_id] = {
            "status": "generating",
            "total": total,
            "completed": 0,
            "failed": 0,
        }

        records = []
        for dl in lines:
            if self._is_cancelled(chapter_id):
                _tts_progress[chapter_id]["status"] = "cancelled"
                return
            voice_tag = voice_overrides.get(dl.character_id or 0, "")
            record = AudioRecord(
                dialogue_line_id=dl.id,
                chapter_id=chapter_id,
                status=AudioStatus.PENDING,
                tts_provider=tts_provider,
                voice_tag=voice_tag,
            )
            session.add(record)
            await session.flush()
            records.append(record)

            try:
                audio_data = await tts.synthesize(dl.text, voice_tag=voice_tag)
                file_path = await file_manager.save_audio(audio_data, dl.id, chapter_id)
                record.file_path = file_path
                record.status = AudioStatus.COMPLETED
                _tts_progress[chapter_id]["completed"] += 1
            except Exception as e:
                record.status = AudioStatus.ERROR
                record.error_message = str(e)
                _tts_progress[chapter_id]["failed"] += 1

            await session.commit()

        _tts_cancel.discard(chapter_id)
        _tts_progress[chapter_id]["status"] = "completed"

    def get_progress(self, chapter_id: int) -> dict:
        return _tts_progress.get(chapter_id, {
            "status": "unknown",
            "total": 0,
            "completed": 0,
            "failed": 0,
        })

    async def get_db_progress(self, session: AsyncSession, chapter_id: int) -> dict:
        records = await session.execute(
            select(AudioRecord).where(AudioRecord.chapter_id == chapter_id)
        )
        all_records = list(records.scalars().all())
        total = len(all_records)
        completed = sum(1 for r in all_records if r.status == AudioStatus.COMPLETED)
        failed = sum(1 for r in all_records if r.status == AudioStatus.ERROR)
        status = "idle"
        if total > 0 and completed + failed == total:
            status = "completed"
        elif total > 0:
            status = "generating"
        return {
            "chapter_id": chapter_id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "status": status,
        }

    async def get_audio_results(self, session: AsyncSession, chapter_id: int) -> list[AudioRecord]:
        records = await session.execute(
            select(AudioRecord)
            .where(AudioRecord.chapter_id == chapter_id)
            .order_by(AudioRecord.id)
        )
        return list(records.scalars().all())

    async def save_voice_file(self, content: bytes, filename: str) -> str:
        return await file_manager.save_voice(content, filename)

    async def list_voice_files(self) -> list[dict]:
        voices = []
        if os.path.exists(settings.voice_dir):
            for f in os.listdir(settings.voice_dir):
                fpath = os.path.join(settings.voice_dir, f)
                voices.append({
                    "name": f,
                    "path": fpath,
                    "size": os.path.getsize(fpath),
                })
        return voices

    async def export_chapter_audio(self, session: AsyncSession, chapter_id: int) -> bytes:
        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError("chapter not found")

        records = await session.execute(
            select(AudioRecord)
            .where(
                AudioRecord.chapter_id == chapter_id,
                AudioRecord.status == AudioStatus.COMPLETED,
            )
            .order_by(AudioRecord.id)
        )
        all_records = list(records.scalars().all())
        if not all_records:
            raise ValueError("no completed audio records found")

        try:
            from pydub import AudioSegment

            combined = AudioSegment.empty()
            for rec in all_records:
                if rec.file_path and os.path.exists(rec.file_path):
                    seg = AudioSegment.from_file(rec.file_path, format="mp3")
                    combined += seg

            buf = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            try:
                combined.export(buf.name, format="mp3")
                with open(buf.name, "rb") as f:
                    return f.read()
            finally:
                os.unlink(buf.name)

        except ImportError:
            return await self._export_as_zip(chapter_id, all_records)
        except Exception:
            return await self._export_as_zip(chapter_id, all_records)

    async def _export_as_zip(
        self, chapter_id: int, records: list[AudioRecord]
    ) -> bytes:
        import io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, rec in enumerate(records):
                if rec.file_path and os.path.exists(rec.file_path):
                    arcname = f"{i+1:04d}_{rec.id}.mp3"
                    zf.write(rec.file_path, arcname)
        return buf.getvalue()


tts_service = TTSService()
