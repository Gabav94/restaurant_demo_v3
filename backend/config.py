# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:18:05 2025

@author: geam9
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any

CONFIG_DIR = os.path.join("data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
os.makedirs(CONFIG_DIR, exist_ok=True)

_DEFAULT_CFG: Dict[str, Any] = {
    "language": "es",
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
        _save(_DEFAULT_CFG.copy())
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _DEFAULT_CFG.copy()


def _with_defaults(cfg: dict) -> dict:
    fixed = _DEFAULT_CFG.copy()
    fixed.update(cfg or {})
    return fixed


def ensure_default_config() -> dict:
    cfg = _read_raw()
    fixed = _with_defaults(cfg)
    if fixed != cfg:
        _save(fixed)
    return fixed


def get_config() -> dict:
    return ensure_default_config()


def update_config(new_values: dict) -> None:
    cfg = ensure_default_config()
    cfg.update(new_values or {})
    cfg = _with_defaults(cfg)
    _save(cfg)


def reset_config() -> None:
    _save(_DEFAULT_CFG.copy())


def get_language() -> str:
    return get_config().get("language", "es")


def get_tone() -> str:
    return get_config().get("tone", _DEFAULT_CFG["tone"])
