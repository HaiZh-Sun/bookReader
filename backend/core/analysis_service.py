import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import async_session as async_session_factory
from db.models import Chapter, Character, DialogueLine, SpeakerType
from llm.registry import get_llm
from config import settings

_analysis_progress: dict[int, dict] = {}
_analysis_cancel: set[int] = set()


class AnalysisService:
    MAX_BATCH_CHARS = 4000

    async def analyze_chapter(self, chapter_id: int) -> dict:
        chapter = None
        async with async_session_factory() as session:
            chapter = await session.get(Chapter, chapter_id)

        if not chapter:
            return {"error": "chapter not found"}

        _analysis_progress[chapter_id] = {
            "status": "pending",
            "total_batches": 0,
            "completed_batches": 0,
            "token_usage": {"prompt": 0, "completion": 0, "total": 0},
        }

        asyncio.create_task(self._do_analyze(chapter_id))
        return {"status": "started", "chapter_id": chapter_id}

    def cancel(self, chapter_id: int):
        _analysis_cancel.add(chapter_id)

    @staticmethod
    def _is_cancelled(chapter_id: int) -> bool:
        return chapter_id in _analysis_cancel

    async def _do_analyze(self, chapter_id: int):
        try:
            async with async_session_factory() as session:
                await self._run_analysis(session, chapter_id)
        except Exception as e:
            if self._is_cancelled(chapter_id):
                return
            _analysis_progress[chapter_id] = {
                "status": "error",
                "error": str(e),
                "total_batches": _analysis_progress.get(chapter_id, {}).get("total_batches", 0),
                "completed_batches": _analysis_progress.get(chapter_id, {}).get("completed_batches", 0),
            }

    async def _run_analysis(self, session: AsyncSession, chapter_id: int):
        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            raise ValueError("chapter not found")

        paragraphs = [p.strip() for p in chapter.content.split("\n") if p.strip()]
        if not paragraphs:
            raise ValueError("chapter has no content")

        from utils.dialogue_parser import split_certain_ambiguous, ParsedSegment
        from tts.voice_attrs import match_voice

        # Phase 1: Rule-based parsing for all paragraphs
        certain_segments, ambiguous_indices = split_certain_ambiguous(paragraphs)

        total_tokens = 0
        has_ai = bool(ambiguous_indices and settings.llm_api_key)

        # Phase 2: LLM disambiguation for ambiguous paragraphs
        _analysis_progress[chapter_id] = {
            "status": "analyzing",
            "total_batches": 0,
            "completed_batches": 0,
            "token_usage": {"prompt": 0, "completion": 0, "total": 0},
        }

        if has_ai:
            llm = get_llm(
                settings.llm_provider,
                api_key=settings.llm_api_key,
                api_base=settings.llm_api_base,
                model=settings.llm_model,
            )
            if llm:
                ambiguous_paras = [paragraphs[i] for i in ambiguous_indices]
                batches = self._split_batches(ambiguous_paras)
                _analysis_progress[chapter_id]["total_batches"] = len(batches)

                for batch_idx, batch_paras in enumerate(batches):
                    if self._is_cancelled(chapter_id):
                        _analysis_progress[chapter_id]["status"] = "cancelled"
                        return
                    batch_text = "\n".join(batch_paras)
                    try:
                        result = await llm.analyze_dialogue(batch_text)
                        tu = result.token_usage
                        total_tokens += tu.total_tokens
                        _analysis_progress[chapter_id]["token_usage"]["prompt"] += tu.prompt_tokens
                        _analysis_progress[chapter_id]["token_usage"]["completion"] += tu.completion_tokens
                        _analysis_progress[chapter_id]["token_usage"]["total"] += tu.total_tokens
                        for seg in result.segments:
                            certain_segments.append(ParsedSegment(
                                text=seg.text,
                                raw_text=paragraphs[seg.paragraph_index] if seg.paragraph_index < len(paragraphs) else "",
                                speaker=seg.speaker,
                                speaker_type=seg.speaker_type,
                                confidence=0.85,
                                paragraph_index=seg.paragraph_index,
                                age_group=getattr(seg, 'age_group', '成年') or '成年',
                                gender=getattr(seg, 'gender', '男') or '男',
                            ))
                    except Exception:
                        for para in batch_paras:
                            idx = paragraphs.index(para)
                            certain_segments.append(ParsedSegment(
                                text=para, raw_text=para,
                                speaker="旁白", speaker_type="narrator",
                                confidence=0.5, paragraph_index=idx,
                            ))
                    _analysis_progress[chapter_id]["completed_batches"] = batch_idx + 1

        if self._is_cancelled(chapter_id):
            _analysis_progress[chapter_id]["status"] = "cancelled"
            return

        # Fallback: unhandled ambiguous paragraphs → treat as narrator
        handled_indices = {s.paragraph_index for s in certain_segments}
        for i in range(len(paragraphs)):
            if i not in handled_indices:
                certain_segments.append(ParsedSegment(
                    text=paragraphs[i], raw_text=paragraphs[i],
                    speaker="旁白", speaker_type="narrator",
                    confidence=0.5, paragraph_index=i,
                ))

        certain_segments.sort(key=lambda s: s.paragraph_index)

        characters_map: dict[str, Character] = {}
        char_attrs: dict[str, tuple[str, str]] = {}
        narrator_char: Optional[Character] = None
        global_order = 0

        old_lines = await session.execute(
            select(DialogueLine).where(DialogueLine.chapter_id == chapter_id)
        )
        for dl in old_lines.scalars().all():
            await session.delete(dl)
        await session.commit()

        for seg in certain_segments:
            if seg.speaker_type == "character" and seg.speaker and seg.speaker != "旁白":
                age = seg.age_group or "成年"
                gdr = seg.gender or "男"
                if seg.speaker not in char_attrs:
                    char_attrs[seg.speaker] = (age, gdr)
                else:
                    existing = char_attrs[seg.speaker]
                    if existing[0] == "成年" and age != "成年":
                        char_attrs[seg.speaker] = (age, gdr)
                if seg.speaker not in characters_map:
                    existing = await session.execute(
                        select(Character).where(
                            Character.novel_id == chapter.novel_id,
                            Character.name == seg.speaker,
                        ).limit(1)
                    )
                    char = existing.scalar_one_or_none()
                    if not char:
                        age, gdr = char_attrs.get(seg.speaker, ("成年", "男"))
                        char = Character(
                            novel_id=chapter.novel_id,
                            name=seg.speaker,
                            speaker_type=SpeakerType.CHARACTER,
                            age_group=age,
                            gender=gdr,
                        )
                        session.add(char)
                        await session.flush()
                    characters_map[seg.speaker] = char

            if narrator_char is None:
                existing = await session.execute(
                    select(Character).where(
                        Character.novel_id == chapter.novel_id,
                        Character.name == "旁白",
                    ).limit(1)
                )
                narrator_char = existing.scalar_one_or_none()
                if not narrator_char:
                    narrator_char = Character(
                        novel_id=chapter.novel_id,
                        name="旁白",
                        speaker_type=SpeakerType.NARRATOR,
                        age_group="成年",
                        gender="男",
                    )
                    session.add(narrator_char)
                    await session.flush()

            is_char = seg.speaker_type == "character" and seg.speaker and seg.speaker != "旁白"
            char = characters_map.get(seg.speaker) if is_char else narrator_char

            dl = DialogueLine(
                chapter_id=chapter_id,
                character_id=char.id if char else None,
                text=seg.text,
                speaker_type=SpeakerType.CHARACTER if is_char else SpeakerType.NARRATOR,
                order=global_order,
                paragraph_index=global_order,
            )
            session.add(dl)
            global_order += 1

        await session.commit()

        # Auto-assign voices based on character age/gender
        all_chars = (await session.execute(
            select(Character).where(Character.novel_id == chapter.novel_id)
        )).scalars().all()
        tts_provider = settings.tts_provider
        from tts.registry import get_tts
        tts_kw = {"default_voice": settings.tts_edge_voice}
        if tts_provider in ("cosyvoice", "cosyvoice_gradio"):
            tts_kw["api_base"] = settings.tts_cosyvoice_api_base
            tts_kw["default_voice"] = settings.tts_cosyvoice_default_voice
        tts = get_tts(tts_provider, **tts_kw)
        available = tts.available_voices if tts else []
        for ch in all_chars:
            if not ch.voice_tag and ch.name != "旁白":
                matched = match_voice(ch.age_group, ch.gender, available)
                if matched:
                    ch.voice_tag = matched
        await session.commit()
        _analysis_cancel.discard(chapter_id)
        prog = _analysis_progress[chapter_id]
        if prog["total_batches"] == 0:
            prog["total_batches"] = 1
        prog["completed_batches"] = prog["total_batches"]
        prog["status"] = "completed"

    def _split_batches(self, paragraphs: list[str]) -> list[list[str]]:
        batches = []
        current = []
        length = 0
        for p in paragraphs:
            if length + len(p) > self.MAX_BATCH_CHARS and current:
                batches.append(current)
                current = [p]
                length = len(p)
            else:
                current.append(p)
                length += len(p)
        if current:
            batches.append(current)
        return batches

    def get_progress(self, chapter_id: int) -> dict:
        return _analysis_progress.get(chapter_id, {
            "status": "unknown",
            "total_batches": 0,
            "completed_batches": 0,
            "token_usage": {"prompt": 0, "completion": 0, "total": 0},
        })

    async def get_analysis(self, session: AsyncSession, chapter_id: int) -> dict:
        chapter = await session.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "chapter not found"}

        characters = await session.execute(
            select(Character).where(Character.novel_id == chapter.novel_id)
        )
        lines = await session.execute(
            select(DialogueLine).where(DialogueLine.chapter_id == chapter_id).order_by(DialogueLine.order)
        )
        from tts.voice_attrs import all_voice_attrs
        from tts.registry import get_tts
        tts_provider = settings.tts_provider
        tts_kw = {"default_voice": settings.tts_edge_voice}
        if tts_provider in ("cosyvoice", "cosyvoice_gradio"):
            tts_kw["api_base"] = settings.tts_cosyvoice_api_base
            tts_kw["default_voice"] = settings.tts_cosyvoice_default_voice
        tts = get_tts(tts_provider, **tts_kw)
        all_attrs = all_voice_attrs()
        voice_attrs_res = {}
        if tts:
            for v in tts.available_voices:
                if v in all_attrs:
                    voice_attrs_res[v] = all_attrs[v]
        return {
            "characters": list(characters.scalars().all()),
            "dialogue_lines": list(lines.scalars().all()),
            "voice_attrs": voice_attrs_res,
        }

    async def merge_characters(self, session: AsyncSession, novel_id: int, source_ids: list[int], target_id: int):
        target_char = await session.get(Character, target_id)
        if not target_char:
            raise ValueError("target character not found")

        for cid in source_ids:
            char = await session.get(Character, cid)
            if char and char.id != target_char.id:
                lines = await session.execute(
                    select(DialogueLine).where(DialogueLine.character_id == char.id)
                )
                for dl in lines.scalars().all():
                    dl.character_id = target_char.id
                char.is_merged = True
                char.merged_into_id = target_char.id

        await session.commit()

    async def rename_character(self, session: AsyncSession, character_id: int, new_name: str):
        char = await session.get(Character, character_id)
        if char:
            char.name = new_name
            await session.commit()

    async def set_character_voice(self, session: AsyncSession, character_id: int, voice_tag: str):
        char = await session.get(Character, character_id)
        if char:
            char.voice_tag = voice_tag
            await session.commit()

    async def update_character_attrs(self, session: AsyncSession, character_id: int, body):
        char = await session.get(Character, character_id)
        if char:
            if body.age_group is not None:
                char.age_group = body.age_group
            if body.gender is not None:
                char.gender = body.gender
            await session.commit()

    async def update_dialogue_character(self, session: AsyncSession, line_id: int, character_id: Optional[int]):
        dl = await session.get(DialogueLine, line_id)
        if not dl:
            raise ValueError("dialogue line not found")
        dl.character_id = character_id
        await session.commit()

    async def update_dialogue_text(self, session: AsyncSession, line_id: int, text: str):
        dl = await session.get(DialogueLine, line_id)
        if not dl:
            raise ValueError("dialogue line not found")
        dl.text = text
        await session.commit()

    async def delete_dialogue_line(self, session: AsyncSession, line_id: int):
        dl = await session.get(DialogueLine, line_id)
        if not dl:
            raise ValueError("dialogue line not found")
        await session.delete(dl)
        await session.commit()


analysis_service = AnalysisService()
