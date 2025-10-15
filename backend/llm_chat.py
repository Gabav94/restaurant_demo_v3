# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:20:15 2025

@author: geam9
"""

# from __future__ import annotations
# from typing import List, Dict
# import json
# import re
# import tempfile
# import os
# import wave
# import streamlit as st
# from dotenv import dotenv_values
# from langchain_openai import ChatOpenAI
# from openai import OpenAI
# from backend.config import get_config
# from backend.faq import match_faq
# from backend.db import create_pending_question


# def _get_llm(cfg: dict) -> ChatOpenAI:
#     # key = dotenv_values().get("OPENAI_API_KEY")
#     key = st.secrets["OPENAI_API_KEY"]
#     if not key:
#         raise RuntimeError("Falta OPENAI_API_KEY en .env")
#     model = cfg.get("model", "gpt-4o-mini")
#     temp = float(cfg.get("temperature", 0.4))
#     return ChatOpenAI(api_key=key, model=model, temperature=temp)


# def _format_price(p) -> str:
#     try:
#         return f"{float(p):.2f}"
#     except Exception:
#         return str(p)


# def _format_menu(menu: List[Dict]) -> str:
#     lines = []
#     for it in (menu or [])[:120]:
#         name = it.get("name", "").strip()
#         if not name:
#             continue
#         desc = (it.get("description") or "").strip()
#         price = _format_price(it.get("price", 0))
#         cur = it.get("currency", "USD")
#         notes = (it.get("special_notes") or "").strip()
#         notes_txt = f" — [{notes}]" if notes else ""
#         line = f"- {name} ({cur} {price}){notes_txt}"
#         if desc:
#             line += f"\n  {desc}"
#         lines.append(line)
#     return "\n".join(lines)


# def _system_prompt(cfg: dict, menu: List[Dict], lang: str) -> str:
#     formatted_menu = _format_menu(menu)
#     tone = cfg.get("tone") or ("Amable y profesional; breve, guiado." if lang ==
#                                "es" else "Friendly and professional; concise, guided.")
#     assistant_name = cfg.get(
#         "assistant_name", "Asistente" if lang == "es" else "Assistant")
#     if lang == "es":
#         return (
#             f"Eres {
#                 assistant_name}, un asistente de pedidos para un restaurante. Responde SIEMPRE en español.\n"
#             f"Tu tono: {tone}\n\n"
#             "Objetivo: ayudar al cliente a armar su pedido basado en el menú y confirmar datos. "
#             "Sugiere acompañantes y bebidas. Si piden algo fuera del menú, pide elegir otra opción.\n\n"
#             "🍽 Menú disponible:\n" + formatted_menu + "\n\n"
#             "📌 Comportamiento:\n"
#             "- Cálido, claro, paso a paso. No inventes productos/ingredientes.\n"
#             "- Personalizaciones: acepta sin cebolla, salsa aparte, extra papas, etc. Ajusta precio si aplica.\n"
#             '- Si no estás seguro: "⏳ Espera un momento por favor, estoy consultando con cocina…".\n'
#             "- Usa la FAQ interna si hay respuesta registrada (no pidas confirmación humana si ya existe).\n"
#             "- Lleva total aproximado mientras ordena.\n\n"
#             "🧾 Cuando parezca listo, recopila (detecta si ya se dieron):\n"
#             "  1) pickup o delivery\n  2) teléfono\n  3) dirección si delivery\n  4) método de pago\n"
#             "Reconoce nombre, teléfono, tipo de entrega, dirección y pago en texto o audio transcrito. "
#             "No invites a confirmar hasta que estén completos.\n\n"
#             "✅ Cuando tengas todo: “Pedido listo para confirmación. Por favor, presiona el botón Confirmar Pedido.”\n"
#             "🛑 Si dice “stop”, termina con amabilidad.\n"
#             "🎯 Estilo: amable, profesional, breve y guiado."
#         )
#     else:
#         return (
#             f"You are {
#                 assistant_name}, a restaurant ordering assistant. ALWAYS answer in English.\n"
#             f"Tone: {tone}\n\n"
#             "Goal: help the customer build an order based on the menu and confirm details. "
#             "Suggest sides and drinks. If off-menu, ask to pick an available option.\n\n"
#             "🍽 Menu:\n" + formatted_menu + "\n\n"
#             "📌 Behavior: warm, clear, step by step; no invention. "
#             "Customizations accepted when on menu. If unsure: “⏳ Please wait… checking with the kitchen…”. "
#             "Use internal FAQ if available. Keep a running total.\n\n"
#             "🧾 When ready, gather (detect if already provided): pickup/delivery, phone, address (if delivery), payment.\n"
#             "✅ Once complete: “Order ready for confirmation. Please press Confirm Order.”\n"
#             "🛑 If user says “stop”, end politely.\n"
#             "🎯 Style: friendly, professional, concise and guided."
#         )


# def client_assistant_reply(history: List[Dict], menu: List[Dict], cfg: dict | None, conversation_id: str) -> str:
#     cfg = cfg or get_config()
#     lang = cfg.get("language", "es")
#     last_user = next((m["content"] for m in reversed(
#         history) if m.get("role") == "user"), "")
#     if last_user:
#         faq_ans = match_faq(last_user, language=lang)
#         if faq_ans:
#             return faq_ans
#     llm = _get_llm(cfg)
#     sys = _system_prompt(cfg, menu, lang)
#     msgs = [{"role": "system", "content": sys}] + history[-12:]
#     res = llm.invoke(msgs)
#     reply = (res.content or "").strip()
#     low = reply.lower()
#     if ("consultando con cocina" in low) or ("checking with the kitchen" in low):
#         try:
#             create_pending_question(
#                 conversation_id=conversation_id, question=last_user, language=lang, ttl_seconds=60)
#         except Exception:
#             pass
#     return reply


# _NAME_PAT_ES = re.compile(
#     r"(?i)(?:mi\s+)?nombre\s*(?:es|:)?\s*([A-Za-zÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑ\s]{1,})")
# _NAME_PAT_EN = re.compile(
#     r"(?i)(?:my\s+)?name\s*(?:is|:)?\s*([A-Za-z][A-Za-z\s]{1,})")
# _PHONE_PAT = re.compile(
#     r"(?i)(?:tel[eé]fono|phone|cel|cell|m[oó]vil|mobile)\s*(?:es|is|:)?\s*(\+?\d[\d\-\s]{6,})")
# _ADDRESS_PAT_ES = re.compile(r"(?i)direcci[oó]n\s*(?:es|:)?\s*(.+)")
# _ADDRESS_PAT_EN = re.compile(r"(?i)address\s*(?:is|:)?\s*(.+)")
# _MIN_PAT = re.compile(r"(?i)(\d{1,3})\s*(?:min|minute|minutes|minutos)")
# _DELIVERY_ES = re.compile(r"(?i)(domicilio|delivery|enviar|entrega)")
# _PICKUP_ES = re.compile(r"(?i)(retir|recoger|pickup)")
# _DELIVERY_EN = re.compile(r"(?i)(delivery|deliver)")
# _PICKUP_EN = re.compile(r"(?i)(pickup|pick up)")


# def extract_client_info(history: List[Dict], lang: str) -> Dict:
#     text = " \n".join([m.get("content", "")
#                       for m in history if m.get("role") == "user"])
#     out = {"name": "", "phone": "", "delivery_type": "",
#            "address": "", "pickup_eta_min": "", "payment_method": ""}
#     m = (_NAME_PAT_ES.search(text) if lang ==
#          "es" else _NAME_PAT_EN.search(text))
#     if m:
#         out["name"] = m.group(1).strip()
#     m = _PHONE_PAT.search(text)
#     if m:
#         out["phone"] = re.sub(r"\s+", "", m.group(1)).replace("-", "")
#     if ((_DELIVERY_ES.search(text) if lang == "es" else _DELIVERY_EN.search(text))):
#         out["delivery_type"] = "delivery"
#     if ((_PICKUP_ES.search(text) if lang == "es" else _PICKUP_EN.search(text))):
#         out["delivery_type"] = out["delivery_type"] or "pickup"
#     m = (_ADDRESS_PAT_ES.search(text) if lang ==
#          "es" else _ADDRESS_PAT_EN.search(text))
#     if m:
#         out["address"] = m.group(1).strip()
#     m = _MIN_PAT.search(text)
#     if m:
#         out["pickup_eta_min"] = m.group(1).strip()
#     if re.search(r"(?i)(efectivo|cash)", text):
#         out["payment_method"] = "cash"
#     elif re.search(r"(?i)(tarjeta|card)", text):
#         out["payment_method"] = "card"
#     elif re.search(r"(?i)(online|transfer|transferencia|bank)", text):
#         out["payment_method"] = "online"
#     return out


# def ensure_all_required_present(info: Dict, lang: str) -> List[str]:
#     req = ["name", "phone", "delivery_type", "payment_method"]
#     if info.get("delivery_type") == "delivery":
#         req.append("address")
#     else:
#         req.append("pickup_eta_min")
#     missing = [k for k in req if not str(info.get(k, "")).strip()]
#     if "pickup_eta_min" in missing and info.get("delivery_type") == "pickup":
#         info["pickup_eta_min"] = 30
#         missing.remove("pickup_eta_min")
#     return missing


# def parse_items_from_chat(history: List[Dict], menu: List[Dict], cfg: dict) -> List[Dict]:
#     llm = _get_llm(cfg)
#     lang = cfg.get("language", "es")
#     names = [m["name"] for m in (menu or [])]
#     price_map = {m["name"]: float(m.get("price", 0.0)) for m in (menu or [])}
#     sys = ("Devuelve exclusivamente un JSON UTF-8: "
#            '[{"name":"...","qty":N,"unit_price":P}]' if lang == "es"
#            else "Return ONLY a UTF-8 JSON list: "
#            '[{"name":"...","qty":N,"unit_price":P}]')
#     user_text = "\n".join([m["content"]
#                           for m in history if m.get("role") == "user"])[-2000:]
#     prompt = (f"Menú: {names}\nPrecios: {price_map}\nExtrae items/cantidades/precios."
#               if lang == "es" else
#               f"Menu items: {names}\nPrices: {price_map}\nExtract items/quantities/prices.")
#     try:
#         out = llm.invoke([{"role": "system", "content": sys}, {
#                          "role": "user", "content": prompt+"\n\n"+user_text}]).content
#         data = json.loads(out)
#         clean = []
#         for d in (data if isinstance(data, list) else []):
#             nm = d.get("name")
#             if nm in price_map:
#                 clean.append({"name": nm, "qty": int(d.get("qty", 1)), "unit_price": float(
#                     d.get("unit_price", price_map[nm]))})
#         if clean:
#             return clean
#     except Exception:
#         pass
#     text_low = user_text.lower()
#     items = []
#     for nm, pr in price_map.items():
#         if nm.lower() in text_low:
#             items.append({"name": nm, "qty": 1, "unit_price": pr})
#     return items


# def _bytes_to_wav_temp(raw_pcm: bytes, channels: int = 1, sample_width: int = 2, frame_rate: int = 16000) -> str:
#     try:
#         fd, path = tempfile.mkstemp(suffix=".wav")
#         os.close(fd)
#         with wave.open(path, "wb") as wf:
#             wf.setnchannels(channels)
#             wf.setsampwidth(sample_width)
#             wf.setframerate(frame_rate)
#             wf.writeframes(raw_pcm)
#         return path
#     except Exception:
#         return ""


# def _transcribe_file(path: str) -> str:
#     key = dotenv_values().get("OPENAI_API_KEY")
#     if not key or not path or not os.path.isfile(path):
#         return ""
#     client = OpenAI(api_key=key)
#     try:
#         with open(path, "rb") as f:
#             tr = client.audio.transcriptions.create(model="whisper-1", file=f)
#         return tr.text or ""
#     except Exception:
#         return ""


# def client_voice_to_text(raw_audio_bytes: bytes, cfg: dict) -> str:
#     path = _bytes_to_wav_temp(raw_audio_bytes)
#     if not path:
#         return ""
#     try:
#         return _transcribe_file(path)
#     finally:
#         try:
#             os.remove(path)
#         except Exception:
#             pass


# def admin_voice_command(raw_audio_bytes: bytes, cfg: dict, lang: str) -> str:
#     text = client_voice_to_text(raw_audio_bytes, cfg) or ""
#     if not text:
#         return "No se pudo transcribir audio." if lang == "es" else "Could not transcribe audio."
#     tl = text.lower()
#     if lang == "es":
#         m = re.search(r"aprobar pendiente (\w[\w\-]+)", tl)
#         if m:
#             return f"Acción sugerida: aprobar pendiente {m.group(1)}"
#         m = re.search(r"negar pendiente (\w[\w\-]+)", tl)
#         if m:
#             return f"Acción sugerida: negar pendiente {m.group(1)}"
#         m = re.search(r"cambiar orden (\w[\w\-]+)\s+a\s+([a-z_]+)", tl)
#         if m:
#             return f"Acción sugerida: cambiar orden {m.group(1)} a {m.group(2)}"
#     else:
#         m = re.search(r"approve pending (\w[\w\-]+)", tl)
#         if m:
#             return f"Suggested: approve pending {m.group(1)}"
#         m = re.search(r"deny pending (\w[\w\-]+)", tl)
#         if m:
#             return f"Suggested: deny pending {m.group(1)}"
#         m = re.search(r"change order (\w[\w\-]+)\s+to\s+([a-z_]+)", tl)
#         if m:
#             return f"Suggested: change order {m.group(1)} to {m.group(2)}"
#     return (f"Transcripción: {text}" if lang == "es" else f"Transcription: {text}")

from __future__ import annotations
from typing import List, Dict
import json
import re
import tempfile
import os
import wave
import streamlit as st
from dotenv import dotenv_values
from langchain_openai import ChatOpenAI
from openai import OpenAI
from backend.config import get_config
from backend.faq import match_faq
from backend.db import create_pending_question


def _get_llm(cfg: dict) -> ChatOpenAI:
    key = st.secrets.get(
        "OPENAI_API_KEY") or dotenv_values().get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Falta OPENAI_API_KEY en .env / secrets")
    model = cfg.get("model", "gpt-4o-mini")
    temp = float(cfg.get("temperature", 0.4))
    return ChatOpenAI(api_key=key, model=model, temperature=temp)


def _format_price(p) -> str:
    try:
        return f"{float(p):.2f}"
    except Exception:
        return str(p)


def _format_menu(menu: List[Dict]) -> str:
    lines = []
    for it in (menu or [])[:120]:
        name = it.get("name", "").strip()
        if not name:
            continue
        desc = (it.get("description") or "").strip()
        price = _format_price(it.get("price", 0))
        cur = it.get("currency", "USD")
        notes = (it.get("special_notes") or "").strip()
        notes_txt = f" — [{notes}]" if notes else ""
        line = f"- {name} ({cur} {price}){notes_txt}"
        if desc:
            line += f"\n  {desc}"
        lines.append(line)
    return "\n".join(lines)


def _system_prompt(cfg: dict, menu: List[Dict], lang: str) -> str:
    formatted_menu = _format_menu(menu)
    tone = cfg.get("tone") or ("Amable y profesional; breve, guiado." if lang ==
                               "es" else "Friendly and professional; concise, guided.")
    assistant_name = cfg.get(
        "assistant_name", "Asistente" if lang == "es" else "Assistant")
    if lang == "es":
        return (
            f"Eres {
                assistant_name}, un asistente de pedidos para un restaurante. Responde SIEMPRE en español.\n"
            f"Tu tono: {tone}\n\n"
            "Objetivo: ayudar al cliente a armar su pedido basado en el menú y confirmar datos. "
            "Sugiere acompañantes y bebidas. Si piden algo fuera del menú, pide elegir otra opción.\n\n"
            "🍽 Menú disponible:\n" + formatted_menu + "\n\n"
            "📌 Comportamiento:\n"
            "- Cálido, claro, paso a paso. No inventes productos/ingredientes.\n"
            "- Personalizaciones: acepta sin cebolla, salsa aparte, extra papas, etc. Ajusta precio si aplica.\n"
            '- Si no estás seguro: "⏳ Espera un momento por favor, estoy consultando con cocina…".\n'
            "- Usa la FAQ interna si hay respuesta registrada (no pidas confirmación humana si ya existe).\n"
            "- Lleva total aproximado mientras ordena.\n\n"
            "🧾 Cuando tengas el pedido y muestres el total, DI explícitamente:\n"
            "  “Ahora necesito unos datos para completar tu pedido…” y luego pregunta UNO A UNO:\n"
            "  1) nombre  2) teléfono  3) pickup o delivery  4) dirección (si delivery) o minutos de retiro (si pickup)  5) método de pago.\n"
            "Reconoce nombre, teléfono, tipo de entrega, dirección y pago en texto o audio transcrito.\n"
            "NO invites a confirmar hasta tener todos los datos.\n\n"
            "✅ Cuando todo esté completo: “Pedido listo para confirmación. Por favor, presiona el botón Confirmar Pedido.”\n"
            "🛑 Si dice “stop”, termina con amabilidad.\n"
            "🎯 Estilo: amable, profesional, breve y guiado."
        )
    else:
        return (
            f"You are {
                assistant_name}, a restaurant ordering assistant. ALWAYS answer in English.\n"
            f"Tone: {tone}\n\n"
            "Goal: help the customer build an order based on the menu and confirm details. "
            "Suggest sides and drinks. If off-menu, ask to pick an available option.\n\n"
            "🍽 Menu:\n" + formatted_menu + "\n\n"
            "📌 Behavior: warm, clear, step by step; no invention. "
            "Use internal FAQ if available. Keep a running total.\n\n"
            "🧾 Once you have the order and show the total, explicitly say:\n"
            '  “I now need a few details to complete your order…” and then ask ONE BY ONE:\n'
            "  1) name  2) phone  3) pickup or delivery  4) address (if delivery) or pickup minutes (if pickup)  5) payment method.\n"
            "Do NOT invite to confirm until all data are complete.\n\n"
            "✅ When everything is complete: “Order ready for confirmation. Please press Confirm Order.”\n"
            "🛑 If user says “stop”, end politely.\n"
            "🎯 Style: friendly, professional, concise and guided."
        )


# def client_assistant_reply(history: List[Dict], menu: List[Dict], cfg: dict | None, conversation_id: str) -> str:
#     cfg = cfg or get_config()
#     lang = cfg.get("language", "es")
#     last_user = next((m["content"] for m in reversed(
#         history) if m.get("role") == "user"), "")
#     if last_user:
#         faq_ans = match_faq(last_user, language=lang)
#         if faq_ans:
#             return faq_ans
#     llm = _get_llm(cfg)
#     sys = _system_prompt(cfg, menu, lang)
#     msgs = [{"role": "system", "content": sys}] + history[-12:]
#     res = llm.invoke(msgs)
#     reply = (res.content or "").strip()
#     low = reply.lower()
#     if ("consultando con cocina" in low) or ("checking with the kitchen" in low):
#         try:
#             create_pending_question(
#                 conversation_id=conversation_id, question=last_user, language=lang, ttl_seconds=60)
#         except Exception:
#             pass
#     return reply


def client_assistant_reply(history: List[Dict], menu: List[Dict], cfg: dict | None, conversation_id: str) -> str:
    """
    - Consulta FAQ antes que el LLM.
    - Refuerza en el prompt que NO pida datos personales hasta tener total o cierre del pedido.
    - Dispara 'pending' por dos vías:
        (a) Si el LLM devuelve la frase de consulta a cocina (ES/EN).
        (b) Heurística sobre el último mensaje del usuario cuando pide cosas fuera del menú o
            personalizaciones de ingredientes no listadas con claridad.
    """
    cfg = cfg or get_config()
    lang = cfg.get("language", "es")

    # --- 1) FAQ pre-check
    last_user = next((m["content"] for m in reversed(
        history) if m.get("role") == "user"), "")
    if last_user:
        faq_ans = match_faq(last_user, language=lang)
        if faq_ans:
            return faq_ans

    # --- 2) Reglas adicionales al prompt del sistema (no pedir datos hasta el final)
    llm = _get_llm(cfg)
    sys = _system_prompt(cfg, menu, lang)
    extra_rules = (
        "\n\n⚠️ Reglas adicionales importantes:\n"
        "- No solicites nombre, teléfono, dirección ni método de pago hasta que el cliente indique que terminó o hayas dado un total/subtotal claro.\n"
        "- Si el cliente pide algo fuera del menú o una personalización dudosa, responde con: "
        "\"⏳ Espera un momento por favor, estoy consultando con cocina…\" y NO inventes.\n"
    ) if lang == "es" else (
        "\n\n⚠️ Additional rules:\n"
        "- Do not ask for name, phone, address or payment method until the customer says they are done or you have provided a clear total/subtotal.\n"
        "- If the customer asks for something off-menu or a doubtful customization, reply: "
        "\"⏳ Please wait a moment, I'm checking with the kitchen…\" and do not make things up.\n"
    )
    sys = sys + extra_rules

    msgs = [{"role": "system", "content": sys}] + history[-12:]
    res = llm.invoke(msgs)
    reply = (res.content or "").strip()

    # --- 3) Trigger 'pending' por respuesta del LLM (palabras clave ES/EN)
    low = reply.lower()
    llm_signals = [
        "consultando con cocina",         # ES
        "checking with the kitchen",      # EN
        "consultar con cocina",           # ES
        "checking with kitchen"           # EN
    ]
    llm_suggests_pending = any(sig in low for sig in llm_signals)

    # --- 4) Trigger heurístico por mensaje del usuario si parece "difícil"
    def _normalize(s: str) -> str:
        return (s or "").lower().strip()

    def _menu_tokens(menu_items: List[Dict]) -> set:
        tokens = set()
        for it in (menu_items or []):
            name = _normalize(it.get("name", ""))
            desc = _normalize(it.get("description", ""))
            if name:
                tokens.update(re.findall(r"[a-záéíóúñü]+", name))
            if desc:
                tokens.update(re.findall(r"[a-záéíóúñü]+", desc))
        return tokens

    def _looks_difficult(user_text: str, menu_items: List[Dict]) -> bool:
        text = _normalize(user_text)
        if not text:
            return False

        # Señales de personalización/ingredientes
        intent_words = [
            "sin ", "con ", "extra ", "aparte", "remover", "quitar", "agregar", "añadir",
            "ingrediente", "gluten", "vegano", "celíac", "picant", "lactosa", "cambiar",
            # EN
            "without ", "with ", "extra ", "on the side", "remove", "add", "ingredient",
            "gluten", "vegan", "celiac", "spicy", "lactose", "swap", "replace"
        ]
        if any(w in text for w in intent_words):
            # Si no menciona con claridad un item del menú, lo marcamos como difícil
            menu_words = _menu_tokens(menu_items)
            user_words = set(re.findall(r"[a-záéíóúñü]+", text))
            overlap = len(menu_words.intersection(user_words))
            # Umbral bajo para evitar falsos negativos
            if overlap < 1:
                return True

        # Señales de pedir algo que no suena a lo listado
        off_menu_markers = [
            "no está en el menú", "no veo en el menú", "tienen X?", "hacen X?",
            "do you have", "not on the menu", "can you make", "custom"
        ]
        if any(m in text for m in off_menu_markers):
            return True

        return False

    heuristic_difficult = _looks_difficult(last_user, menu)

    # --- 5) Crear pending si corresponde (por cualquiera de los triggers)
    if llm_suggests_pending or heuristic_difficult:
        try:
            create_pending_question(
                conversation_id=conversation_id,
                question=last_user or "(consulta del cliente)",
                language=lang,
                ttl_seconds=60
            )
        except Exception:
            # fallar silencioso para no romper UX, el autoaprobado seguirá funcionando
            pass

    return reply


# ── Extracción de datos mejorada
_NAME_PAT_ES = re.compile(
    r"(?i)(?:me\s+llamo|soy|mi\s+nombre\s*(?:es|:))\s*([A-Za-zÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑ\s]{1,})")
_NAME_PAT_EN = re.compile(
    r"(?i)(?:i\s*am|i'm|my\s+name\s*(?:is|:))\s*([A-Za-z][A-Za-z\s]{1,})")
# teléfono: también si aparece un número sin “phone”, capturamos secuencias de 7+ dígitos
_PHONE_PAT_HINT = re.compile(r"(?<!\d)(\+?\d[\d\-\s]{6,}\d)(?!\d)")
_PHONE_PAT_LABELED = re.compile(
    r"(?i)(?:tel[eé]fono|phone|cel|cell|m[oó]vil|mobile)\s*(?:es|is|:)?\s*(\+?\d[\d\-\s]{6,}\d)")
_ADDRESS_PAT_ES = re.compile(r"(?i)direcci[oó]n\s*(?:es|:)?\s*(.+)")
_ADDRESS_PAT_EN = re.compile(r"(?i)address\s*(?:is|:)?\s*(.+)")
_MIN_PAT = re.compile(r"(?i)(\d{1,3})\s*(?:min|minute|minutes|minutos)")
_DELIVERY_ES = re.compile(r"(?i)(domicilio|delivery|enviar|entrega)")
_PICKUP_ES = re.compile(r"(?i)(retir|recoger|pickup)")
_DELIVERY_EN = re.compile(r"(?i)(delivery|deliver)")
_PICKUP_EN = re.compile(r"(?i)(pickup|pick up)")


def extract_client_info(history: List[Dict], lang: str) -> Dict:
    text = " \n".join([m.get("content", "")
                      for m in history if m.get("role") == "user"])
    out = {"name": "", "phone": "", "delivery_type": "",
           "address": "", "pickup_eta_min": "", "payment_method": ""}

    m = (_NAME_PAT_ES.search(text) if lang ==
         "es" else _NAME_PAT_EN.search(text))
    if m:
        out["name"] = m.group(1).strip()

    # teléfono con o sin etiqueta
    m = _PHONE_PAT_LABELED.search(text) or _PHONE_PAT_HINT.search(text)
    if m:
        out["phone"] = re.sub(r"\s+", "", m.group(1)).replace("-", "")

    if (_DELIVERY_ES.search(text) if lang == "es" else _DELIVERY_EN.search(text)):
        out["delivery_type"] = "delivery"
    if (_PICKUP_ES.search(text) if lang == "es" else _PICKUP_EN.search(text)):
        out["delivery_type"] = out["delivery_type"] or "pickup"

    m = (_ADDRESS_PAT_ES.search(text) if lang ==
         "es" else _ADDRESS_PAT_EN.search(text))
    if m:
        out["address"] = m.group(1).strip()

    m = _MIN_PAT.search(text)
    if m:
        out["pickup_eta_min"] = m.group(1).strip()

    if re.search(r"(?i)(efectivo|cash)", text):
        out["payment_method"] = "cash"
    elif re.search(r"(?i)(tarjeta|card)", text):
        out["payment_method"] = "card"
    elif re.search(r"(?i)(online|transfer|transferencia|bank)", text):
        out["payment_method"] = "online"

    return out


def ensure_all_required_present(info: Dict, lang: str) -> List[str]:
    req = ["name", "phone", "delivery_type", "payment_method"]
    if info.get("delivery_type") == "delivery":
        req.append("address")
    else:
        req.append("pickup_eta_min")
    missing = [k for k in req if not str(info.get(k, "")).strip()]
    if "pickup_eta_min" in missing and info.get("delivery_type") == "pickup":
        info["pickup_eta_min"] = 30  # default razonable
        missing.remove("pickup_eta_min")
    return missing


def parse_items_from_chat(history: List[Dict], menu: List[Dict], cfg: dict) -> List[Dict]:
    llm = _get_llm(cfg)
    lang = cfg.get("language", "es")
    names = [m["name"] for m in (menu or [])]
    price_map = {m["name"]: float(m.get("price", 0.0)) for m in (menu or [])}
    sys = ("Devuelve exclusivamente un JSON UTF-8: "
           '[{"name":"...","qty":N,"unit_price":P}]' if lang == "es"
           else "Return ONLY a UTF-8 JSON list: "
           '[{"name":"...","qty":N,"unit_price":P}]')
    user_text = "\n".join([m["content"]
                          for m in history if m.get("role") == "user"])[-2000:]
    prompt = (f"Menú: {names}\nPrecios: {price_map}\nExtrae items/cantidades/precios."
              if lang == "es" else
              f"Menu items: {names}\nPrices: {price_map}\nExtract items/quantities/prices.")
    try:
        out = llm.invoke([{"role": "system", "content": sys}, {
                         "role": "user", "content": prompt+"\n\n"+user_text}]).content
        data = json.loads(out)
        clean = []
        for d in (data if isinstance(data, list) else []):
            nm = d.get("name")
            if nm in price_map:
                clean.append({"name": nm, "qty": int(d.get("qty", 1)), "unit_price": float(
                    d.get("unit_price", price_map[nm]))})
        if clean:
            return clean
    except Exception:
        pass
    # Fallback: coincidencias por nombre
    text_low = user_text.lower()
    items = []
    for nm, pr in price_map.items():
        if nm.lower() in text_low:
            items.append({"name": nm, "qty": 1, "unit_price": pr})
    return items

# Audio


def _bytes_to_wav_temp(raw_pcm: bytes, channels: int = 1, sample_width: int = 2, frame_rate: int = 16000) -> str:
    try:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(frame_rate)
            wf.writeframes(raw_pcm)
        return path
    except Exception:
        return ""


def _transcribe_file(path: str) -> str:
    key = st.secrets.get(
        "OPENAI_API_KEY") or dotenv_values().get("OPENAI_API_KEY")
    if not key or not path or not os.path.isfile(path):
        return ""
    client = OpenAI(api_key=key)
    try:
        with open(path, "rb") as f:
            tr = client.audio.transcriptions.create(model="whisper-1", file=f)
        return tr.text or ""
    except Exception:
        return ""


def client_voice_to_text(raw_audio_bytes: bytes, cfg: dict) -> str:
    path = _bytes_to_wav_temp(raw_audio_bytes)
    if not path:
        return ""
    try:
        return _transcribe_file(path)
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def admin_voice_command(raw_audio_bytes: bytes, cfg: dict, lang: str) -> str:
    text = client_voice_to_text(raw_audio_bytes, cfg) or ""
    if not text:
        return "No se pudo transcribir audio." if lang == "es" else "Could not transcribe audio."
    tl = text.lower()
    if lang == "es":
        m = re.search(r"aprobar pendiente (\w[\w\-]+)", tl)
        if m:
            return f"Acción sugerida: aprobar pendiente {m.group(1)}"
        m = re.search(r"negar pendiente (\w[\w\-]+)", tl)
        if m:
            return f"Acción sugerida: negar pendiente {m.group(1)}"
        m = re.search(r"cambiar orden (\w[\w\-]+)\s+a\s+([a-z_]+)", tl)
        if m:
            return f"Acción sugerida: cambiar orden {m.group(1)} a {m.group(2)}"
    else:
        m = re.search(r"approve pending (\w[\w\-]+)", tl)
        if m:
            return f"Suggested: approve pending {m.group(1)}"
        m = re.search(r"deny pending (\w[\w\-]+)", tl)
        if m:
            return f"Suggested: deny pending {m.group(1)}"
        m = re.search(r"change order (\w[\w\-]+)\s+to\s+([a-z_]+)", tl)
        if m:
            return f"Suggested: change order {m.group(1)} to {m.group(2)}"
    return (f"Transcripción: {text}" if lang == "es" else f"Transcription: {text}")
