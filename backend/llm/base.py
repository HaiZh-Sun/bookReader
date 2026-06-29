from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class DialogueSegment(BaseModel):
    text: str
    speaker: str
    speaker_type: str
    paragraph_index: int
    age_group: str = "成年"
    gender: str = "男"


class AnalysisResult(BaseModel):
    segments: list[DialogueSegment]
    characters: list[str]
    token_usage: TokenUsage = TokenUsage()


class BaseLLM(ABC):
    @abstractmethod
    async def analyze_dialogue(self, text: str, context: Optional[dict] = None) -> AnalysisResult:
        raise NotImplementedError

    async def disambiguate_speakers(self, segments: list[DialogueSegment]) -> list[DialogueSegment]:
        """Lightweight call to resolve ambiguous speaker assignments.
        Default implementation just returns segments unchanged."""
        return segments

    @abstractmethod
    async def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
