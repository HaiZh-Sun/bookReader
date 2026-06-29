# BookReader — 有声书自动生成系统

将小说自动转换为有声书：智能识别对话角色、匹配音色、语音合成。

---

## 功能特色 / Features

### 🇨🇳 中文

| 功能 | 说明 |
|------|------|
| **小说上传与章节解析** | 支持 `.txt` / `.md` 格式，自动检测编码（UTF‑8/GBK/Big5），智能拆分为章节 |
| **对话-旁白分离** | 混合策略：正则表达式高置信度匹配（75%+）+ LLM 低置信度消歧，节省约 80% Token |
| **角色识别与属性推断** | 自动识别说话人，推断年龄组（少儿/成年/老）和性别，自动匹配音色 |
| **多 TTS 引擎支持** | 内置 Edge‑TTS（云端）和 CosyVoice（本地/远程 GPU 服务器） |
| **插件式 Provider 架构** | 可扩展的 LLM 和 TTS 提供者注册机制，易于接入新引擎 |
| **音色属性管理** | 可编辑每个音色的年龄段、性别、描述，支持试听 |
| **分批后台分析** | 长文本自动分批调用 LLM，前端轮询进度，可随时中断 |
| **批量 TTS 生成** | 逐句合成，完成一段即展示一段，支持顺序播放与音频导出（MP3/ZIP） |
| **角色合并与编辑** | 合并重复角色，重命名，修改对话归属和文本内容 |
| **Token 用量追踪** | 记录每次 LLM 调用的 Prompt/Completion Token 数，可开关显示 |
| **设置持久化** | 所有配置保存到 JSON 文件，重启不丢失 |

### 🇬🇧 English

| Feature | Description |
|---------|-------------|
| **Novel Upload & Chapter Parsing** | Supports `.txt` / `.md` with auto‑encoding detection (UTF‑8/GBK/Big5), smart chapter splitting |
| **Dialogue-Narration Separation** | Hybrid approach: regex (75%+ coverage, zero token cost) + LLM disambiguation for ambiguous paragraphs, saving ~80% tokens |
| **Character Recognition & Attribute Inference** | Automatically identifies speakers, infers age group (child/adult/elderly) and gender, auto‑assigns matching voice |
| **Multi‑TTS Engine Support** | Built‑in Edge‑TTS (cloud) and CosyVoice (local / remote GPU server) |
| **Plugin‑Style Provider Architecture** | Extensible registry for both LLM and TTS providers — easy to add new engines |
| **Voice Attribute Management** | Editable age group, gender, and description per voice; preview before use |
| **Background Analysis with Batching** | Long texts are split into batches for LLM; frontend polls progress; cancel anytime |
| **Batch TTS Generation** | Synthesizes sentence by sentence, displays incrementally; supports sequential playback and export (MP3/ZIP) |
| **Character Merge & Editing** | Merge duplicate characters, rename, reassign dialogue ownership, edit text inline |
| **Token Usage Tracking** | Records prompt/completion tokens per LLM call; toggle display on/off |
| **Persistent Settings** | All configurations saved to JSON file, survives restarts |

---

## 技术栈 / Tech Stack

- **Frontend**: Vue 3 + Vite
- **Backend**: Python FastAPI + SQLAlchemy (async) + SQLite
- **LLM**: OpenAI‑compatible API (GPT‑4o‑mini etc.)
- **TTS**: Edge‑TTS (cloud), CosyVoice (local / remote via Gradio API)

## 快速开始 / Quick Start

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173
