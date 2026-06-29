from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from schemas.analysis import (
    CharacterOut, DialogueLineOut, CharacterMerge, CharacterRename,
    CharacterVoiceUpdate, CharacterAttrUpdate,
    DialogueLineUpdateCharacter, DialogueLineUpdateText,
)
from core.analysis_service import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/chapters/{chapter_id}/analyze")
async def analyze_chapter(chapter_id: int):
    result = await analysis_service.analyze_chapter(chapter_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.post("/chapters/{chapter_id}/cancel")
async def cancel_analysis(chapter_id: int):
    analysis_service.cancel(chapter_id)
    return {"ok": True}


@router.get("/progress/{chapter_id}")
async def get_analysis_progress(chapter_id: int):
    return analysis_service.get_progress(chapter_id)


@router.get("/chapters/{chapter_id}")
async def get_analysis(chapter_id: int, session: AsyncSession = Depends(get_session)):
    result = await analysis_service.get_analysis(session, chapter_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return {
        "characters": [CharacterOut.model_validate(c) for c in result["characters"]],
        "dialogue_lines": [DialogueLineOut.model_validate(d) for d in result["dialogue_lines"]],
        "voice_attrs": result.get("voice_attrs", {}),
    }


@router.post("/novels/{novel_id}/characters/merge")
async def merge_characters(
    novel_id: int,
    body: CharacterMerge,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.merge_characters(session, novel_id, body.source_ids, body.target_id)
    return {"ok": True}


@router.patch("/characters/{character_id}/rename")
async def rename_character(
    character_id: int,
    body: CharacterRename,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.rename_character(session, character_id, body.name)
    return {"ok": True}


@router.patch("/characters/{character_id}/voice")
async def set_character_voice(
    character_id: int,
    body: CharacterVoiceUpdate,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.set_character_voice(session, character_id, body.voice_tag)
    return {"ok": True}


@router.patch("/characters/{character_id}/attrs")
async def update_character_attrs(
    character_id: int,
    body: CharacterAttrUpdate,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.update_character_attrs(session, character_id, body)
    return {"ok": True}


@router.patch("/dialogue-lines/{line_id}/character")
async def update_dialogue_character(
    line_id: int,
    body: DialogueLineUpdateCharacter,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.update_dialogue_character(session, line_id, body.character_id)
    return {"ok": True}


@router.patch("/dialogue-lines/{line_id}/text")
async def update_dialogue_text(
    line_id: int,
    body: DialogueLineUpdateText,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.update_dialogue_text(session, line_id, body.text)
    return {"ok": True}


@router.delete("/dialogue-lines/{line_id}")
async def delete_dialogue_line(
    line_id: int,
    session: AsyncSession = Depends(get_session),
):
    await analysis_service.delete_dialogue_line(session, line_id)
    return {"ok": True}
