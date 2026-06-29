import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class NovelStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    READY = "ready"
    ERROR = "error"


class Novel(Base):
    __tablename__ = "novels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), default="")
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(SAEnum(NovelStatus), default=NovelStatus.UPLOADED)
    total_chapters = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    title = Column(String(255), default="")
    order = Column(Integer, default=0)
    content = Column(Text, default="")
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    novel = relationship("Novel", back_populates="chapters")
    dialogue_lines = relationship("DialogueLine", back_populates="chapter", cascade="all, delete-orphan")
