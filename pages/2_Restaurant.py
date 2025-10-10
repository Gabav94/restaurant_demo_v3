# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:16:39 2025

@author: geam9
"""

from __future__ import annotations
import io
import csv
import pandas as pd
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import numpy as np
import time
from backend.utils import render_js_carousel
from backend.config import get_config
from backend.db import (
    add_menu_item, fetch_menu, delete_menu_item, add_menu_image, fetch_menu_images,
    fetch_orders_queue, update_order_status, bump_priorities_if_sla_missed,
    fetch_pending_questions, answer_pending_question, autoapprove_expired_pendings,
    export_orders_csv, export_pendings_csv
)
from backend.utils import menu_table_component, menu_gallery_component
from backend import ocr as ocr_mod  # backend/ocr.py

st.set_page_config(page_title="Restaurante", page_icon="🧑‍🍳", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){ .block-container{padding-top:1rem;padding-bottom:3rem;} }
</style>
""", unsafe_allow_html=True)


def _t(lang):
    return (lambda es, en: es if lang == "es" else en)


def _safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def _parse_csv_or_txt(file) -> list[dict]:
    content = file.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(content.splitlines(
        )[0]) if content else csv.get_dialect("excel")
    except Exception:
        dialect = csv.get_dialect("excel")
    reader = csv.DictReader(io.StringIO(content), dialect=dialect)
    items = []
    for r in reader:
        items.append({
            "name": r.get("name", "").strip(),
            "description": r.get("description", "").strip(),
            "price": _safe_float(r.get("price", "0")),
            "special_notes": r.get("special_notes", "").strip(),
        })
    return items


def _rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def carousel(images: list[str], key_prefix: str, lang: str, interval_sec: int = 5):
    if "carousel_state" not in st.session_state:
        st.session_state.carousel_state = {}
    state = st.session_state.carousel_state.setdefault(
        key_prefix, {"idx": 0, "on": True})

    # Toggle y avance
    colA, colB = st.columns([1, 3])
    with colA:
        state["on"] = st.toggle(
            "⏯️ Auto", value=state["on"], key=f"{key_prefix}_auto")
    with colB:
        st.caption("Avanza cada 5s" if lang == "es" else "Advances every 5s")

    if images:
        from backend.utils import _image  # usa tu helper
        _image(images[state["idx"]])

        # Controles manuales
        c1, c2, c3 = st.columns(3)
        if c1.button("⏮️", key=f"{key_prefix}_prev"):
            state["idx"] = (state["idx"]-1) % len(images)
            st.rerun()
        if c3.button("⏭️", key=f"{key_prefix}_next"):
            state["idx"] = (state["idx"]+1) % len(images)
            st.rerun()

        # Autoavance simple por refresh
        if state["on"]:
            # Inyecta refresh a los 5s SIN tocar toda la app (solo recarga la página)
            st.markdown(
                f"<meta http-equiv='refresh' content='{interval_sec}'>",
                unsafe_allow_html=True
            )
            # al volver a correr, avanzamos índice
            state["idx"] = (state["idx"]+1) % len(images)


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
            notes = st.text_input(t("Notas especiales (etiquetas)", "Special notes (tags)"), placeholder=t(
                "vegetariano, sin gluten, picante…", "vegetarian, gluten-free, spicy…"))
            if st.form_submit_button(t("Agregar", "Add")):
                if name.strip():
                    add_menu_item(name, desc, price, cfg.get(
                        "currency", "USD"), notes)
                    st.success(t("Ítem agregado", "Item added"))
                else:
                    st.error(t("El nombre es obligatorio", "Name is required"))

    with col2:
        st.subheader(t("Carga masiva (CSV/TXT) + OCR",
                     "Bulk upload (CSV/TXT) + OCR"))
        up = st.file_uploader(
            t("Subir CSV/TXT", "Upload CSV/TXT"), type=["csv", "txt"], label_visibility="visible")
        if st.button(t("Procesar archivo", "Process file")) and up:
            try:
                items = _parse_csv_or_txt(up)
                current = {m["name"] for m in fetch_menu()}
                added = 0
                for it in items:
                    if it["name"] and it["name"] not in current:
                        add_menu_item(it["name"], it["description"], it["price"], cfg.get(
                            "currency", "USD"), it["special_notes"])
                        added += 1
                st.success(t(f"Agregados: {added}", "Added: ") + str(added))
                _rerun()
            except Exception as e:
                st.error(t("No se pudo procesar el archivo",
                         "Failed to process file") + f": {e}")

        img = st.file_uploader(t("Subir imagen (OCR)", "Upload image (OCR)"), type=[
                               "png", "jpg", "jpeg"])
        if st.button(t("Leer con OCR", "Read with OCR")) and img:
            try:
                # [{name, description, price, special_notes}]
                rows = ocr_mod.parse_menu_image(img, lang=lang)
                current = {m["name"] for m in fetch_menu()}
                added = 0
                for it in rows:
                    if it["name"] and it["name"] not in current:
                        add_menu_item(it["name"], it["description"], it["price"], cfg.get(
                            "currency", "USD"), it.get("special_notes", ""))
                        added += 1
                st.success(t(f"Agregados vía OCR: {
                           added}", "Added via OCR: ") + str(added))
                _rerun()
            except Exception as e:
                st.error(t("OCR falló", "OCR failed") + f": {e}")

        st.caption(t("Imágenes del menú (galería)", "Menu images (gallery)"))
        img_up = st.file_uploader(t("Subir imagen del menú", "Upload menu image"), type=[
                                  "png", "jpg", "jpeg"], key="menu_img")
        if st.button(t("Guardar imagen", "Save image")) and img_up:
            add_menu_image(img_up)
            st.success("OK")
            _rerun()

    st.write("---")
    view = st.radio(t("Visualización del menú", "Menu view"), [t("Tabla", "Table"), t(
        "Imágenes", "Images")], horizontal=True, key="menu_view_admin")
    menu = fetch_menu()
    if view == t("Tabla", "Table"):
        menu_table_component(menu, lang, deletable=True,
                             on_delete=delete_menu_item)
    else:
        gallery = fetch_menu_images()
        if not gallery:
            st.info(t("No hay imágenes cargadas aún.", "No images uploaded yet."))
        else:
            # menu_gallery_component(menu, lang, images=gallery, columns=2)
            # carousel(gallery, key_prefix="rest_menu",
            #          lang=lang, interval_sec=5)
            render_js_carousel(gallery, interval_ms=5000, aspect_ratio=16 /
                               6, key_prefix="client_menu", show_dots=True)

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
                    _rerun()

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
                        _rerun()
                with colB:
                    if st.button(t("Negar", "Deny"), key="dn_"+p["id"]):
                        answer_pending_question(p["id"], "denied", t(
                            "No disponible.", "Not available."))
                        st.success("OK")
                        _rerun()
                with colC:
                    msg = st.text_input(
                        t("Mensaje al cliente (opcional)", "Message to client (optional)"), key="msg_"+p["id"])
                    if st.button(t("Responder con mensaje", "Reply with message"), key="rm_"+p["id"]):
                        answer_pending_question(
                            p["id"], "custom", msg or t("Aprobado.", "Approved."))
                        st.success("OK")
                        _rerun()

            st.download_button(
                label=t("⬇️ Descargar interacciones (CSV)",
                        "⬇️ Download pendings (CSV)"),
                data=export_pendings_csv(), file_name="pendings.csv", mime="text/csv"
            )

    st.write("---")
    st.subheader(t("Micrófono (comandos de voz)",
                 "Microphone (voice commands)"))

    rtc_cfg = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    media_constraints = {"audio": True, "video": False}

    webrtc_ctx = webrtc_streamer(
        key="admin-ptt",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=rtc_cfg,
        media_stream_constraints=media_constraints,
        audio_receiver_size=256,
        async_processing=True,
    )

    if "admin_audio_buffer" not in st.session_state:
        st.session_state.admin_audio_buffer = []

    class AdminAudioProcessor:
        def recv(self, frame: av.AudioFrame):
            st.session_state.admin_audio_buffer.append(frame.to_ndarray())
            return frame

    if webrtc_ctx and webrtc_ctx.state.playing:
        webrtc_ctx.audio_processor = AdminAudioProcessor()

    if st.button(t("🎙️ Usar último audio (comando)", "🎙️ Use last audio (command)")) and st.session_state.admin_audio_buffer:
        from backend.llm_chat import admin_voice_command
        pcm = np.concatenate(
            st.session_state.admin_audio_buffer, axis=1).tobytes()
        st.session_state.admin_audio_buffer = []
        cfg = get_config()
        resp = admin_voice_command(pcm, cfg, lang=lang)
        st.info(resp)


if __name__ == "__main__":
    main()
