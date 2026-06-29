"""
CosyVoice API Server

在另一台机器（有 GPU）上运行此服务：
  python cosyvoice_server.py --model_dir /path/to/CosyVoice-300M --port 5000

然后在本项目的设置页面将 TTS provider 设为 cosyvoice，
并配置 COSYVOICE_API_BASE 指向该服务器的地址。

依赖：
  pip install cosyvoice fastapi uvicorn soundfile
"""

import argparse
import io
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
import uvicorn

app = FastAPI(title="CosyVoice TTS Server")

cosyvoice = None
model_loaded = False


@app.on_event("startup")
async def startup():
    global cosyvoice, model_loaded
    model_dir = os.environ.get("COSYVOICE_MODEL_DIR", "")
    if not model_dir:
        print("WARNING: COSYVOICE_MODEL_DIR not set, model not loaded at startup")
        return
    if not os.path.exists(model_dir):
        print(f"WARNING: model dir not found: {model_dir}")
        return
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice
        cosyvoice = CosyVoice(model_dir)
        model_loaded = True
        print(f"CosyVoice model loaded from {model_dir}")
    except Exception as e:
        print(f"Failed to load model: {e}")


def _ensure_model():
    if not model_loaded or cosyvoice is None:
        raise HTTPException(503, "CosyVoice model not loaded. Set COSYVOICE_MODEL_DIR and restart.")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model_loaded,
    }


@app.post("/synthesize")
async def synthesize(
    text: str = Form(...),
    voice_tag: str = Form(""),
):
    """
    标准 TTS 合成（无音色克隆）。
    voice_tag 在 CosyVoice 中可以指定预设说话人。
    """
    _ensure_model()
    try:
        if voice_tag:
            output = cosyvoice.inference_sft(text, voice_tag)
        else:
            output = cosyvoice.inference_sft(text)
        return _audio_response(output)
    except Exception as e:
        raise HTTPException(500, f"Synthesis failed: {e}")


@app.post("/synthesize_with_voice")
async def synthesize_with_voice(
    text: str = Form(...),
    voice_file: UploadFile = File(...),
):
    """
    音色克隆 TTS 合成。
    上传一段参考音频（wav/mp3），服务端用该音色朗读 text。
    """
    _ensure_model()
    try:
        content = await voice_file.read()
        suffix = Path(voice_file.filename or "voice.wav").suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            output = cosyvoice.inference_zero_shot(text, tmp_path)
            return _audio_response(output)
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(500, f"Voice cloning failed: {e}")


def _audio_response(output):
    """将 CosyVoice 输出（numpy array）转为 WAV 返回"""
    import soundfile as sf
    import numpy as np

    buf = io.BytesIO()
    # output 通常是 (t,) 的 numpy array
    if isinstance(output, list):
        audio_data = output[0]['tts_speech'].numpy()
    else:
        audio_data = output
    sf.write(buf, audio_data, 22050, format="WAV")
    buf.seek(0)
    return Response(content=buf.read(), media_type="audio/wav")


def main():
    parser = argparse.ArgumentParser(description="CosyVoice TTS Server")
    parser.add_argument("--model_dir", default=os.environ.get("COSYVOICE_MODEL_DIR", ""),
                        help="CosyVoice model directory")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    if args.model_dir:
        os.environ["COSYVOICE_MODEL_DIR"] = args.model_dir

    print(f"Starting CosyVoice TTS Server on {args.host}:{args.port}")
    print(f"Model dir: {args.model_dir or '(not set, use env COSYVOICE_MODEL_DIR)'}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
