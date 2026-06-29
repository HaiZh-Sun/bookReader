from typing import Optional
from .base import BaseTTS
from .edge_tts import EdgeTTS
from .cosyvoice import CosyVoiceTTS
from .cosyvoice_gradio import CosyVoiceGradioTTS


_registry: dict[str, type[BaseTTS]] = {}


def register(name: str, cls: type[BaseTTS]):
    _registry[name] = cls


def get_tts(name: str, **kwargs) -> Optional[BaseTTS]:
    cls = _registry.get(name)
    if cls is None:
        return None
    return cls(**kwargs)


def list_providers() -> list[str]:
    return list(_registry.keys())


register("edge_tts", EdgeTTS)
register("cosyvoice", CosyVoiceTTS)
register("cosyvoice_gradio", CosyVoiceGradioTTS)
