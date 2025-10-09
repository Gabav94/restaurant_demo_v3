# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:18:05 2025

@author: geam9
"""

# from __future__ import annotations
# import os
# import json
# from sqlalchemy import create_engine, Column, String
# from sqlalchemy.orm import declarative_base, sessionmaker

# DB_DIR = os.path.join(".", "data")
# os.makedirs(DB_DIR, exist_ok=True)
# DB_PATH = os.path.join(DB_DIR, "config.db")
# engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
# SessionLocal = sessionmaker(
#     bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
# Base = declarative_base()


# class KV(Base):
#     __tablename__ = "kv"
#     key = Column(String, primary_key=True)
#     val = Column(String, default="")


# Base.metadata.create_all(engine)

# DEFAULTS = {
#     "assistant_name": "Raiva",
#     "tone": "casual",
#     "language": "es",
#     "currency": "USD",
#     "model": "gpt-4o-mini",
#     "temperature": 0.4,
#     "system_note": "Friendly and casual, but respectful and supportive",
# }


# def _session():
#     return SessionLocal()


# def ensure_default_config():
#     s = _session()
#     try:
#         for k, v in DEFAULTS.items():
#             row = s.get(KV, k)
#             if not row:
#                 s.add(KV(key=k, val=json.dumps(v)))
#         s.commit()
#     finally:
#         s.close()


# def get_config() -> dict:
#     s = _session()
#     try:
#         out = {}
#         for k in DEFAULTS.keys():
#             row = s.get(KV, k)
#             out[k] = json.loads(row.val) if row and row.val else DEFAULTS[k]
#         return out
#     finally:
#         s.close()


# def update_config(d: dict):
#     s = _session()
#     try:
#         for k, v in d.items():
#             row = s.get(KV, k)
#             if not row:
#                 row = KV(key=k, val=json.dumps(v))
#                 s.add(row)
#             else:
#                 row.val = json.dumps(v)
#         s.commit()
#     finally:
#         s.close()

from __future__ import annotations
import os
import json
from typing import Dict, Any

CONFIG_DIR = os.path.join("data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

_DEFAULT_CFG: Dict[str, Any] = {
    "language": "es",                         # "es" | "en"
    "model": "gpt-4o-mini",
    "temperature": 0.4,
    "assistant_name": "Asistente",
    "tone": "Amable y profesional; breve, guiado.",
    "currency": "USD",
}


def _save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _read_raw() -> dict:
    if not os.path.exists(CONFIG_PATH):
        # Si no existe, creamos con los defaults
        _save(_DEFAULT_CFG.copy())
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Si hay un problema de lectura/JSON malformado, regresamos defaults
        return _DEFAULT_CFG.copy()


def _with_defaults(cfg: dict) -> dict:
    """Backfill: asegura que todas las claves default existan en el cfg actual."""
    fixed = _DEFAULT_CFG.copy()
    fixed.update(cfg or {})
    return fixed


def ensure_default_config() -> dict:
    """
    Garantiza que exista data/config.json y que contenga todas las claves requeridas.
    Devuelve la configuración final aplicada (con backfill de defaults si faltaban claves).
    """
    cfg = _read_raw()
    fixed = _with_defaults(cfg)
    if fixed != cfg:
        _save(fixed)  # persistir backfill
    return fixed


def get_config() -> dict:
    """
    Lee la configuración global (creando el archivo si no existe)
    y garantizando que todas las claves existan.
    """
    return ensure_default_config()


def update_config(new_values: dict) -> None:
    """
    Actualiza claves de configuración persistente.
    Aplica backfill de defaults por si en el futuro agregamos más claves.
    """
    cfg = ensure_default_config()
    cfg.update(new_values or {})
    cfg = _with_defaults(cfg)
    _save(cfg)


def reset_config() -> None:
    """Restaura configuración predeterminada."""
    _save(_DEFAULT_CFG.copy())


def get_language() -> str:
    """Devuelve el idioma actual ('es' o 'en')."""
    return get_config().get("language", "es")


def get_tone() -> str:
    """Devuelve el tono configurado."""
    return get_config().get("tone", _DEFAULT_CFG["tone"])
