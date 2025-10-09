# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:32 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from uuid import uuid4
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np

from backend.config import get_config
from backend.db import (
    fetch_menu, fetch_menu_images, create_order_from_chat_ready
)
from backend.llm_chat import (
    client_assistant_reply, extract_client_info, ensure_all_required_present,
    parse_items_from_chat, client_voice_to_text
)
from backend.utils import (
    menu_table_component, menu_gallery_component, render_auto_carousel
)

st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){
  .block-container{padding-top:0.5rem;padding-bottom:3rem;}
}
.sticky-menu { position: sticky; top: 0; z-index: 9; background: white; padding: .4rem 0 .6rem 0; border-bottom: 1px solid #eee; }
.carousel-wrap { margin-bottom: .5rem; }
.chat-wrap { height: 74vh; max-height: 760px; overflow-y: auto; padding: .5rem .25rem; border-radius: 12px; border: 1px solid #eee; background: #fafafa; }
.user-bubble .stMarkdown p{background:#DCF8C6; padding:.6rem .8rem; border-radius:1rem;}
.bot-bubble .stMarkdown p{background:#FFFFFF; padding:.6rem .8rem; border-radius:1rem; border:1px solid #eee;}
</style>
""", unsafe_allow_html=True)


def _t(lang):
    return (lambda es, en: es if lang == "es" else en)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    currency = cfg.get("currency", "USD")

    st.title(t("💬 Cliente", "💬 Client"))

    # ---- Carrusel SOLO con imágenes subidas por el restaurante ----
    real_menu_imgs = fetch_menu_images()
    with st.container():
        st.markdown('<div class="carousel-wrap">', unsafe_allow_html=True)
        if real_menu_imgs:
            render_auto_carousel(real_menu_imgs, height_px=180, interval_sec=4)
        else:
            st.info(t("El restaurante aún no ha cargado imágenes de su menú.",
                    "The restaurant has not uploaded menu images yet."))
        st.markdown('</div>', unsafe_allow_html=True)

    menu = fetch_menu()
    if not menu:
        st.warning(t("El restaurante aún no ha cargado su menú.",
                   "The restaurant has not uploaded its menu yet."))
        return

    if "conv_id" not in st.session_state:
        st.session_state.conv_id = uuid4().hex
    if "conv" not in st.session_state:
        st.session_state.conv = [{"role": "assistant", "content": t(
            "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
            "Thanks for contacting us. How can we help?"
        )}]
    if "client_info" not in st.session_state:
        st.session_state.client_info = {}
    if "order_items" not in st.session_state:
        st.session_state.order_items = []

    # ---- Menú sticky (arriba) ----
    with st.container():
        st.markdown('<div class="sticky-menu">', unsafe_allow_html=True)
        view = st.radio(t("Visualización del menú", "Menu view"), [
                        t("Tabla", "Table"), t("Imágenes", "Images")], horizontal=True)
        if view == t("Tabla", "Table"):
            menu_table_component(menu, lang)
        else:
            menu_gallery_component(menu, lang, images=None, columns=3)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----- Chat fijo + mic -----
    st.subheader("💬 Chat")
    with st.container():
        st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
        for m in st.session_state.conv:
            klass = "user-bubble" if m["role"] == "user" else "bot-bubble"
            with st.chat_message(m["role"]):
                st.markdown(f'<div class="{klass}">{
                            m["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    media_constraints = {"audio": True, "video": False}

    class AudioProcessor:
        def __init__(self) -> None:
            self._buf = []

        def recv(self, frame: av.AudioFrame):
            self._buf.append(frame.to_ndarray())
            return frame

        def pop(self):
            if not self._buf:
                return None
            import numpy as np
            pcm = np.concatenate(self._buf, axis=1).tobytes()
            self._buf = []
            return pcm

    webrtc_ctx = webrtc_streamer(
        key="client-ptt",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=rtc_cfg,
        media_stream_constraints=media_constraints,
        audio_receiver_size=256,
        async_processing=True,
        audio_processor_factory=AudioProcessor,
    )

    cols = st.columns([1, 1])
    with cols[0]:
        use_audio = st.button(t("🎙️ Usar último audio", "🎙️ Use last audio"))
    with cols[1]:
        user_msg = st.chat_input(
            t("Escribe tu mensaje…", "Type your message…"))

    if use_audio and webrtc_ctx and webrtc_ctx.audio_processor:
        pcm = webrtc_ctx.audio_processor.pop()
        if pcm:
            text = client_voice_to_text(pcm, cfg)
            if text:
                user_msg = (user_msg + " " if user_msg else "") + text

    if user_msg:
        st.session_state.conv.append({"role": "user", "content": user_msg})
        reply = client_assistant_reply(
            st.session_state.conv, menu, cfg, conversation_id=st.session_state.conv_id)
        st.session_state.conv.append({"role": "assistant", "content": reply})
        # extracción robusta de datos e ítems
        info = extract_client_info(st.session_state.conv, lang)
        st.session_state.client_info.update(
            {k: v for k, v in info.items() if v})
        st.session_state.order_items = parse_items_from_chat(
            st.session_state.conv, menu, cfg)
        st.rerun()

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
            st.warning((f"Faltan datos para confirmar: {
                       miss_str}." if lang == "es" else f"Missing fields: {miss_str}."))
        else:
            st.success(t("Tenemos todos los datos. Puedes confirmar.",
                       "All data present. You can confirm."))
            if st.session_state.get("order_items"):
                st.caption(t("Items detectados: ", "Detected items: ") + "; ".join(
                    [f"{i['name']} x{i['qty']}" for i in st.session_state["order_items"]]))

    with right:
        if st.button(t("✅ Confirmar pedido", "✅ Confirm order")):
            if missing:
                st.error((f"No se puede confirmar. Falta: {
                         miss_str}" if lang == "es" else f"Cannot confirm. Missing: {miss_str}"))
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
