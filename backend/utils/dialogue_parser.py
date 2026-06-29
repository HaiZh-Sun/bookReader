"""
Rule-based dialogue parser for Chinese novels.

Uses regex patterns to identify narrator vs character dialogue with high confidence.
Only paragraphs that can't be clearly classified are flagged for AI disambiguation.

Confidence levels:
  >= 0.9 → rule-based result is final
  < 0.9  → needs AI disambiguation
"""

import re
from typing import Optional

# Characters that typically appear as speaker attributions
_SPEAKER_WORDS = r'(?:说|道|问|答|喊|叫|骂|笑|叹|应|说道|笑道|叹道|问道|答道|喊道|叫道|喝道|骂道|哭道|嗔道|催道|劝道|夸道|吼道|哭着说|笑着说|笑着道|低声说|低声道|小声说|小声道|大声说|大声道|轻声说|轻声道|正色道|正色说|自言自语|回答|开口|招呼|解释|吩咐|提醒|告诉|批评|称赞)'

# Chinese quotation marks (including ASCII " and Chinese curly quotes)
_QUOTES = r'[\"\u201c\u201d\u300c\u300d\u300e\u300f]'

# Pattern 1: "话"XX说 — quote first, then speaker attribution
# e.g. "早上好！"小明说。 "你好啊，"他笑道。
_PAT_QUOTE_FIRST = re.compile(
    rf'^{_QUOTES}(.+?){_QUOTES}\s*，?\s*([\u4e00-\u9fff]{{1,4}}?){_SPEAKER_WORDS}'
)

# Pattern 2: XX说："话" — speaker first, then quote with colon
# e.g. 小明说："你好。" 小红问道："你去哪？"
_PAT_SPEAKER_FIRST_COLON = re.compile(
    rf'^([\u4e00-\u9fff]{{1,4}}?){_SPEAKER_WORDS}[：:]\s*{_QUOTES}(.+?){_QUOTES}'
)

# Pattern 3: XX说，"话" — speaker first, then quote with comma
_PAT_SPEAKER_FIRST_COMMA = re.compile(
    rf'^([\u4e00-\u9fff]{{1,4}}?){_SPEAKER_WORDS}[，,]\s*{_QUOTES}(.+?){_QUOTES}'
)

# Pattern 4: "话" — quote only, no speaker attribution (ambiguous)
_PAT_QUOTE_ONLY = re.compile(
    rf'^{_QUOTES}(.+?){_QUOTES}'
)

# Pattern 5: Mixed — speaker is at the end without attribution word
# e.g. "我来了。"张三。 "吃饭了。"母亲。
# This is rare but handle it
_PAT_QUOTE_THEN_NAME = re.compile(
    rf'^{_QUOTES}(.+?){_QUOTES}[，。！？，!?\s]*([\u4e00-\u9fff]{{1,4}}?)(?:[，。！？\s]|$)'
)


class ParsedSegment:
    __slots__ = ('text', 'raw_text', 'speaker', 'speaker_type', 'confidence', 'paragraph_index', 'age_group', 'gender')

    def __init__(self, text: str, raw_text: str, speaker: str, speaker_type: str,
                 confidence: float, paragraph_index: int,
                 age_group: str = "成年", gender: str = "男"):
        self.text = text
        self.raw_text = raw_text
        self.speaker = speaker
        self.speaker_type = speaker_type
        self.confidence = confidence
        self.paragraph_index = paragraph_index
        self.age_group = age_group
        self.gender = gender

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "speaker": self.speaker,
            "speaker_type": self.speaker_type,
            "paragraph_index": self.paragraph_index,
        }


def _has_quotes(text: str) -> bool:
    """Check if text contains any Chinese quotation marks."""
    return bool(re.search(_QUOTES, text))


def parse_paragraph(para: str, index: int) -> ParsedSegment:
    """
    Parse a single paragraph using rules.
    Returns ParsedSegment with confidence score.
    """
    para = para.strip()
    if not para:
        return ParsedSegment("", "", "旁白", "narrator", 1.0, index)

    has_q = _has_quotes(para)

    # No quotes → almost certainly narration
    if not has_q:
        return ParsedSegment(para, para, "旁白", "narrator", 0.95, index)

    # Try Pattern 1: "quote"XX说
    m = _PAT_QUOTE_FIRST.search(para)
    if m:
        dialogue = m.group(1).strip()
        speaker = m.group(2).strip()
        return ParsedSegment(dialogue, para, speaker, "character", 0.95, index)

    # Try Pattern 2: XX说："quote"
    m = _PAT_SPEAKER_FIRST_COLON.search(para)
    if m:
        speaker = m.group(1).strip()
        dialogue = m.group(2).strip()
        return ParsedSegment(dialogue, para, speaker, "character", 0.95, index)

    # Try Pattern 3: XX说，"quote"
    m = _PAT_SPEAKER_FIRST_COMMA.search(para)
    if m:
        speaker = m.group(1).strip()
        dialogue = m.group(2).strip()
        return ParsedSegment(dialogue, para, speaker, "character", 0.90, index)

    # Try Pattern 5: "quote"XX (name after quote, no verb)
    m = _PAT_QUOTE_THEN_NAME.search(para)
    if m:
        dialogue = m.group(1).strip()
        speaker = m.group(2).strip()
        return ParsedSegment(dialogue, para, speaker, "character", 0.85, index)

    # Pattern 4: Just quotes, no speaker → ambiguous
    m = _PAT_QUOTE_ONLY.search(para)
    if m:
        dialogue = m.group(1).strip()
        return ParsedSegment(dialogue, para, "未知角色", "character", 0.50, index)

    # Fallback: has quotes but doesn't match any pattern → ambiguous narration
    return ParsedSegment(para, para, "旁白", "narrator", 0.40, index)


def split_certain_ambiguous(
    paragraphs: list[str],
    confidence_threshold: float = 0.9,
) -> tuple[list[ParsedSegment], list[int]]:
    """
    Split paragraphs into certain (rule-based) and ambiguous (need AI).
    Returns (certain_segments, ambiguous_indices).
    """
    certain: list[ParsedSegment] = []
    ambiguous_indices: list[int] = []

    for i, para in enumerate(paragraphs):
        seg = parse_paragraph(para, i)
        if seg.confidence >= confidence_threshold:
            certain.append(seg)
        else:
            ambiguous_indices.append(i)

    return certain, ambiguous_indices
