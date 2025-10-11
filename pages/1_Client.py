# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:32 2025

@author: geam9
"""

# from __future__ import annotations
# import streamlit as st
# from uuid import uuid4
# from streamlit_webrtc import webrtc_streamer, WebRtcMode
# import av
# import numpy as np
# from backend.utils import render_js_carousel

# from backend.config import get_config
# from backend.db import (
#     fetch_menu, fetch_menu_banners, create_order_from_chat_ready,
#     fetch_menu_images
# )
# from backend.llm_chat import (
#     client_assistant_reply, extract_client_info, ensure_all_required_present,
#     parse_items_from_chat, client_voice_to_text
# )
# from backend.utils import menu_table_component, menu_gallery_component
# import time


# def carousel(images: list[str], key_prefix: str, lang: str, interval_sec: int = 5):
#     if "carousel_state" not in st.session_state:
#         st.session_state.carousel_state = {}
#     state = st.session_state.carousel_state.setdefault(
#         key_prefix, {"idx": 0, "on": True})

#     # Toggle y avance
#     colA, colB = st.columns([1, 3])
#     with colA:
#         state["on"] = st.toggle(
#             "⏯️ Auto", value=state["on"], key=f"{key_prefix}_auto")
#     with colB:
#         st.caption("Avanza cada 5s" if lang == "es" else "Advances every 5s")

#     if images:
#         from backend.utils import _image  # usa tu helper
#         _image(images[state["idx"]])

#         # Controles manuales
#         c1, c2, c3 = st.columns(3)
#         if c1.button("⏮️", key=f"{key_prefix}_prev"):
#             state["idx"] = (state["idx"]-1) % len(images)
#             st.rerun()
#         if c3.button("⏭️", key=f"{key_prefix}_next"):
#             state["idx"] = (state["idx"]+1) % len(images)
#             st.rerun()

#         # Autoavance simple por refresh
#         if state["on"]:
#             # Inyecta refresh a los 5s SIN tocar toda la app (solo recarga la página)
#             st.markdown(
#                 f"<meta http-equiv='refresh' content='{interval_sec}'>",
#                 unsafe_allow_html=True
#             )
#             # al volver a correr, avanzamos índice
#             state["idx"] = (state["idx"]+1) % len(images)


# st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

# st.markdown("""
# <style>
# /* Caja de chat con scroll interno */
# .chat-box {
#   border: 1px solid #eee; border-radius: 12px;
#   padding: 10px 12px; height: 52vh; overflow-y: auto;
#   background: #fafafa;
# }
# /* Burbujas estilo WhatsApp */
# .msg-user { background:#DCF8C6; color:#222; padding:10px 12px; border-radius:14px; margin:6px 0; max-width:88%; align-self:flex-end; }
# .msg-bot  { background:#ffffff; color:#222; padding:10px 12px; border-radius:14px; margin:6px 0; max-width:88%; align-self:flex-start; border:1px solid #eee; }
# /* Pie con input */
# .input-row { position: sticky; bottom: 0; background: #fff; padding-top: 8px; }
# @media (max-width: 768px){
#   .chat-box { height: 54vh; }
# }
# </style>
# """, unsafe_allow_html=True)


# def _t(lang):
#     return (lambda es, en: es if lang == "es" else en)


# def _image_compat(img):
#     try:
#         st.image(img, width='stretch')
#     except TypeError:
#         st.image(img, use_column_width=True)


# def main():
#     cfg = get_config()
#     lang = cfg.get("language", "es")
#     t = _t(lang)
#     currency = cfg.get("currency", "USD")

#     st.title(t("💬 Cliente", "💬 Client"))

#     # banners = fetch_menu_banners()
#     # if banners:
#     #     _image_compat(banners[0])

#     menu = fetch_menu()
#     if not menu:
#         st.warning(t("El restaurante aún no ha cargado su menú.",
#                    "The restaurant has not uploaded its menu yet."))
#         return

#     if "conv_id" not in st.session_state:
#         st.session_state.conv_id = uuid4().hex
#     if "conv" not in st.session_state:
#         st.session_state.conv = [{"role": "assistant", "content": t(
#             "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
#             "Thanks for contacting us. How can we help?"
#         )}]
#     if "client_info" not in st.session_state:
#         st.session_state.client_info = {}
#     if "order_items" not in st.session_state:
#         st.session_state.order_items = []

#     view = st.radio(t("Visualización del menú", "Menu view"), [
#                     t("Tabla", "Table"), t("Imágenes", "Images")], horizontal=True)
#     col_menu, col_chat = st.columns([1, 1])

#     with col_menu:
#         st.subheader(t("📖 Menú", "📖 Menu"))
#         if view == t("Tabla", "Table"):
#             menu_table_component(menu, lang)
#         else:
#             gallery = fetch_menu_images()
#             if not gallery:
#                 st.info(t("No hay imágenes cargadas aún.",
#                         "No images uploaded yet."))
#             else:
#                 # menu_gallery_component(menu, lang, images=gallery, columns=2)
#                 # carousel(gallery, key_prefix="client_menu",
#                 #          lang=lang, interval_sec=5)
#                 render_js_carousel(gallery, interval_ms=5000, aspect_ratio=16 /
#                                    6, key_prefix="client_menu", show_dots=True, height_px=420)

#     with col_chat:
#         st.subheader("💬 Chat")
#         for m in st.session_state.conv:
#             klass = "user-bubble" if m["role"] == "user" else "bot-bubble"
#             with st.chat_message(m["role"]):
#                 st.markdown(f'<div class="{klass}">{
#                             m["content"]}</div>', unsafe_allow_html=True)

#         user_msg = st.chat_input(
#             t("Escribe tu mensaje…", "Type your message…"))

#         rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
#         media_constraints = {"audio": True, "video": False}
#         webrtc_ctx = webrtc_streamer(
#             key="client-ptt",
#             mode=WebRtcMode.SENDONLY,
#             rtc_configuration=rtc_cfg,
#             media_stream_constraints=media_constraints,
#             audio_receiver_size=256,
#             async_processing=True,
#         )

#         if "audio_buffer" not in st.session_state:
#             st.session_state.audio_buffer = []

#         class AudioProcessor:
#             def recv(self, frame: av.AudioFrame):
#                 pcm = frame.to_ndarray()
#                 st.session_state.audio_buffer.append(pcm)
#                 return frame

#         if webrtc_ctx and webrtc_ctx.state.playing:
#             webrtc_ctx.audio_processor = AudioProcessor()

#         if st.button(t("🎙️ Usar último audio", "🎙️ Use last audio")) and st.session_state.audio_buffer:
#             wav_bytes = np.concatenate(
#                 st.session_state.audio_buffer, axis=1).tobytes()
#             st.session_state.audio_buffer = []
#             text = client_voice_to_text(wav_bytes, cfg)
#             if text:
#                 user_msg = (user_msg + " " if user_msg else "") + text

#         if user_msg:
#             st.session_state.conv.append({"role": "user", "content": user_msg})
#             reply = client_assistant_reply(
#                 st.session_state.conv, menu, cfg, conversation_id=st.session_state.conv_id)
#             st.session_state.conv.append(
#                 {"role": "assistant", "content": reply})

#             info = extract_client_info(st.session_state.conv, lang)
#             st.session_state.client_info.update(
#                 {k: v for k, v in info.items() if v})
#             st.session_state.order_items = parse_items_from_chat(
#                 st.session_state.conv, menu, cfg)

#             # Nueva lógica: si falta info, preguntar explícitamente el siguiente campo
#             missing = ensure_all_required_present(
#                 st.session_state.client_info, lang)
#             if missing:
#                 next_field = missing[0]
#                 q_map_es = {
#                     "name": "¿Cuál es tu nombre?",
#                     "phone": "¿Cuál es tu número de teléfono?",
#                     "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
#                     "address": "¿Cuál es la dirección para la entrega?",
#                     "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
#                     "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
#                 }
#                 q_map_en = {
#                     "name": "What is your name?",
#                     "phone": "What is your phone number?",
#                     "delivery_type": "Pickup or delivery?",
#                     "address": "What is the delivery address?",
#                     "pickup_eta_min": "In how many minutes would you pick up?",
#                     "payment_method": "What is your payment method (cash, card, online)?",
#                 }
#                 qmap = q_map_es if lang == "es" else q_map_en
#                 st.session_state.conv.append(
#                     {"role": "assistant", "content": qmap[next_field]})

#             st.rerun()

#     st.write("---")
#     missing = ensure_all_required_present(
#         st.session_state.get("client_info", {}), lang)
#     label_map_es = {"name": "nombre", "phone": "teléfono", "delivery_type": "tipo de entrega",
#                     "payment_method": "método de pago", "address": "dirección", "pickup_eta_min": "tiempo de retiro (min)"}
#     label_map_en = {"name": "name", "phone": "phone", "delivery_type": "delivery type",
#                     "payment_method": "payment method", "address": "address", "pickup_eta_min": "pickup ETA (min)"}
#     lm = label_map_es if lang == "es" else label_map_en
#     miss_str = ", ".join([lm[m] for m in missing])

#     left, right = st.columns([2, 1])
#     with left:
#         if missing:
#             st.warning((f"Faltan datos para confirmar: {
#                        miss_str}." if lang == "es" else f"Missing fields: {miss_str}."))
#         else:
#             st.success(t("Tenemos todos los datos. Puedes confirmar.",
#                        "All data present. You can confirm."))
#             if st.session_state.get("order_items"):
#                 st.caption(t("Items detectados: ", "Detected items: ") + "; ".join(
#                     [f"{i['name']} x{i['qty']}" for i in st.session_state["order_items"]]))

#     with right:
#         if st.button(t("✅ Confirmar pedido", "✅ Confirm order")):
#             if missing:
#                 st.error((f"No se puede confirmar. Falta: {
#                          miss_str}" if lang == "es" else f"Cannot confirm. Missing: {miss_str}"))
#             else:
#                 order = create_order_from_chat_ready(
#                     client=st.session_state.get("client_info", {}),
#                     items=st.session_state.get("order_items", []),
#                     currency=currency,
#                 )
#                 st.session_state.conv.append({"role": "assistant", "content": t(
#                     "Pedido confirmado. ¡Lo estamos preparando! 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
#                     "Order confirmed. We’re on it! 🚗💨 for delivery, or ready at your pickup time."
#                 )})
#                 st.success(t("¡Pedido confirmado!", "Order confirmed!"))
#                 st.rerun()


# if __name__ == "__main__":
#     main()

from __future__ import annotations
import streamlit as st
from uuid import uuid4
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np

from backend.utils import render_js_carousel, menu_table_component
from backend.config import get_config
from backend.db import (
    fetch_menu, fetch_menu_banners, create_order_from_chat_ready,
    fetch_menu_images
)
from backend.llm_chat import (
    client_assistant_reply, extract_client_info, ensure_all_required_present,
    parse_items_from_chat, client_voice_to_text
)

# ──────────────────────────────────────────────────────────────────────────────
# Config de página
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

# CSS para layout tipo WhatsApp (chat sin título + input fijo abajo)
st.markdown("""
<style>
/* Caja de chat con scroll interno */
.chat-box {
  border: 1px solid #eee; border-radius: 12px;
  padding: 10px 12px; height: 52vh; overflow-y: auto;
  background: #fafafa;
  display: flex; flex-direction: column; gap: 6px;
}
/* Burbujas estilo WhatsApp */
.msg-user { 
  align-self: flex-end;
  background:#DCF8C6; color:#222; padding:10px 12px; 
  border-radius:14px; margin:2px 0; max-width:88%;
}
.msg-bot  { 
  align-self: flex-start;
  background:#ffffff; color:#222; padding:10px 12px; 
  border-radius:14px; margin:2px 0; max-width:88%; border:1px solid #eee; 
}
/* Pie con input */
.input-row { position: sticky; bottom: 0; background: #fff; padding-top: 8px; }
@media (max-width: 768px){
  .chat-box { height: 54vh; }
}
</style>
""", unsafe_allow_html=True)


def _t(lang: str):
    return (lambda es, en: es if lang == "es" else en)


def main():
    # Config y estado base
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    currency = cfg.get("currency", "USD")

    st.title(t("💬 Cliente", "💬 Client"))

    # Carga de menú
    menu = fetch_menu()
    if not menu:
        st.warning(t("El restaurante aún no ha cargado su menú.",
                     "The restaurant has not uploaded its menu yet."))
        return

    # Estado de conversación
    if "conv_id" not in st.session_state:
        st.session_state.conv_id = uuid4().hex
    if "conv" not in st.session_state:
        st.session_state.conv = [{
            "role": "assistant",
            "content": t(
                "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
                "Thanks for contacting us. How can we help?"
            )
        }]
    if "client_info" not in st.session_state:
        st.session_state.client_info = {}
    if "order_items" not in st.session_state:
        st.session_state.order_items = []
    if "pending_user_input" not in st.session_state:
        st.session_state.pending_user_input = ""

    # Visualización: tabla o imágenes
    view = st.radio(
        t("Visualización del menú", "Menu view"),
        [t("Tabla", "Table"), t("Imágenes", "Images")],
        horizontal=True
    )

    col_menu, col_chat = st.columns([1, 1])

    # ──────────────────────────────────────────────────────────────────────────
    # Columna izquierda: Menú (Tabla o Carrusel de Imágenes)
    # ──────────────────────────────────────────────────────────────────────────
    with col_menu:
        st.subheader(t("📖 Menú", "📖 Menu"))
        if view == t("Tabla", "Table"):
            menu_table_component(menu, lang)
        else:
            gallery = fetch_menu_images()
            if not gallery:
                st.info(t("No hay imágenes cargadas aún.",
                        "No images uploaded yet."))
            else:
                # Carrusel más alto en móvil/escritorio
                render_js_carousel(
                    gallery,
                    interval_ms=5000,
                    aspect_ratio=16/7,
                    key_prefix="client_menu",
                    show_dots=True,
                    height_px=420
                )

    # ──────────────────────────────────────────────────────────────────────────
    # Columna derecha: Chat tipo WhatsApp (sin título) + input fijo abajo
    # ──────────────────────────────────────────────────────────────────────────
    with col_chat:
        # Caja con scroll donde se pintan las burbujas
        st.markdown('<div class="chat-box" id="chatBox">',
                    unsafe_allow_html=True)
        for m in st.session_state.conv:
            klass = "msg-user" if m["role"] == "user" else "msg-bot"
            st.markdown(f'<div class="{klass}">{
                        m["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # WebRTC: captura de audio en background
        rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        media_constraints = {"audio": True, "video": False}
        webrtc_ctx = webrtc_streamer(
            key="client-ptt",
            mode=WebRtcMode.SENDONLY,
            rtc_configuration=rtc_cfg,
            media_stream_constraints=media_constraints,
            audio_receiver_size=256,
            async_processing=True,
        )

        if "audio_buffer" not in st.session_state:
            st.session_state.audio_buffer = []

        class AudioProcessor:
            def recv(self, frame: av.AudioFrame):
                pcm = frame.to_ndarray()
                st.session_state.audio_buffer.append(pcm)
                return frame

        if webrtc_ctx and webrtc_ctx.state.playing:
            webrtc_ctx.audio_processor = AudioProcessor()

        # Fila de input + botones (texto, Enviar, Confirmar, 🎙️)
        st.markdown('<div class="input-row">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([7, 1.5, 2, 1.5])

        user_text = c1.text_input(
            "",
            value=st.session_state.get("pending_user_input", ""),
            key="client_input",
            placeholder=t("Escribe tu mensaje…", "Type your message…"),
            label_visibility="collapsed"
        )

        send_clicked = c2.button(t("Enviar", "Send"), use_container_width=True)
        confirm_clicked = c3.button(
            t("Confirmar", "Confirm"), use_container_width=True)
        mic_clicked = c4.button("🎙️", use_container_width=True)

        # Botón 🎙️: transcribe el último audio acumulado y lo inyecta al input
        if mic_clicked and st.session_state.audio_buffer:
            wav_bytes = np.concatenate(
                st.session_state.audio_buffer, axis=1).tobytes()
            st.session_state.audio_buffer = []
            text = client_voice_to_text(wav_bytes, cfg)
            if text:
                # concatena al input existente
                cur = st.session_state.get("pending_user_input", "")
                st.session_state.pending_user_input = (
                    cur + " " + text).strip()
                st.rerun()

        # Enviar mensaje al LLM
        if send_clicked and user_text.strip():
            st.session_state.conv.append(
                {"role": "user", "content": user_text.strip()})
            st.session_state.pending_user_input = ""

            reply = client_assistant_reply(
                st.session_state.conv, menu, cfg, conversation_id=st.session_state.conv_id
            )
            st.session_state.conv.append(
                {"role": "assistant", "content": reply})

            # Extraer datos del cliente + items
            info = extract_client_info(st.session_state.conv, lang)
            st.session_state.client_info.update(
                {k: v for k, v in info.items() if v})
            st.session_state.order_items = parse_items_from_chat(
                st.session_state.conv, menu, cfg
            )

            # Si falta info, preguntar explícitamente el siguiente campo
            missing = ensure_all_required_present(
                st.session_state.client_info, lang)
            if missing:
                next_field = missing[0]
                q_map_es = {
                    "name": "¿Cuál es tu nombre?",
                    "phone": "¿Cuál es tu número de teléfono?",
                    "delivery_type": "¿Será para recoger (pickup) o entrega a domicilio?",
                    "address": "¿Cuál es la dirección para la entrega?",
                    "pickup_eta_min": "¿En cuántos minutos pasarías a recoger?",
                    "payment_method": "¿Cuál es tu método de pago (efectivo, tarjeta u online)?",
                }
                q_map_en = {
                    "name": "What is your name?",
                    "phone": "What is your phone number?",
                    "delivery_type": "Pickup or delivery?",
                    "address": "What is the delivery address?",
                    "pickup_eta_min": "In how many minutes would you pick up?",
                    "payment_method": "What is your payment method (cash, card, online)?",
                }
                qmap = q_map_es if lang == "es" else q_map_en
                st.session_state.conv.append(
                    {"role": "assistant", "content": qmap[next_field]})

            st.rerun()

        # Confirmar pedido (validación estricta)
        if confirm_clicked:
            missing = ensure_all_required_present(
                st.session_state.get("client_info", {}), lang)
            label_map_es = {"name": "nombre", "phone": "teléfono", "delivery_type": "tipo de entrega",
                            "payment_method": "método de pago", "address": "dirección", "pickup_eta_min": "tiempo de retiro (min)"}
            label_map_en = {"name": "name", "phone": "phone", "delivery_type": "delivery type",
                            "payment_method": "payment method", "address": "address", "pickup_eta_min": "pickup ETA (min)"}
            lm = label_map_es if lang == "es" else label_map_en
            miss_str = ", ".join([lm[m] for m in missing])

            if missing:
                st.error(t(f"No se puede confirmar. Falta: {miss_str}",
                           f"Cannot confirm. Missing: {miss_str}"))
            else:
                order = create_order_from_chat_ready(
                    client=st.session_state.get("client_info", {}),
                    items=st.session_state.get("order_items", []),
                    currency=currency,
                )
                st.session_state.conv.append({"role": "assistant", "content": t(
                    "Pedido confirmado. ¡Lo estamos preparando! 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
                    "Order confirmed. We’re on it! 🚗💨 for delivery, or ready at your pickup time."
                )})
                st.success(t("¡Pedido confirmado!", "Order confirmed!"))
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # cierre input-row

    # ──────────────────────────────────────────────────────────────────────────
    # Aviso de campos faltantes + items detectados (bajo el chat)
    # ──────────────────────────────────────────────────────────────────────────
    st.write("---")
    missing = ensure_all_required_present(
        st.session_state.get("client_info", {}), lang)
    label_map_es = {"name": "nombre", "phone": "teléfono", "delivery_type": "tipo de entrega",
                    "payment_method": "método de pago", "address": "dirección", "pickup_eta_min": "tiempo de retiro (min)"}
    label_map_en = {"name": "name", "phone": "phone", "delivery_type": "delivery type",
                    "payment_method": "payment method", "address": "address", "pickup_eta_min": "pickup ETA (min)"}
    lm = label_map_es if lang == "es" else label_map_en
    miss_str = ", ".join([lm[m] for m in missing])

    left, right = st.columns([2, 1])
    with left:
        if missing:
            st.warning(t(f"Faltan datos para confirmar: {miss_str}.",
                         f"Missing fields: {miss_str}."))
        else:
            st.success(t("Tenemos todos los datos. Puedes confirmar.",
                         "All data present. You can confirm."))
            if st.session_state.get("order_items"):
                st.caption(t("Ítems detectados: ", "Detected items: ") + "; ".join(
                    [f"{i['name']} x{i['qty']}" for i in st.session_state["order_items"]]
                ))

    with right:
        # Botón redundante (por comodidad) para confirmar también desde aquí
        if st.button(t("✅ Confirmar pedido", "✅ Confirm order"), use_container_width=True):
            if missing:
                st.error(t(f"No se puede confirmar. Falta: {miss_str}",
                           f"Cannot confirm. Missing: {miss_str}"))
            else:
                order = create_order_from_chat_ready(
                    client=st.session_state.get("client_info", {}),
                    items=st.session_state.get("order_items", []),
                    currency=currency,
                )
                st.session_state.conv.append({"role": "assistant", "content": t(
                    "Pedido confirmado. ¡Lo estamos preparando! 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
                    "Order confirmed. We’re on it! 🚗💨 for delivery, or ready at your pickup time."
                )})
                st.success(t("¡Pedido confirmado!", "Order confirmed!"))
                st.rerun()


if __name__ == "__main__":
    main()
