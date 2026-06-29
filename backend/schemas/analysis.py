from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CharacterOut(BaseModel):
    id: int
    name: str
    speaker_type: str
    voice_tag: str
    age_group: str = "成年"
    gender: str = "男"
    description: str
    is_merged: bool
    merged_into_id: Optional[int] = None

    model_config = {"from_attributes": True}


class CharacterMerge(BaseModel):
    source_ids: List[int]
    target_id: int


class CharacterRename(BaseModel):
    name: str


class CharacterVoiceUpdate(BaseModel):
    voice_tag: str


class CharacterAttrUpdate(BaseModel):
    age_group: Optional[str] = None
    gender: Optional[str] = None


class DialogueLineOut(BaseModel):
    id: int
    chapter_id: int
    character_id: Optional[int] = None
    text: str
    speaker_type: str
    order: int
    paragraph_index: int

    model_config = {"from_attributes": True}


class DialogueLineUpdateCharacter(BaseModel):
    character_id: Optional[int] = None


class DialogueLineUpdateText(BaseModel):
    text: str


class AnalysisResult(BaseModel):
    chapter_id: int
    characters: List[CharacterOut]
    dialogue_lines: List[DialogueLineOut]
