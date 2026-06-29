from pydantic import BaseModel
from typing import Optional, List


class LLMConfigOut(BaseModel):
    provider: str
    api_base: str
    model: str
    api_key_set: bool


class TTSConfigOut(BaseModel):
    provider: str
    edge_voice: str
    cosyvoice_api_base: str
    cosyvoice_default_voice: str
    voices: list[str] = []
    voice_attrs: dict[str, dict] = {}


class SettingsOut(BaseModel):
    llm: LLMConfigOut
    tts: TTSConfigOut
    show_token_usage: bool = False


class SettingsUpdate(BaseModel):
    show_token_usage: Optional[bool] = None


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class TTSConfigUpdate(BaseModel):
    provider: Optional[str] = None
    edge_voice: Optional[str] = None
    cosyvoice_api_base: Optional[str] = None
    cosyvoice_default_voice: Optional[str] = None
