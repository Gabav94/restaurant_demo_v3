# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

# from __future__ import annotations
# import os
# import json
# import streamlit as st
# from typing import List, Dict, Any, Optional
# # from openai import OpenAI
# from langchain_openai import ChatOpenAI
# from dotenv import dotenv_values


# def get_openai_client() -> Optional[ChatOpenAI]:
#     config = dotenv_values()
#     # key = os.environ.get("OPENAI_API_KEY")
#     # key = config["OPENAI_API_KEY"]
#     key = st.secrets["OPENAI_API_KEY"]
#     if not key:
#         return None
#     return ChatOpenAI(model="gpt-4o-mini", temperature=0.25, api_key=key)


# def chat_completion(system: str, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
#     client = get_openai_client()
#     if client is None:
#         # Fallback: echo assistant for offline demo
#         last_user = ""
#         for m in reversed(messages):
#             if m.get("role") == "user":
#                 last_user = m.get("content", "")
#                 break
#         return f"[DEMO MODE] You said: {last_user[:200]}"
#     model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
#     resp = client.chat.completions.create(
#         model=model,
#         messages=[{"role": "system", "content": system}, *messages],
#         temperature=0.3,
#     )
#     return resp.choices[0].message.content


# def transcribe_audio(file_bytes: bytes, filename: str = "audio.wav") -> Optional[str]:
#     client = get_openai_client()
#     if client is None:
#         return None
#     audio_model = os.environ.get("OPENAI_AUDIO_MODEL", "whisper-1")
#     try:
#         # Using new OpenAI SDK - audio.transcriptions for "whisper-1"
#         import tempfile
#         with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
#             tmp.write(file_bytes)
#             tmp.flush()
#             with open(tmp.name, "rb") as f:
#                 tr = client.audio.transcriptions.create(
#                     model=audio_model, file=f)
#         return tr.text
#     except Exception as e:
#         return None

# backend/llm_providers.py
"""
Espacio para integrar proveedores LLM reales (OpenAI, etc.).
En esta demo v3 el grafo usa una heurística simple.
Puedes reemplazarlo por llamadas reales y enriquecer el prompt.
"""




from __future__ import annotations
def transcribe_audio(content: bytes, language: str = "es") -> str:
    # Mock: en producción integrar Whisper/OpenAI Speech o Vosk/Coqui
    return "[transcripción demo]"
