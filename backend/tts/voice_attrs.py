"""
Voice attribute registry — maps each voice name to its age_group and gender.
Used for auto-assigning voices to characters based on LLM extraction.
User overrides are loaded from global settings.
"""

_DEFAULT_ATTRS: dict[str, dict] = {
    # CosyVoice gradio voices
    "成年女性_1":  {"age_group": "成年", "gender": "女", "description": ""},
    "成年男性_1":  {"age_group": "成年", "gender": "男", "description": ""},
    "未成年女性":  {"age_group": "少儿", "gender": "女", "description": ""},
    "未成年男性":  {"age_group": "少儿", "gender": "男", "description": ""},
    "老年女性":    {"age_group": "老",   "gender": "女", "description": ""},
    "老年男性":    {"age_group": "老",   "gender": "男", "description": ""},

    # Edge-TTS Chinese voices
    "zh-CN-XiaoxiaoNeural":  {"age_group": "成年", "gender": "女", "description": ""},
    "zh-CN-XiaoyiNeural":    {"age_group": "成年", "gender": "女", "description": ""},
    "zh-CN-YunjianNeural":   {"age_group": "成年", "gender": "男", "description": ""},
    "zh-CN-YunxiNeural":     {"age_group": "成年", "gender": "男", "description": ""},
    "zh-CN-YunxiaNeural":    {"age_group": "成年", "gender": "男", "description": ""},
    "zh-CN-YunyangNeural":   {"age_group": "成年", "gender": "男", "description": ""},
    "zh-HK-HiuGaaiNeural":   {"age_group": "成年", "gender": "女", "description": ""},
    "zh-HK-HiuMaanNeural":   {"age_group": "成年", "gender": "女", "description": ""},
    "zh-HK-WanLungNeural":   {"age_group": "成年", "gender": "男", "description": ""},
    "zh-TW-HsiaoChenNeural": {"age_group": "成年", "gender": "女", "description": ""},
    "zh-TW-HsiaoYuNeural":   {"age_group": "成年", "gender": "女", "description": ""},
    "zh-TW-YunJheNeural":    {"age_group": "成年", "gender": "男", "description": ""},
}

_OVERIDES: dict[str, dict] = {}


def load_overrides(data: dict[str, dict]):
    _OVERIDES.clear()
    _OVERIDES.update(data)


def get_voice_attrs(voice_name: str) -> dict:
    return _OVERIDES.get(voice_name) or _DEFAULT_ATTRS.get(voice_name) or {"age_group": "成年", "gender": "男", "description": ""}


def all_voice_attrs() -> dict[str, dict]:
    merged = dict(_DEFAULT_ATTRS)
    merged.update(_OVERIDES)
    return merged


def match_voice(age_group: str, gender: str, available_voices: list[str]) -> str:
    """Find the best matching voice for a given age_group + gender."""
    best = ""
    for v in available_voices:
        attrs = get_voice_attrs(v)
        if attrs["age_group"] == age_group and attrs["gender"] == gender:
            return v
        if attrs["gender"] == gender and not best:
            best = v
    return best or (available_voices[0] if available_voices else "")
