# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:32 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from backend.config import get_config
from backend.db import ensure_db_and_seed, fetch_menu, fetch_menu_images, create_order_from_chat_ready
from backend.utils import render_auto_carousel
from backend.llm_chat import llm_reply, extract_fields_from_text

st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

st.markdown("""
<style>
.chat-box{border:1px solid #eee;border-radius:12px;padding:10px;height:380px;overflow-y:auto;background:#fafafa}
.msg{margin:6px 0;max-width:80%;}
.user{background:#DCF8C6;align-self:flex-end;border-radius:14px 14px 0 14px;padding:8px 10px;display:inline-block;}
.bot{background:#fff;border-radius:14px 14px 14px 0;padding:8px 10px;display:inline-block;border:1px solid #eee;}
</style>
""", unsafe_allow_html=True)


def _t(lang): return (lambda es, en: es if lang == "es" else en)


def _menu_text(menu, currency):
    lines = []
    for m in menu:
        lines.append(f"- {m['name']} ({currency} {m['price']:.2f}): {m['description']} [{m.get('special_notes', '')}]")
    return "\n".join(lines)


def _missing_fields(ci: dict, lang: str) -> list[str]:
    need = []
    if not ci.get("name"):
        need.append("nombre" if lang == "es" else "name")
    if not ci.get("phone"):
        need.append("teléfono" if lang == "es" else "phone")
    if not ci.get("delivery_type"):
        need.append("entrega/retiro" if lang == "es" else "delivery/pickup")
    if ci.get("delivery_type") == "delivery" and not ci.get("address"):
        need.append("dirección" if lang == "es" else "address")
    if not ci.get("payment_method"):
        need.append("método de pago" if lang == "es" else "payment method")
    return need


def main():
    ensure_db_and_seed()  # asegura migración + seed
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    menu = fetch_menu()
    imgs = fetch_menu_images()
    currency = cfg.get("currency", "USD")

    st.title("💬 " + ("Cliente" if lang == "es" else "Client"))
    if imgs:
        render_auto_carousel(imgs, height_px=160, interval_sec=4)

    col_menu, col_chat = st.columns([1.1, 1.2])
    with col_menu:
        st.subheader(t("Menú", "Menu"))
        if menu:
            for m in menu:
                st.markdown(f"**{m['name']}** · {currency} {m['price']:.2f}\n\n_{
                            m['description']}_  \n`{m.get('special_notes', '')}`")
        else:
            st.info(t("Sin ítems aún. El restaurante debe cargar el menú.",
                    "No items yet. Restaurant must upload the menu."))

    with col_chat:
        st.subheader(t("Chat", "Chat"))
        if "msgs" not in st.session_state:
            st.session_state.msgs = []
        if "client_info" not in st.session_state:
            st.session_state.client_info = {}
        if "order_ready" not in st.session_state:
            st.session_state.order_ready = False

        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for role, txt in st.session_state.msgs:
            if role == "user":
                st.markdown(f'<div class="msg" style="display:flex;justify-content:flex-end;"><div class="user">{
                            txt}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg"><div class="bot">{
                            txt}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        usr = st.text_input(t("Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
                              "Thanks for reaching us. How can we help?"), key="user_txt")
        send = st.button(t("Enviar", "Send"))
        if send and usr.strip():
            st.session_state.msgs.append(("user", usr.strip()))
            # extracción ligera de campos
            found = extract_fields_from_text(usr)
            st.session_state.client_info.update(
                {k: v for k, v in found.items() if v})

            # respuesta LLM
            menu_text = _menu_text(menu, currency)
            try:
                bot = llm_reply(usr.strip(), menu_text)
            except Exception as e:
                bot = t("Error con el modelo. Intenta de nuevo.",
                        "Model error. Try again.")
            st.session_state.msgs.append(("assistant", bot))

            # validación de “listo para confirmar”
            missing = _missing_fields(st.session_state.client_info, lang)
            if not missing:
                # dar luz: listo para confirmación
                st.session_state.msgs.append(("assistant", t(
                    "Pedido listo para confirmación. Por favor, presiona el botón Confirmar Pedido.",
                    "Order ready for confirmation. Please press the Confirm Order button."
                )))
                st.session_state.order_ready = True
            else:
                st.session_state.order_ready = False

            st.rerun()

        # Confirmar
        if st.session_state.order_ready:
            if st.button(t("Confirmar pedido", "Confirm order")):
                ci = st.session_state.client_info
                missing = _missing_fields(ci, lang)
                if missing:
                    st.warning(t("Faltan datos: ", "Missing: ") +
                               ", ".join(missing))
                else:
                    # Para demo: construye items mínimos desde el chat (no NLU complejo aquí)
                    # En producción extraerías ítems con un parser estructurado.
                    items = []
                    # Si el usuario mencionó algo del menú, arma un item base:
                    # (demo) agregamos Hamburguesa 1u si no hay nada
                    if not items:
                        burger = next(
                            (m for m in menu if "hamburguesa".lower() in m["name"].lower()), None)
                        ref = burger or (menu[0] if menu else None)
                        if ref:
                            items = [{"id": ref["id"], "name": ref["name"], "qty": 1,
                                      "unit_price": ref["price"], "currency": currency}]
                    try:
                        create_order_from_chat_ready(
                            ci, items, currency=currency)
                        st.success(
                            t("¡Pedido confirmado!", "Order confirmed!"))
                        st.session_state.msgs.append(("assistant", t(
                            "¡Listo! Tu pedido estará listo en ~30 minutos (entrega) o según tu tiempo de retiro.",
                            "Done! Your order will be ready in ~30 minutes (delivery) or according to your pickup time."
                        )))
                        st.session_state.order_ready = False
                    except Exception as e:
                        st.error(f"DB error: {e}")
