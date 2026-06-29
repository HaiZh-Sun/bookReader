from fastapi import APIRouter, HTTPException
from config import settings
from schemas.settings import (
    SettingsOut, LLMConfigOut, TTSConfigOut,
    LLMConfigUpdate, TTSConfigUpdate, SettingsUpdate,
)
from llm.registry import list_providers as list_llm_providers
from tts.registry import list_providers as list_tts_providers, get_tts

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings():
    from tts.voice_attrs import all_voice_attrs
    tts_voices = []
    tts_voice_attrs = {}
    tts_kw = {"default_voice": settings.tts_edge_voice}
    if settings.tts_provider in ("cosyvoice", "cosyvoice_gradio"):
        tts_kw["api_base"] = settings.tts_cosyvoice_api_base
        tts_kw["default_voice"] = settings.tts_cosyvoice_default_voice
    instance = get_tts(settings.tts_provider, **tts_kw)
    if instance:
        tts_voices = instance.available_voices
        full = all_voice_attrs()
        tts_voice_attrs = {k: full[k] for k in tts_voices if k in full}
    return SettingsOut(
        llm=LLMConfigOut(
            provider=settings.llm_provider,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
            api_key_set=bool(settings.llm_api_key),
        ),
        tts=TTSConfigOut(
            provider=settings.tts_provider,
            edge_voice=settings.tts_edge_voice,
            cosyvoice_api_base=settings.tts_cosyvoice_api_base,
            cosyvoice_default_voice=settings.tts_cosyvoice_default_voice,
            voices=tts_voices,
            voice_attrs=tts_voice_attrs,
        ),
        show_token_usage=settings.show_token_usage,
    )


@router.patch("/llm")
async def update_llm(body: LLMConfigUpdate):
    if body.provider is not None:
        settings.llm_provider = body.provider
    if body.api_base is not None:
        settings.llm_api_base = body.api_base
    if body.api_key is not None:
        settings.llm_api_key = body.api_key
    if body.model is not None:
        settings.llm_model = body.model
    settings.save()
    return {"ok": True}


@router.patch("/tts")
async def update_tts(body: TTSConfigUpdate):
    if body.provider is not None:
        settings.tts_provider = body.provider
    if body.edge_voice is not None:
        settings.tts_edge_voice = body.edge_voice
    if body.cosyvoice_api_base is not None:
        settings.tts_cosyvoice_api_base = body.cosyvoice_api_base
    if body.cosyvoice_default_voice is not None:
        settings.tts_cosyvoice_default_voice = body.cosyvoice_default_voice
    settings.save()
    return {"ok": True}


@router.patch("")
async def update_settings(body: SettingsUpdate):
    if body.show_token_usage is not None:
        settings.show_token_usage = body.show_token_usage
    settings.save()
    return {"ok": True}


@router.patch("/voices/attrs")
async def update_voice_attrs(body: dict):
    settings.voice_attrs_overrides = body
    settings.save()
    from tts.voice_attrs import load_overrides
    load_overrides(body)
    return {"ok": True}


@router.get("/providers")
async def list_providers():
    return {
        "llm": list_llm_providers(),
        "tts": list_tts_providers(),
    }
