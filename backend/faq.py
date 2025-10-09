# -*- coding: utf-8 -*-
"""
Created on Sun Oct  5 21:29:36 2025

@author: geam9
"""

from __future__ import annotations
import os
import datetime as dt
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join("data", "app.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()


class FAQ(Base):
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True)
    pattern = Column(String, index=True)
    answer = Column(Text)
    language = Column(String, default="es")
    created_at = Column(DateTime, default=dt.datetime.utcnow)


Base.metadata.create_all(engine)


def _s(): return SessionLocal()

# ===== CRUD =====


def add_faq(pattern: str, answer: str, language: str = "es") -> Dict:
    s = _s()
    try:
        faq = FAQ(pattern=pattern[:140], answer=answer, language=language)
        s.add(faq)
        s.commit()
        s.refresh(faq)
        return {"id": faq.id, "pattern": faq.pattern, "answer": faq.answer, "language": faq.language}
    finally:
        s.close()


def fetch_faq(language: str = "es") -> List[Dict]:
    s = _s()
    try:
        rows = s.query(FAQ).filter(FAQ.language == language).order_by(
            FAQ.created_at.desc()).all()
        return [{"pattern": r.pattern, "answer": r.answer, "created_at": r.created_at.isoformat()} for r in rows]
    finally:
        s.close()


def match_faq(question: str, language: str = "es") -> str | None:
    """
    Busca una pregunta similar en la FAQ. 
    Se puede mejorar luego con embeddings o similitud difusa.
    """
    s = _s()
    try:
        rows = s.query(FAQ).filter(FAQ.language == language).all()
        q = question.lower()
        for r in rows:
            if r.pattern.lower() in q or q in r.pattern.lower():
                return r.answer
        return None
    finally:
        s.close()


def clear_faq():
    s = _s()
    try:
        s.query(FAQ).delete()
        s.commit()
    finally:
        s.close()
