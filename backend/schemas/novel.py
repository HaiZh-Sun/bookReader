from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class NovelCreate(BaseModel):
    title: str
    author: str = ""


class NovelOut(BaseModel):
    id: int
    title: str
    author: str
    file_size: int
    status: str
    total_chapters: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterOut(BaseModel):
    id: int
    novel_id: int
    title: str
    order: int
    word_count: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NovelDetail(NovelOut):
    chapters: List[ChapterOut] = []
