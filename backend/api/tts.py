from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
import os

from db.database import get_session
from schemas.tts import TTSGenerateRequest, AudioRecordOut, TTSProgress
from core.tts_service import tts_service
from config import settings

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/preview")
async def preview_voice(body: dict):
    voice = body.get("voice", "")
    text = body.get("text", "你好，这是一个音色试听示例。")
    from tts.registry import get_tts
    from config import settings
    tts_kw = {"default_voice": settings.tts_edge_voice}
    if settings.tts_provider in ("cosyvoice", "cosyvoice_gradio"):
        tts_kw["api_base"] = settings.tts_cosyvoice_api_base
        tts_kw["default_voice"] = settings.tts_cosyvoice_default_voice
    tts = get_tts(settings.tts_provider, **tts_kw)
    if not tts:
        raise HTTPException(400, "TTS provider not available")
    try:
        audio = await tts.synthesize(text, voice_tag=voice)
        return Response(content=audio, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/cancel/{chapter_id}")
async def cancel_tts(chapter_id: int):
    tts_service.cancel(chapter_id)
    return {"ok": True}


@router.post("/generate")
async def generate_chapter(body: TTSGenerateRequest):
    result = await tts_service.generate_chapter(
        chapter_id=body.chapter_id,
        provider=body.provider,
        voice_overrides=body.voice_overrides,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/progress/{chapter_id}", response_model=TTSProgress)
async def get_tts_progress(chapter_id: int, session: AsyncSession = Depends(get_session)):
    mem = tts_service.get_progress(chapter_id)
    if mem.get("status") in ("generating", "pending"):
        return TTSProgress(
            chapter_id=chapter_id,
            total=mem.get("total", 0),
            completed=mem.get("completed", 0),
            failed=mem.get("failed", 0),
            status=mem["status"],
        )
    return await tts_service.get_db_progress(session, chapter_id)


@router.get("/results/{chapter_id}")
async def get_tts_results(chapter_id: int, session: AsyncSession = Depends(get_session)):
    records = await tts_service.get_audio_results(session, chapter_id)
    return [AudioRecordOut.model_validate(r) for r in records]


@router.post("/voices/upload")
async def upload_voice(file: UploadFile = File(...)):
    content = await file.read()
    if not file.filename:
        raise HTTPException(400, "filename required")
    path = await tts_service.save_voice_file(content, file.filename)
    return {"path": path, "name": file.filename}


@router.get("/voices")
async def list_voices():
    return await tts_service.list_voice_files()


@router.get("/download/{audio_id}")
async def download_audio(audio_id: int, session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select
    from db.models import AudioRecord

    result = await session.execute(select(AudioRecord).where(AudioRecord.id == audio_id))
    record = result.scalar_one_or_none()
    if not record or not record.file_path or not os.path.exists(record.file_path):
        raise HTTPException(404, "audio not found")
    return FileResponse(
        record.file_path,
        media_type="audio/mpeg",
        filename=f"audio_{audio_id}.mp3",
    )


@router.get("/export/{chapter_id}")
async def export_chapter_audio(chapter_id: int, session: AsyncSession = Depends(get_session)):
    try:
        data = await tts_service.export_chapter_audio(session, chapter_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    media_type = "audio/mpeg" if data[:3] == b"ID3" or data[:2] == b"\xff\xfb" else "application/zip"
    ext = "mp3" if media_type == "audio/mpeg" else "zip"
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="chapter_{chapter_id}.{ext}"'},
    )
