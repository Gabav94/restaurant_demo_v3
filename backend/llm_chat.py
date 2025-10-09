# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:20:15 2025

@author: geam9
"""

from __future__ import annotations
import re
import os
import streamlit as st
from dotenv import dotenv_values
from openai import OpenAI
from backend.config import get_config

_cfg = dotenv_values(".env")
_client = OpenAI(api_key=_cfg.get("OPENAI_API_KEY"))
# _client = OpenAI(api_key=st.secrets("OPENAI_API_KEY"))

# ---------- Prompt Base ----------


def build_system_prompt(menu_text: str) -> str:
    cfg = get_config()
    lang = cfg.get("language", "es")
    tone = cfg.get("tone", "Amable y profesional; breve y guiado.")
    name = cfg.get("assistant_name", "Asistente")

    # prompt en el idioma seleccionado
    if lang == "es":
        return (
            f"Eres {name}, un asistente de pedidos para un restaurante.\n"
            f"Estilo:{tone}\n"
            "Responde SIEMPRE en español.\n"
            "Objetivo: ayudar al cliente a armar su pedido basado en el menú y confirmar datos.\n"
            "Puedes sugerir acompañantes y bebidas. Si piden algo fuera del menú, pide elegir otra opción.\n"
            "Personalizaciones aceptadas: sin cebolla, salsa aparte, extra papas, etc.\n"
            "Si no estás seguro o preguntan por ingredientes fuera del menú, responde: "
            "«⏳ Espera un momento por favor, estoy consultando con cocina…» y no inventes.\n\n"
            "Cuando el pedido parezca listo, pregunta y valida EN ESTE ORDEN:\n"
            "1) ¿Será para recoger (retiro) o entrega a domicilio?\n"
            "2) ¿Cuál es tu número de teléfono?\n"
            "3) Si es entrega: ¿cuál es la dirección?\n"
            "4) ¿Qué método de pago vas a usar?\n"
            "5) Si es retiro: ¿en cuántos minutos pasas?\n\n"
            "Cuando tengas todo, di: «Pedido listo para confirmación. Por favor, presiona el botón Confirmar Pedido.» "
            "No confirmes tú el pedido; espera al botón.\n\n"
            "Menú:\n" + menu_text
        )
    else:
        return (
            f"You are {name}, a restaurant ordering assistant.\n"
            f"Style:{tone}\n"
            "Always reply in English.\n"
            "Goal: help the customer build an order from the menu and confirm details.\n"
            "You may suggest sides and drinks. If they ask for off-menu items, ask them to pick a listed option.\n"
            "Allowed customizations: no onions, sauce on side, extra fries, etc.\n"
            "If unsure or ingredients are not listed, say: "
            "“⏳ Please wait a moment, I’m checking with the kitchen…” and do not invent.\n\n"
            "When the order seems ready, ask and validate IN THIS ORDER:\n"
            "1) Pickup or delivery?\n"
            "2) Phone number?\n"
            "3) If delivery: address?\n"
            "4) Payment method?\n"
            "5) If pickup: in how many minutes?\n\n"
            "When you have everything, say: “Order ready for confirmation. Please press the Confirm Order button.” "
            "Do not confirm yourself; wait for the button.\n\n"
            "Menu:\n" + menu_text
        )


def llm_reply(user_msg: str, menu_text: str) -> str:
    prompt = build_system_prompt(menu_text)
    r = _client.chat.completions.create(
        model=get_config().get("model", "gpt-4o-mini"),
        temperature=float(get_config().get("temperature", 0.4)),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_msg},
        ]
    )
    return (r.choices[0].message.content or "").strip()

# Extracción muy simple (regex demo). En producción, usaría un parser estructurado.


def extract_fields_from_text(txt: str) -> dict:
    d = {}
    # nombre: "me llamo X", "soy X"
    m = re.search(
        r"(me llamo|soy)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]{2,})", txt, re.IGNORECASE)
    if m:
        d["name"] = m.group(2).strip()
    # teléfono: secuencia 7-15 dígitos
    m = re.search(r"(\+?\d[\d\s\-]{6,})", txt)
    if m:
        d["phone"] = re.sub(r"\D", "", m.group(1))[:15]
    # delivery/pickup
    if re.search(r"\b(entrega|domicilio|delivery)\b", txt, re.IGNORECASE):
        d["delivery_type"] = "delivery"
    if re.search(r"\b(recojo|retiro|pickup)\b", txt, re.IGNORECASE):
        d["delivery_type"] = "pickup"
    # dirección
    m = re.search(r"(dirección|address)\s*[:\-]\s*(.+)$", txt, re.IGNORECASE)
    if m:
        d["address"] = m.group(2).strip()
    # pago
    if re.search(r"\b(efectivo|cash)\b", txt, re.IGNORECASE):
        d["payment_method"] = "cash"
    if re.search(r"\b(tarjeta|card|credito|crédito|debit|débito)\b", txt, re.IGNORECASE):
        d["payment_method"] = "card"
    # pickup ETA
    m = re.search(
        r"(en|dentro de)\s*(\d{1,2})\s*(min|minutos)", txt, re.IGNORECASE)
    if m:
        d["pickup_eta_min"] = int(m.group(2))
    return d
