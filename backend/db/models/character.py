import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, Boolean,
)
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class SpeakerType(str, enum.Enum):
    NARRATOR = "narrator"
    CHARACTER = "character"
    UNKNOWN = "unknown"


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    name = Column(String(255), nullable=False)
    speaker_type = Column(SAEnum(SpeakerType), default=SpeakerType.CHARACTER)
    voice_tag = Column(String(255), default="")
    age_group = Column(String(32), default="成年")
    gender = Column(String(8), default="男")
    description = Column(Text, default="")
    is_merged = Column(Boolean, default=False)
    merged_into_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    novel = relationship("Novel", back_populates="characters")
    dialogue_lines = relationship("DialogueLine", back_populates="character")
    merged_into = relationship("Character", remote_side=[id], backref="merged_from")


class DialogueLine(Base):
    __tablename__ = "dialogue_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    text = Column(Text, nullable=False)
    speaker_type = Column(SAEnum(SpeakerType), default=SpeakerType.UNKNOWN)
    order = Column(Integer, default=0)
    paragraph_index = Column(Integer, default=0)
    is_audiobook_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    chapter = relationship("Chapter", back_populates="dialogue_lines")
    character = relationship("Character", back_populates="dialogue_lines")
    audio_records = relationship("AudioRecord", back_populates="dialogue_line", cascade="all, delete-orphan")
