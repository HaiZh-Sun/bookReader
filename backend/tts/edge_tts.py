from typing import Optional
from .base import BaseTTS

try:
    import edge_tts
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False


EDGE_VOICES = [
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunxiaNeural",
    "zh-CN-YunyangNeural",
    "zh-HK-HiuGaaiNeural",
    "zh-HK-HiuMaanNeural",
    "zh-HK-WanLungNeural",
    "zh-TW-HsiaoChenNeural",
    "zh-TW-HsiaoYuNeural",
    "zh-TW-YunJheNeural",
]


class EdgeTTS(BaseTTS):
    def __init__(self, default_voice: str = "zh-CN-XiaoxiaoNeural", **kwargs):
        self._default_voice = default_voice

    @property
    def name(self) -> str:
        return "edge_tts"

    @property
    def available_voices(self) -> list[str]:
        return EDGE_VOICES

    async def synthesize(self, text: str, voice_tag: str = "", voice_data: Optional[bytes] = None, **kwargs) -> bytes:
        if not EDGE_AVAILABLE:
            raise RuntimeError("edge-tts 未安装，请执行: pip install edge-tts")
        voice = voice_tag or self._default_voice
        communicate = edge_tts.Communicate(text, voice)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        return b"".join(audio_chunks)
