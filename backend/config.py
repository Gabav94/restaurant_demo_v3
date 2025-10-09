# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:18:05 2025

@author: geam9
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any
from threading import RLock

CONFIG_DIR = "data"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

_DEFAULTS: Dict[str, Any] = {
    "language": "es",
    "assistant_name": "Asistente",
    "tone": "Amable y profesional; breve y guiado.",
    "model": "gpt-4o-mini",
    "temperature": 0.4,
    "currency": "USD",
}

_lock = RLock()


def _ensure_dirs(): os.makedirs(CONFIG_DIR, exist_ok=True)


def _ensure_file():
    if not os.path.isfile(CONFIG_PATH):
        _ensure_dirs()
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(_DEFAULTS, f, indent=2, ensure_ascii=False)


def _read() -> Dict[str, Any]:
    _ensure_file()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f) or {}
    merged = {**_DEFAULTS, **data}
    try:
        merged["temperature"] = float(merged.get(
            "temperature", _DEFAULTS["temperature"]))
    except Exception:
        merged["temperature"] = _DEFAULTS["temperature"]
    if merged.get("language") not in ("es", "en"):
        merged["language"] = _DEFAULTS["language"]
    return merged


def _write(cfg: Dict[str, Any]) -> None:
    _ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_config() -> Dict[str, Any]:
    with _lock:
        return _read()


def set_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(updates, dict):
        raise ValueError("updates debe ser dict")
    with _lock:
        current = _read()
        allowed = set(_DEFAULTS.keys())
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if "language" in filtered and filtered["language"] not in ("es", "en"):
            filtered["language"] = current["language"]
        if "temperature" in filtered:
            try:
                filtered["temperature"] = float(filtered["temperature"])
            except Exception:
                filtered["temperature"] = current["temperature"]
        current.update(filtered)
        _write(current)
        return current

# Compat opcional si tenías imports legacy


def ensure_default_config():
    return get_config()
