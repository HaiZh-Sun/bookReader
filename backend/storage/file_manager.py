import os
import aiofiles
import uuid
from pathlib import Path
from config import settings


class FileManager:
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.audio_dir = Path(settings.audio_dir)
        self.voice_dir = Path(settings.voice_dir)
        for d in [self.upload_dir, self.audio_dir, self.voice_dir]:
            d.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix or ".txt"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest = self.upload_dir / unique_name
        async with aiofiles.open(str(dest), "wb") as f:
            await f.write(content)
        return str(dest)

    async def save_audio(self, content: bytes, dialogue_line_id: int, chapter_id: int) -> str:
        chapter_dir = self.audio_dir / str(chapter_id)
        chapter_dir.mkdir(parents=True, exist_ok=True)
        dest = chapter_dir / f"{dialogue_line_id}.mp3"
        async with aiofiles.open(str(dest), "wb") as f:
            await f.write(content)
        return str(dest)

    async def save_voice(self, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest = self.voice_dir / unique_name
        async with aiofiles.open(str(dest), "wb") as f:
            await f.write(content)
        return str(dest)

    async def read_file(self, path: str) -> bytes:
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    def get_upload_path(self, relative: str) -> str:
        return str(self.upload_dir / relative)


file_manager = FileManager()
