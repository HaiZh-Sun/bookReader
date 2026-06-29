from abc import ABC, abstractmethod
from typing import Optional


class BaseTTS(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice_tag: str = "", voice_data: Optional[bytes] = None, **kwargs) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def supports_voice_upload(self) -> bool:
        return False

    @property
    def available_voices(self) -> list[str]:
        return []
