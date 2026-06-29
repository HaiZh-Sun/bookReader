from typing import Optional
import httpx

from .base import BaseTTS


class CosyVoiceTTS(BaseTTS):
    def __init__(self, api_base: str = "", default_voice: str = "", **kwargs):
        self._api_base = (api_base or "http://localhost:5000").rstrip("/")
        self._default_voice = default_voice
        self._client = httpx.AsyncClient(timeout=300.0)

    @property
    def name(self) -> str:
        return "cosyvoice"

    @property
    def supports_voice_upload(self) -> bool:
        return True

    async def synthesize(self, text: str, voice_tag: str = "", voice_data: Optional[bytes] = None, **kwargs) -> bytes:
        if voice_data:
            return await self._synthesize_with_voice(text, voice_data, voice_tag)

        voice = voice_tag or self._default_voice or ""
        try:
            resp = await self._client.post(
                f"{self._api_base}/synthesize",
                data={"text": text, "voice_tag": voice},
                timeout=300.0,
            )
            resp.raise_for_status()
            return resp.content
        except httpx.RequestError as e:
            raise ConnectionError(f"无法连接到 CosyVoice 服务器 ({self._api_base})：{e}")

    async def _synthesize_with_voice(self, text: str, voice_data: bytes, voice_tag: str = "") -> bytes:
        try:
            files = {"voice_file": ("voice.wav", voice_data, "audio/wav")}
            resp = await self._client.post(
                f"{self._api_base}/synthesize_with_voice",
                data={"text": text, "voice_tag": voice_tag or ""},
                files=files,
                timeout=300.0,
            )
            resp.raise_for_status()
            return resp.content
        except httpx.RequestError as e:
            raise ConnectionError(f"无法连接到 CosyVoice 服务器 ({self._api_base})：{e}")
