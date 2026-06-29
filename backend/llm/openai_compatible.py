import json
from typing import Optional
import httpx
from .base import BaseLLM, AnalysisResult, DialogueSegment, TokenUsage


SYSTEM_PROMPT = """你是一位专业的小说文本解析专家，擅长精细拆分旁白与对话。

# 输入
用户将提供一段或多段小说原文（带有段落序号）。

# 核心任务
将输入的文本拆分成一个个独立的逻辑片段（旁白片段或对话片段），并结构化输出。

# 关键规则（必须严格遵守）
1. **旁白与对话剥离**：
   - “旁白”指所有非对话的叙述性文字（包括环境描写、动作描写、以及“XX说”、“XX笑道”、“XX回答”等对话引导语）。
   - “对话”指被中文引号（“ ” 或 「 」）括起来的人物台词。

2. **内容清洗（解决你“摘除”问题的核心）**：
   - 对于**对话片段**，`text` 字段 **只保留引号内的台词原文**，必须去掉两边的引号，并 **彻底剥离** 其前后的“XX说”等引导语。
   - 对于**旁白片段**，`text` 字段保留完整的叙述原文（包含“XX说”等引导语）。

3. **说话人识别**：
   - 如果对话的引导语中明确提到了名字（如“张三说”），则对话的 `speaker` 必须取该名字（如“张三”）。
   - 如果引导语是“他说”、“她笑道”等代词，且上下文能明确指代，则使用指代的名字；若无法确定，则 `speaker` 填“未知角色”。
   - 旁白片段的 `speaker` 固定为“旁白”。

4. **顺序与结构**：
   - 输出的片段顺序必须严格按照原文的阅读顺序排列。
   - 如果一段话里既有旁白又有对话，必须拆分成多个独立的对象。

5. **角色属性**：对于 character 类型的片段，根据上下文推断说话人的年龄组（age_group: "老"/"成年"/"少儿"）和性别（gender: "男"/"女"）。旁白片段的 age_group 和 gender 忽略。

输出格式必须是 JSON 数组，每个元素对应一个段落：
- text: 清洗后的内容
- speaker: 说话人名称或"旁白"
- speaker_type: "narrator" 或 "character"
- paragraph_index: 段落序号（与输入对应）
- age_group: 说话人的年龄组，"老"/"成年"/"少儿"（非 character 类型忽略）
- gender: 说话人的性别，"男"/"女"（非 character 类型忽略）

# 示例示范
输入：
段落0：张三说："今天天气真好。"他望向窗外。
段落1："确实不错。"李四点头附和。

输出：
[
    {"text": "张三说：", "speaker": "旁白", "speaker_type": "narrator", "paragraph_index": 0, "age_group": "", "gender": ""},
    {"text": "今天天气真好。", "speaker": "张三", "speaker_type": "character", "paragraph_index": 0, "age_group": "成年", "gender": "男"},
    {"text": "他望向窗外。", "speaker": "旁白", "speaker_type": "narrator", "paragraph_index": 0, "age_group": "", "gender": ""},
    {"text": "确实不错。", "speaker": "李四", "speaker_type": "character", "paragraph_index": 1, "age_group": "成年", "gender": "男"},
    {"text": "李四点头附和。", "speaker": "旁白", "speaker_type": "narrator", "paragraph_index": 1, "age_group": "", "gender": ""}
]

现在，请严格按上述规则和格式处理以下输入，只输出 JSON，不要额外说明："""


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(timeout=120.0)
        self._last_token_usage = TokenUsage()

    @property
    def name(self) -> str:
        return f"openai_compatible/{self.model}"

    async def analyze_dialogue(self, text: str, context: Optional[dict] = None) -> AnalysisResult:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        if not paragraphs:
            return AnalysisResult(segments=[], characters=[])

        numbered = "\n\n".join(
            f"[段落 {i}]\n{p}" for i, p in enumerate(paragraphs)
        )

        resp = await self.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"分析以下小说段落：\n\n{numbered}"}
        ])

        try:
            data = json.loads(resp)
            if not isinstance(data, list):
                data = [data]
            segments = []
            for item in data:
                idx = item.get("paragraph_index", len(segments))
                is_char = item.get("speaker_type") == "character"
                segments.append(DialogueSegment(
                    text=item.get("text", paragraphs[idx] if idx < len(paragraphs) else ""),
                    speaker=item.get("speaker", "旁白"),
                    speaker_type=item.get("speaker_type", "narrator"),
                    paragraph_index=idx,
                    age_group=item.get("age_group", "成年") if is_char else "成年",
                    gender=item.get("gender", "男") if is_char else "男",
                ))
        except (json.JSONDecodeError, KeyError, TypeError):
            segments = [
                DialogueSegment(text=p, speaker="旁白", speaker_type="narrator", paragraph_index=i)
                for i, p in enumerate(paragraphs)
            ]

        characters = list(set(s.speaker for s in segments if s.speaker_type == "character"))
        return AnalysisResult(segments=segments, characters=characters, token_usage=self._last_token_usage)

    async def disambiguate_speakers(self, segments: list[DialogueSegment]) -> list[DialogueSegment]:
        """Lightweight disambiguation: given paragraphs with quotes but unknown speakers,
        ask LLM to identify who is speaking based on context."""
        if not segments:
            return segments

        lines = []
        for s in segments:
            lines.append(f"[段落 {s.paragraph_index}] {s.raw_text if hasattr(s, 'raw_text') else s.text}")

        prompt = (
            "以下是一段小说中的几个段落，每段都包含带引号的对话，但说话人未明确标注。\n"
            "请为每个段落判断说话人是谁（如果是旁白叙述则标为'旁白'）。\n"
            "根据上下文推测最合理的说话人名称。\n\n"
            + "\n".join(lines) +
            "\n\n返回 JSON 数组，每个元素: {\"paragraph_index\": 序号, \"speaker\": \"说话人\"}"
        )

        resp = await self.chat([
            {"role": "system", "content": "你是一个小说对话分析助手。只返回 JSON，不要额外说明。"},
            {"role": "user", "content": prompt},
        ])

        try:
            data = json.loads(resp)
            if not isinstance(data, list):
                data = [data]
            speaker_map = {}
            for item in data:
                idx = item.get("paragraph_index")
                sp = item.get("speaker", "")
                if idx is not None and sp:
                    speaker_map[idx] = sp

            for seg in segments:
                sp = speaker_map.get(seg.paragraph_index)
                if sp and sp != "旁白":
                    seg.speaker = sp
                    seg.speaker_type = "character"
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return segments

    async def chat(self, messages: list[dict]) -> str:
        try:
            resp = await self._client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            self._last_token_usage = TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
            return data["choices"][0]["message"]["content"]
        except httpx.ConnectError as e:
            raise ConnectionError(f"无法连接到 {self.api_base}：{e}")
        except httpx.TimeoutException:
            raise TimeoutError(f"连接 LLM 超时（{self.api_base}），请检查网络或 API 地址")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"LLM 返回错误 {e.response.status_code}：{e.response.text[:200]}")
