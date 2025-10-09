# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:20:15 2025

@author: geam9
"""

from __future__ import annotations
import re
from typing import List, Dict, Any
from dotenv import dotenv_values
from openai import OpenAI

_cfg = dotenv_values(".env")
_client = OpenAI(api_key=_cfg.get("OPENAI_API_KEY"))

# ---------- Prompt / Chat ----------


def _format_menu(menu: List[Dict]) -> str:
    lines = []
    for m in menu:
        price = f'{m.get("currency", "")} {float(m.get("price", 0.0)):.2f}'
        notes = f" [{m.get('special_notes')}]" if m.get(
            "special_notes") else ""
        lines.append(
            f"- {m.get('name', '')} — {price}{notes}: {m.get('description', '')}")
    return "\n".join(lines)


def _build_system_prompt(menu: List[Dict], cfg: Dict) -> str:
    lang = cfg.get("language", "es")
    assistant_name = cfg.get(
        "assistant_name", "Asistente" if lang == "es" else "Assistant")
    tone = cfg.get("tone", "Amable y profesional; breve y guiado." if lang ==
                   "es" else "Friendly and professional; concise and guided.")
    formatted_menu = _format_menu(menu)

    if lang == "es":
        return (
            f"Eres {assistant_name}, un asistente de pedidos para un restaurante. {
                tone}\n"
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
            "Menú:\n" + formatted_menu
        )
    else:
        return (
            f"You are {assistant_name}, a restaurant ordering assistant. {
                tone}\n"
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
            "Menu:\n" + formatted_menu
        )


def client_assistant_reply(messages: List[Dict[str, str]], menu: List[Dict], cfg: Dict, conversation_id: str) -> str:
    model = cfg.get("model", "gpt-4o-mini")
    temperature = float(cfg.get("temperature", 0.4))
    sys_prompt = _build_system_prompt(menu, cfg)
    msg_payload = [{"role": "system", "content": sys_prompt}] + messages[-12:]
    rsp = _client.chat.completions.create(
        model=model, temperature=temperature, messages=msg_payload)
    return rsp.choices[0].message.content.strip()

# ---------- STT (Whisper-1) ----------


def client_voice_to_text(pcm_bytes: bytes, cfg: Dict) -> str:
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(pcm_bytes)
            tmp.flush()
            with open(tmp.name, "rb") as fh:
                tr = _client.audio.transcriptions.create(
                    model="whisper-1", file=fh, response_format="text",
                    language=cfg.get("language", "es")
                )
                return tr
    except Exception:
        return ""


# ---------- Extracción de datos (igual que antes; omito comentarios por brevedad) ----------
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-\(\)]{6,}\d)")
_MIN_RE = re.compile(
    r"\b(\d{1,3})\s*(?:min|mins|minutos|minutes)\b", re.IGNORECASE)


def _norm(s: str) -> str:
    import re as _re
    return _re.sub(r"\s+", " ", s or "").strip()


def _extract_name(text: str, lang: str) -> str:
    if lang == "es":
        pats = [r"\bme llamo ([A-Za-zÁÉÍÓÚÑáéíóúñ ]{2,40})",
                r"\bmi nombre es ([A-Za-zÁÉÍÓÚÑáéíóúñ ]{2,40})", r"\bsoy ([A-Za-zÁÉÍÓÚÑáéíóúñ ]{2,40})"]
    else:
        pats = [r"\bmy name is ([A-Za-z' \-]{2,40})",
                r"\bi am ([A-Za-z' \-]{2,40})", r"\bthis is ([A-Za-z' \-]{2,40})"]
    for p in pats:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return _norm(m.group(1))
    m = re.search(
        r"(?:nombre|name)\s*[:\-]\s*([A-Za-zÁÉÍÓÚÑáéíóúñ' \-]{2,40})", text, re.IGNORECASE)
    return _norm(m.group(1)) if m else ""


def _extract_phone(text: str) -> str:
    phones = _PHONE_RE.findall(text)
    if not phones:
        return ""
    ph = phones[-1]
    ph = re.sub(r"[^\d\+]", "", ph)
    return ph[:20]


def _extract_delivery_type(text: str, lang: str) -> str:
    if re.search(r"\b(delivery|a domicilio|entrega)\b", text, re.IGNORECASE):
        return "delivery"
    if re.search(r"\b(pickup|recoger|retiro|retiro en local)\b", text, re.IGNORECASE):
        return "pickup"
    return ""


def _extract_address(text: str, lang: str) -> str:
    m = re.search(r"(?:dirección|address)\s*[:\-]\s*(.+)", text, re.IGNORECASE) or \
        re.search(r"(?:mi\s+dirección\s+es|my\s+address\s+is)\s*(.+)",
                  text, re.IGNORECASE)
    return _norm(m.group(1)) if m else ""


def _extract_payment(text: str, lang: str) -> str:
    opts = {
        "cash": ["efectivo", "cash"],
        "card": ["tarjeta", "card", "credit", "debit", "crédito", "débito"],
        "transfer": ["transferencia", "bank", "nequi", "yape", "plin", "bizum", "zelle"],
    }
    for k, words in opts.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE):
                return k
    m = re.search(
        r"(?:pago|payment).{0,15}[:\-]\s*([A-Za-z ]+)", text, re.IGNORECASE)
    return _norm(m.group(1)).lower() if m else ""


def _extract_eta(text: str, lang: str) -> int:
    m = _MIN_RE.search(text)
    if m:
        try:
            return int(m.group(1))
        except:
            return 0
    return 0


def extract_client_info(messages: List[Dict[str, str]], lang: str) -> Dict[str, Any]:
    full = " ".join([m.get("content", "")
                    for m in messages]).replace("\n", " ").lower()
    info = {
        "name": _extract_name(full, lang),
        "phone": _extract_phone(full),
        "delivery_type": _extract_delivery_type(full, lang),
        "address": _extract_address(full, lang),
        "payment_method": _extract_payment(full, lang),
        "pickup_eta_min": _extract_eta(full, lang),
    }
    if info["delivery_type"] != "delivery":
        info["address"] = info["address"] or ""
    return info


def ensure_all_required_present(info: Dict[str, Any], lang: str) -> List[str]:
    missing = []
    if not info.get("name"):
        missing.append("name")
    if not info.get("phone"):
        missing.append("phone")
    if not info.get("delivery_type"):
        missing.append("delivery_type")
    if info.get("delivery_type") == "delivery":
        if not info.get("address"):
            missing.append("address")
    else:
        if not info.get("pickup_eta_min"):
            missing.append("pickup_eta_min")
    if not info.get("payment_method"):
        missing.append("payment_method")
    return missing


def parse_items_from_chat(messages: List[Dict[str, str]], menu: List[Dict], cfg: Dict) -> List[Dict]:
    text = " ".join([m.get("content", "") for m in messages]).lower()
    items = []
    for m in menu:
        name = (m.get("name", "") or "").lower()
        if not name:
            continue
        if name in text:
            qty = 1
            m1 = re.search(rf"{re.escape(name)}\s*(?:x|\*)\s*(\d+)", text)
            m2 = re.search(rf"(\d+)\s+(?:de\s+)?{re.escape(name)}", text)
            if m1:
                qty = int(m1.group(1))
            elif m2:
                qty = int(m2.group(1))
            items.append({"id": m.get("id"), "name": m.get("name"), "qty": max(1, qty),
                          "unit_price": float(m.get("price", 0.0)), "currency": m.get("currency", "USD")})
    by_name = {}
    for it in items:
        k = it["name"]
        by_name[k] = {"id": it["id"], "name": k, "qty": by_name.get(k, {"qty": 0})["qty"] + it["qty"],
                      "unit_price": it["unit_price"], "currency": it["currency"]}
    # recuperar el nombre correcto (no en lower)
    final = []
    for k, v in by_name.items():
        orig = next((mm for mm in menu if mm["name"].lower() == k), None)
        v["name"] = orig["name"] if orig else k
        final.append(v)
    return final

# ---------- Admin voice commands ----------


def admin_voice_command(pcm_bytes: bytes, cfg: Dict, lang: str = "es") -> str:
    """
    Transcribe audio y ejecuta cambios de estado:
      - "orden <ID> a preparado/listo/entregado"
      - "set order <ID> to preparing/ready/delivered"
    Devuelve un resumen de la acción.
    """
    text = client_voice_to_text(pcm_bytes, cfg) or ""
    if not text:
        return "No se reconoció audio." if lang == "es" else "No audio recognized."

    low = text.lower()
    # extrae algo que luzca como ID (hex o alfanum largo)
    m = re.search(r"\b([a-f0-9]{12,32}|\w{8,})\b", low)
    order_id = m.group(1) if m else ""

    # mapping de estados
    if lang == "es":
        map_es = {
            "confirmada": "confirmed", "preparada": "preparing", "preparando": "preparing",
            "lista": "ready", "listo": "ready", "entregada": "delivered", "entregado": "delivered"
        }
        target = ""
        for k, v in map_es.items():
            if re.search(rf"\b{k}\b", low):
                target = v
                break
        if not order_id or not target:
            return f"Transcrito: “{text}”. Faltó identificar ID o estado."
        # actualizar
        from backend.db import update_order_status
        update_order_status(order_id, target)
        return f"OK: orden {order_id} → {target} (voz)."
    else:
        map_en = {
            "confirmed": "confirmed", "confirm": "confirmed",
            "preparing": "preparing", "prepare": "preparing",
            "ready": "ready",
            "delivered": "delivered", "deliver": "delivered"
        }
        target = ""
        for k, v in map_en.items():
            if re.search(rf"\b{k}\b", low):
                target = v
                break
        if not order_id or not target:
            return f"Transcribed: “{text}”. Order ID or status not detected."
        from backend.db import update_order_status
        update_order_status(order_id, target)
        return f"OK: order {order_id} → {target} (voice)."
