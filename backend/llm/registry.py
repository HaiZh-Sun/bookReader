from typing import Optional
from .base import BaseLLM
from .openai_compatible import OpenAICompatibleLLM


_registry: dict[str, type[BaseLLM]] = {}


def register(name: str, cls: type[BaseLLM]):
    _registry[name] = cls


def get_llm(name: str, **kwargs) -> Optional[BaseLLM]:
    cls = _registry.get(name)
    if cls is None:
        return None
    return cls(**kwargs)


def list_providers() -> list[str]:
    return list(_registry.keys())


register("openai_compatible", OpenAICompatibleLLM)
