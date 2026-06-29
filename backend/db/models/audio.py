import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from db.database import Base
import enum


class AudioStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"


class AudioRecord(Base):
    __tablename__ = "audio_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dialogue_line_id = Column(Integer, ForeignKey("dialogue_lines.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    file_path = Column(String(512), default="")
    status = Column(SAEnum(AudioStatus), default=AudioStatus.PENDING)
    duration_ms = Column(Integer, default=0)
    tts_provider = Column(String(64), default="")
    voice_tag = Column(String(255), default="")
    error_message = Column(String(512), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dialogue_line = relationship("DialogueLine", back_populates="audio_records")
    chapter = relationship("Chapter")
