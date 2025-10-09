# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

# # backend/langgraph_agents.py
# from __future__ import annotations
# import re
# import json
# from typing import Dict, Any, List, Optional
# from langgraph.graph import StateGraph, END
# from pydantic import BaseModel, Field
# from .llm_providers import chat_completion
# from .utils import (
#     basic_parse_items_from_text,
#     compute_total,
#     format_menu_for_prompt,
#     ensure_required_info,
# )
# from .db import create_pending, expired_pending_autoapprove, SessionLocal, PendingConfirmation


# class OrderState(BaseModel):
#     conversation_id: str
#     language: str = "es"
#     # [{"role":"user/assistant","content":...}]
#     messages: List[Dict[str, str]] = Field(default_factory=list)
#     menu: List[Dict[str, Any]] = Field(default_factory=list)
#     items: List[Dict[str, Any]] = Field(
#         default_factory=list)     # {"name","qty","unit_price"}
#     payment_method: Optional[str] = None
#     # {"name","phone","delivery_type","delivery_address","pickup_eta_min"}
#     client_info: Dict[str, Any] = Field(default_factory=dict)
#     needs_human: bool = False
#     human_question: Optional[str] = None
#     pending_id: Optional[str] = None
#     notes: str = ""


# def _sys_prompt(lang: str, menu: List[Dict[str, Any]]) -> str:
#     menu_str = format_menu_for_prompt(menu)
#     if lang == "es":
#         return (
#             "Eres un asistente de pedidos para un restaurante. Responde SIEMPRE en español. "
#             "Objetivo: ayudar al cliente a armar su pedido basado en el menú y confirmar datos. "
#             "Puedes sugerir acompañantes y bebidas. Si piden algo fuera del menú, pide elegir otra opción. "
#             "Menú:\n" + menu_str
#         )
#     else:
#         return (
#             "You are a restaurant order assistant. Always respond in English. "
#             "Goal: help the customer build an order based on the menu and confirm details. "
#             "You can suggest sides and drinks. If they ask for something off-menu, ask them to pick another option. "
#             "Menu:\n" + menu_str
#         )


# # ----------------- NODES (solo aceptan `state`) -----------------

# def node_parse(state: OrderState) -> OrderState:
#     """Parse ordered items (LLM first; fallback naive)."""
#     user_last = ""
#     for m in reversed(state.messages):
#         if m["role"] == "user":
#             user_last = m["content"]
#             break

#     # Intento con LLM
#     system = _sys_prompt(state.language, state.menu) + \
#         "\nExtract the ordered items with quantities as JSON: [{name, qty}]."
#     try:
#         content = chat_completion(system, state.messages)
#         jmatch = re.search(r"\[[\s\S]*\]", content)
#         if jmatch:
#             arr = json.loads(jmatch.group(0))
#             items = []
#             name_to_price = {it["name"]: it["price"] for it in state.menu}
#             for it in arr:
#                 nm = it.get("name")
#                 qty = int(it.get("qty", 1))
#                 if nm in name_to_price:
#                     items.append(
#                         {"name": nm, "qty": qty, "unit_price": name_to_price[nm]})
#             if items:
#                 state.items = items
#     except Exception:
#         pass

#     if not state.items:
#         # Fallback naive
#         state.items = basic_parse_items_from_text(user_last, state.menu)
#     return state


# def node_check_customization(state: OrderState) -> OrderState:
#     """Decide si hace falta confirmación humana por personalización/alergias/cambios."""
#     user_last = ""
#     for m in reversed(state.messages):
#         if m["role"] == "user":
#             user_last = m["content"].lower()
#             break

#     trigger = any(k in user_last for k in [
#         "sin ", "without", "swap", " alerg", " allergy", "extra ", "add ", "remove ", "quitar", "agregar"
#     ])
#     if trigger:
#         state.needs_human = True
#         state.human_question = (
#             state.messages[-1]["content"] if state.messages else "")
#     return state


# def node_create_pending(state: OrderState) -> OrderState:
#     """Crea el pending de confirmación humana (TTL 60s) si hace falta."""
#     if state.needs_human and not state.pending_id:
#         sess = SessionLocal()
#         try:
#             p = create_pending(sess, state.conversation_id,
#                                state.human_question, ttl_seconds=60)
#             state.pending_id = p.id
#         finally:
#             sess.close()
#     return state


# def node_wait_or_autoapprove(state: OrderState) -> OrderState:
#     if not state.pending_id:
#         return state
#     sess = SessionLocal()
#     try:
#         expired_pending_autoapprove(sess)
#         p = sess.query(PendingConfirmation).get(state.pending_id)
#         if p and p.resolved:
#             if p.resolution.startswith("custom:"):
#                 admin_msg = p.resolution.split("custom:", 1)[1].strip()
#                 state.messages.append(
#                     {"role": "assistant", "content": admin_msg})
#             elif p.resolution == "denied":
#                 msg = ("Lo siento, no es posible esa modificación. ¿Deseas otra opción?"
#                        if state.language == "es" else
#                        "Sorry, that customization isn't possible. Would you like another option?")
#                 state.messages.append({"role": "assistant", "content": msg})
#             elif p.resolution == "approved":  # <-- AÑADIR ESTE BLOQUE
#                 msg = ("He confirmado tu solicitud. ¡Continuemos!"
#                        if state.language == "es" else
#                        "I’ve confirmed your request. Let’s continue!")
#                 state.messages.append({"role": "assistant", "content": msg})
#             # aprobado/denegado/custom ya resuelto
#             state.needs_human = False
#             return state

#         # si sigue pendiente, mostramos el mensaje de espera
#         wait_msg = ("Necesito confirmar esto con el restaurante. Dame 1 minuto por favor..."
#                     if state.language == "es" else
#                     "I need to confirm this with the restaurant. Give me 1 minute please...")
#         state.messages.append({"role": "assistant", "content": wait_msg})
#         return state
#     finally:
#         sess.close()


# def node_collect_info(state: OrderState) -> OrderState:
#     """Pide datos faltantes; si está todo, entrega resumen + total."""
#     missing = ensure_required_info(state.model_dump())
#     if missing:
#         ask = (
#             "Para confirmar tu pedido necesito: " +
#             ", ".join(missing) + ". Por favor indícame."
#             if state.language == "es" else
#             "To confirm your order I still need: " +
#             ", ".join(missing) + ". Please tell me."
#         )
#         state.messages.append({"role": "assistant", "content": ask})
#         return state

#     total = compute_total(state.items)
#     currency = state.menu[0].get("currency", "USD") if state.menu else "USD"
#     items_txt = "\n".join(
#         [f"- {i['qty']} x {i['name']} ({currency} {i['unit_price']:.2f})" for i in state.items])
#     summary = (
#         f"Resumen de tu pedido:\n{items_txt}\nTotal: {
#             currency} {total:.2f}\n¿Confirmas?"
#         if state.language == "es" else
#         f"Order summary:\n{items_txt}\nTotal: {
#             currency} {total:.2f}\nDo you confirm?"
#     )
#     state.messages.append({"role": "assistant", "content": summary})
#     return state


# def build_graph():
#     sg = StateGraph(OrderState)
#     sg.add_node("parse", node_parse)
#     sg.add_node("check_customization", node_check_customization)
#     sg.add_node("create_pending", node_create_pending)
#     sg.add_node("wait_or_autoapprove", node_wait_or_autoapprove)
#     sg.add_node("collect_info", node_collect_info)

#     sg.set_entry_point("parse")
#     sg.add_edge("parse", "check_customization")
#     sg.add_edge("check_customization", "create_pending")
#     sg.add_edge("create_pending", "wait_or_autoapprove")
#     sg.add_edge("wait_or_autoapprove", "collect_info")
#     sg.add_edge("collect_info", END)

#     return sg.compile()

# backend/langgraph_agents.py
from __future__ import annotations
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

# Grafo mínimo que:
# 1) Lee el último mensaje del usuario
# 2) Genera una respuesta simple, sugiere 2-3 ítems del menú
# 3) Devuelve el estado con un mensaje del asistente


def _reply_simple(state: Dict[str, Any]) -> Dict[str, Any]:
    lang = (state.get("language") or "es").lower()
    messages: List[Dict[str, str]] = state.get("messages", [])
    menu: List[Dict[str, Any]] = state.get("menu", [])

    user_last = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_last = m.get("content", "")
            break

    # Heurística simple de sugerencias
    suggestions = [it.get("name", "") for it in (menu[:3] if menu else [])]
    if lang == "es":
        text = "Puedo sugerirte: " + \
            ", ".join(suggestions) + ". ¿Qué te gustaría pedir?"
    else:
        text = "I can suggest: " + \
            ", ".join(suggestions) + ". What would you like to order?"

    out = dict(state)
    out.setdefault("messages", [])
    out["messages"] = list(messages) + [{"role": "assistant", "content": text}]
    return out


def build_graph():
    sg = StateGraph(dict)  # usamos estados como dict
    sg.add_node("reply_simple", _reply_simple)
    sg.set_entry_point("reply_simple")
    sg.add_edge("reply_simple", END)
    return sg.compile()
