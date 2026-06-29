from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TTSConfig(BaseModel):
    provider: str = "edge_tts"
    voice_tag: str = ""
    speed: float = 1.0


class TTSGenerateRequest(BaseModel):
    chapter_id: int
    provider: str = "edge_tts"
    voice_overrides: dict[int, str] = {}
    speed: float = 1.0


class AudioRecordOut(BaseModel):
    id: int
    dialogue_line_id: int
    chapter_id: int
    file_path: str
    status: str
    duration_ms: int
    tts_provider: str
    voice_tag: str
    error_message: str

    model_config = {"from_attributes": True}


class TTSProgress(BaseModel):
    chapter_id: int
    total: int
    completed: int
    failed: int
    status: str
