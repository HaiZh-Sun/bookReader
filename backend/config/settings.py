import json
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "settings.json"


class Settings(BaseSettings):
    app_name: str = "BookReader"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    db_url: str = "sqlite+aiosqlite:///./data/bookreader.db"
    upload_dir: str = "./data/uploads"
    audio_dir: str = "./data/audio"
    voice_dir: str = "./data/voices"

    llm_provider: str = "openai_compatible"
    llm_api_key: Optional[str] = None
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    tts_provider: str = "edge_tts"
    tts_edge_voice: str = "zh-CN-XiaoxiaoNeural"
    tts_cosyvoice_api_base: str = "http://localhost:5000"
    tts_cosyvoice_default_voice: str = ""
    show_token_usage: bool = False
    voice_attrs_overrides: dict = {}

    model_config = {"env_prefix": "BOOKREADER_", "env_file": ".env", "extra": "allow"}

    def save(self):
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = self.model_dump(exclude={"llm_api_key"})
        if self.llm_api_key:
            data["llm_api_key"] = self.llm_api_key
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_persisted(cls) -> "Settings":
        obj = cls()
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
            except Exception:
                pass
        return obj


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.load_persisted()
        from tts.voice_attrs import load_overrides
        load_overrides(_settings.voice_attrs_overrides)
    return _settings
