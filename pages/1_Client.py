# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:32 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from uuid import uuid4
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av, numpy as np

from backend.config import get_config
from backend.db import fetch_menu, fetch_menu_banners, create_order_from_chat_ready
from backend.llm_chat import (
    client_assistant_reply, extract_client_info, ensure_all_required_present,
    parse_items_from_chat, client_voice_to_text
)
from backend.utils import menu_table_component, menu_gallery_component

st.set_page_config(page_title="Cliente", page_icon="💬", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){
  .block-container{padding-top:1rem;padding-bottom:3rem;}
}
.stChatMessage[data-testid="stChatMessage"] { max-width: 740px; }
.user-bubble .stMarkdown p{background:#DCF8C6; padding:.6rem .8rem; border-radius:1rem;}
.bot-bubble .stMarkdown p{background:#FFFFFF; padding:.6rem .8rem; border-radius:1rem; border:1px solid #eee;}
</style>
""", unsafe_allow_html=True)

def _t(lang): 
    return (lambda es,en: es if lang=="es" else en)

def _image_compat(img):
    try:
        st.image(img, use_container_width=True)
    except TypeError:
        st.image(img, use_column_width=True)

def main():
    cfg = get_config()
    lang = cfg.get("language","es"); t = _t(lang)
    currency = cfg.get("currency","USD")

    st.title(t("💬 Cliente","💬 Client"))

    banners = fetch_menu_banners()
    if banners:
        _image_compat(banners[0])

    menu = fetch_menu()
    if not menu:
        st.warning(t("El restaurante aún no ha cargado su menú.","The restaurant has not uploaded its menu yet."))
        return

    if "conv_id" not in st.session_state:
        st.session_state.conv_id = uuid4().hex
    if "conv" not in st.session_state:
        st.session_state.conv = [{"role":"assistant","content":t(
            "Gracias por comunicarte con nosotros. ¿Cómo podemos ayudarte?",
            "Thanks for contacting us. How can we help?"
        )}]
    if "client_info" not in st.session_state: st.session_state.client_info={}
    if "order_items" not in st.session_state: st.session_state.order_items=[]

    view = st.radio(t("Visualización del menú","Menu view"), [t("Tabla","Table"), t("Imágenes","Images")], horizontal=True)
    col_menu, col_chat = st.columns([1,1])

    with col_menu:
        st.subheader(t("📖 Menú","📖 Menu"))
        if view == t("Tabla","Table"):
            menu_table_component(menu, lang)
        else:
            menu_gallery_component(menu, lang)

    with col_chat:
        st.subheader("💬 Chat")
        for m in st.session_state.conv:
            klass = "user-bubble" if m["role"]=="user" else "bot-bubble"
            with st.chat_message(m["role"]):
                st.markdown(f'<div class="{klass}">{m["content"]}</div>', unsafe_allow_html=True)

        user_msg = st.chat_input(t("Escribe tu mensaje…","Type your message…"))

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

        if "audio_buffer" not in st.session_state: st.session_state.audio_buffer = []

        class AudioProcessor:
            def recv(self, frame: av.AudioFrame):
                pcm = frame.to_ndarray()
                st.session_state.audio_buffer.append(pcm)
                return frame

        if webrtc_ctx and webrtc_ctx.state.playing:
            webrtc_ctx.audio_processor = AudioProcessor()

        if st.button(t("🎙️ Usar último audio","🎙️ Use last audio")) and st.session_state.audio_buffer:
            wav_bytes = np.concatenate(st.session_state.audio_buffer, axis=1).tobytes()
            st.session_state.audio_buffer = []
            text = client_voice_to_text(wav_bytes, cfg)
            if text:
                user_msg = (user_msg + " " if user_msg else "") + text

        if user_msg:
            st.session_state.conv.append({"role":"user","content":user_msg})
            reply = client_assistant_reply(st.session_state.conv, menu, cfg, conversation_id=st.session_state.conv_id)
            st.session_state.conv.append({"role":"assistant","content":reply})

            info = extract_client_info(st.session_state.conv, lang)
            st.session_state.client_info.update({k:v for k,v in info.items() if v})
            st.session_state.order_items = parse_items_from_chat(st.session_state.conv, menu, cfg)
            st.rerun()

    st.write("---")
    missing = ensure_all_required_present(st.session_state.get("client_info",{}), lang)
    label_map_es = {"name":"nombre","phone":"teléfono","delivery_type":"tipo de entrega","payment_method":"método de pago","address":"dirección","pickup_eta_min":"tiempo de retiro (min)"}
    label_map_en = {"name":"name","phone":"phone","delivery_type":"delivery type","payment_method":"payment method","address":"address","pickup_eta_min":"pickup ETA (min)"}
    lm = label_map_es if lang=="es" else label_map_en
    miss_str = ", ".join([lm[m] for m in missing])

    left, right = st.columns([2,1])
    with left:
        if missing:
            st.warning((f"Faltan datos para confirmar: {miss_str}." if lang=="es" else f"Missing fields: {miss_str}."))
        else:
            st.success(t("Tenemos todos los datos. Puedes confirmar.","All data present. You can confirm."))
            if st.session_state.get("order_items"):
                st.caption(t("Items detectados: ","Detected items: ") + "; ".join([f"{i['name']} x{i['qty']}" for i in st.session_state["order_items"]]))

    with right:
        if st.button(t("✅ Confirmar pedido","✅ Confirm order")):
            if missing:
                st.error((f"No se puede confirmar. Falta: {miss_str}" if lang=="es" else f"Cannot confirm. Missing: {miss_str}"))
            else:
                order = create_order_from_chat_ready(
                    client=st.session_state.get("client_info", {}),
                    items=st.session_state.get("order_items", []),
                    currency=currency,
                )
                st.session_state.conv.append({"role":"assistant","content":t(
                    "Pedido confirmado. ¡Lo estamos preparando! 🚗💨 si es a domicilio, o listo según tu hora de retiro.",
                    "Order confirmed. We’re on it! 🚗💨 for delivery, or ready at your pickup time."
                )})
                st.success(t("¡Pedido confirmado!","Order confirmed!"))
                st.rerun()

if __name__ == "__main__":
    main()
