# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:16:39 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np

from backend.config import get_config
from backend.db import (
    add_menu_item, fetch_menu, delete_menu_item,
    add_menu_image, fetch_menu_images_full, delete_menu_image,
    fetch_orders_queue, update_order_status, bump_priorities_if_sla_missed,
    fetch_pending_questions, answer_pending_question, autoapprove_expired_pendings,
    export_orders_csv, export_pendings_csv
)
from backend.utils import menu_table_component, render_auto_carousel

st.set_page_config(page_title="Restaurante", page_icon="🧑‍🍳", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){ .block-container{padding-top:1rem;padding-bottom:3rem;} }
.card{
  border:1px solid #eee; border-radius:12px; padding:12px; background:#fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.imgbox{ display:flex; align-items:center; gap:8px; }
.imgbox img{ max-height:120px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)


def _t(lang):
    return (lambda es, en: es if lang == "es" else en)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    st.title(t("🧑‍🍳 Restaurante", "🧑‍🍳 Restaurant"))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t("Agregar ítem", "Add item"))
        with st.form("add_item"):
            name = st.text_input(t("Nombre", "Name"))
            desc = st.text_area(t("Descripción", "Description"))
            price = st.number_input(
                t("Precio", "Price"), min_value=0.0, value=0.0, step=0.1)
            notes = st.text_input(t("Notas especiales (etiquetas)", "Special notes (tags)"),
                                  placeholder=t("vegetariano, sin gluten, picante…", "vegetarian, gluten-free, spicy…"))
            if st.form_submit_button(t("Agregar", "Add")):
                if name.strip():
                    add_menu_item(name, desc, price, cfg.get(
                        "currency", "USD"), notes)
                    st.success(t("Ítem agregado", "Item added"))
                    st.rerun()
                else:
                    st.error(t("El nombre es obligatorio", "Name is required"))

    with col2:
        st.subheader(t("Imágenes del menú", "Menu images"))
        up = st.file_uploader(t("Subir imagen", "Upload image"), type=[
                              "png", "jpg", "jpeg"])
        if st.button(t("Guardar imagen", "Save image")) and up:
            add_menu_image(up)
            st.success("OK")
            st.rerun()

        rows = fetch_menu_images_full()
        if not rows:
            st.info(t("No hay imágenes aún.", "No images yet."))
        else:
            # Toggle para ver carrusel de vista previa
            preview_as_carousel = st.toggle(
                t("Ver como carrusel", "Preview as carousel"), value=True)
            if preview_as_carousel:
                render_auto_carousel(
                    [r["path"] for r in rows], height_px=180, interval_sec=4)

            st.markdown("### " + t("Galería (administrable)",
                        "Gallery (manageable)"))
            for r in rows:
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    cA, cB = st.columns([3, 1])
                    with cA:
                        st.markdown(f"<div class='imgbox'><img src='file://{r['path']}' /><div><b>ID:</b> {
                                    r['id']}<br/><b>Ruta:</b> {r['path']}</div></div>", unsafe_allow_html=True)
                    with cB:
                        if st.button(t("Eliminar", "Delete"), key=f"del_img_{r['id']}"):
                            if delete_menu_image(r["id"]):
                                st.success("OK")
                                st.rerun()
                            else:
                                st.error(
                                    t("No se pudo eliminar", "Failed to delete"))
                    st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    # Switch tabla / imágenes para el menú (en imágenes no se muestra texto de ítems)
    view = st.radio(t("Visualización del menú", "Menu view"), [
                    t("Tabla", "Table"), t("Imágenes", "Images")], horizontal=True)
    if view == t("Tabla", "Table"):
        menu = fetch_menu()
        menu_table_component(menu, lang, deletable=True,
                             on_delete=delete_menu_item)
    else:
        st.info(t("Vista Imágenes: arriba puedes subir, previsualizar y eliminar. Aquí no se listan ítems del menú.",
                  "Images view: above you can upload, preview and delete. Items are not listed here."))

    st.write("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader(t("Órdenes", "Orders"))
        bump_priorities_if_sla_missed()
        orders = fetch_orders_queue()
        if not orders:
            st.info(t("No hay órdenes aún.", "No orders yet."))
        else:
            df = pd.DataFrame([{
                "id": o["id"],
                t("creada", "created"): o["created_at"],
                t("cliente", "client"): o["client_name"],
                t("tipo", "type"): o["delivery_type"],
                t("total", "total"): f'{o["currency"]} {o["total"]:0.2f}',
                t("estado", "status"): o["status"],
                t("prioridad", "priority"): o["priority"],
                t("SLA", "SLA"): "⚠️" if o["sla_breached"] else "✅",
            } for o in orders])
            try:
                st.dataframe(df, hide_index=True, use_container_width=True)
            except TypeError:
                st.dataframe(df, hide_index=True)
            with st.expander(t("Cambiar estado", "Change status")):
                oid = st.selectbox(t("Orden", "Order"), [
                                   o["id"] for o in orders])
                newst = st.selectbox(t("Nuevo estado", "New status"), [
                                     "confirmed", "preparing", "ready", "delivered"])
                if st.button(t("Aplicar", "Apply")) and oid:
                    update_order_status(oid, newst)
                    st.success("OK")
                    st.rerun()
            st.download_button(
                label=t("⬇️ Descargar órdenes (CSV)",
                        "⬇️ Download orders (CSV)"),
                data=export_orders_csv(), file_name="orders.csv", mime="text/csv"
            )

    with c2:
        st.subheader(t("Interacciones por confirmar (1 min)",
                     "Pending interactions (1 min)"))
        autoapprove_expired_pendings()
        pend = fetch_pending_questions()
        if not pend:
            st.info(t("No hay interacciones pendientes.",
                    "No pending interactions."))
        else:
            for p in pend:
                st.markdown(f"**ID:** {p['id']}  \n**Pregunta:** {p['question']}  \n**Idioma:** {
                            p['language']}  \n**Expira:** {p['expires_at']}")
                colA, colB, colC = st.columns(3)
                with colA:
                    if st.button(t("Aprobar", "Approve"), key="ap_"+p["id"]):
                        answer_pending_question(p["id"], "approved", t(
                            "Aprobado por cocina.", "Approved by kitchen."))
                        st.success("OK")
                        st.rerun()
                with colB:
                    if st.button(t("Negar", "Deny"), key="dn_"+p["id"]):
                        answer_pending_question(p["id"], "denied", t(
                            "No disponible.", "Not available."))
                        st.success("OK")
                        st.rerun()
                with colC:
                    msg = st.text_input(
                        t("Mensaje al cliente (opcional)", "Message to client (optional)"), key="msg_"+p["id"])
                    if st.button(t("Responder con mensaje", "Reply with message"), key="rm_"+p["id"]):
                        answer_pending_question(
                            p["id"], "custom", msg or t("Aprobado.", "Approved."))
                        st.success("OK")
                        st.rerun()

    st.write("---")
    st.subheader(t("Micrófono (comandos de voz)",
                 "Microphone (voice commands)"))

    rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    media_constraints = {"audio": True, "video": False}

    class AdminAudioProcessor:
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
        key="admin-ptt",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=rtc_cfg,
        media_stream_constraints=media_constraints,
        audio_receiver_size=256,
        async_processing=True,
        audio_processor_factory=AdminAudioProcessor,
    )

    if st.button(t("🎙️ Usar último audio (comando)", "🎙️ Use last audio (command)")) and webrtc_ctx and webrtc_ctx.audio_processor:
        from backend.llm_chat import admin_voice_command
        pcm = webrtc_ctx.audio_processor.pop()
        if pcm:
            cfg = get_config()
            # <-- ya existe en llm_chat con este cambio
            resp = admin_voice_command(pcm, cfg, lang=lang)
            st.info(resp)


if __name__ == "__main__":
    main()
