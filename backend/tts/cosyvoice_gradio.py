from typing import Optional
import httpx

from .base import BaseTTS


_COSYVOICE_VOICES = [
    "成年女性_1",
    "成年男性_1",
    "未成年女性",
    "未成年男性",
    "老年女性",
    "老年男性",
]


class CosyVoiceGradioTTS(BaseTTS):
    def __init__(self, api_base: str = "", default_voice: str = "", **kwargs):
        self._api_base = (api_base or "http://localhost:50000").rstrip("/")
        self._default_voice = default_voice
        self._client = httpx.AsyncClient(timeout=300.0)

    @property
    def name(self) -> str:
        return "cosyvoice_gradio"

    @property
    def supports_voice_upload(self) -> bool:
        return False

    @property
    def available_voices(self) -> list[str]:
        return list(_COSYVOICE_VOICES)

    async def synthesize(self, text: str, voice_tag: str = "", voice_data: Optional[bytes] = None, **kwargs) -> bytes:
        voice = voice_tag or self._default_voice or "成年女性_1"
        try:
            resp = await self._client.post(
                f"{self._api_base}/gradio_api/api/generate_audio/",
                json={
                    "data": [
                        text,
                        "预训练音色",
                        voice,
                        "",
                        None,
                        None,
                        "",
                        0,
                        False,
                        1.0,
                    ]
                },
                timeout=300.0,
            )
            resp.raise_for_status()
            result = resp.json()
            audio_url = result["data"][0]["url"]
            audio_resp = await self._client.get(audio_url, timeout=60.0)
            audio_resp.raise_for_status()
            return audio_resp.content
        except httpx.RequestError as e:
            raise ConnectionError(f"无法连接到 CosyVoice 服务器 ({self._api_base})：{e}")
        except (KeyError, IndexError, httpx.HTTPStatusError) as e:
            raise RuntimeError(f"CosyVoice 合成失败：{e}")
