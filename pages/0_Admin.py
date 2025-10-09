# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:14:54 2025

@author: geam9
"""

from __future__ import annotations
import os
import streamlit as st
from backend.config import get_config, update_config, reset_config
from backend.db import (
    clear_orders, clear_pendings, clear_menu, clear_menu_images, clear_banners,
    reset_everything, ensure_db_and_seed, fetch_menu_banners
)
from backend.faq import clear_faq

st.set_page_config(page_title="Admin (Super)", page_icon="⚙️", layout="wide")


def _t(lang):
    return (lambda es, en: es if lang == "es" else en)


def _image_compat(img):
    try:
        st.image(img, use_container_width=True)
    except TypeError:
        st.image(img, use_column_width=True)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    st.title("⚙️ Admin")

    st.subheader(t("Configuración general", "General settings"))
    col1, col2 = st.columns(2)
    with col1:
        new_lang = st.selectbox("Idioma / Language",
                                ["es", "en"], index=0 if lang == "es" else 1)
        model = st.text_input(t("Modelo LLM", "LLM Model"),
                              value=cfg.get("model", "gpt-4o-mini"))
        temperature = st.slider(t("Temperatura", "Temperature"), 0.0, 1.0, float(
            cfg.get("temperature", 0.4)), 0.1)
        assistant_name = st.text_input(t("Nombre del asistente", "Assistant name"), value=cfg.get(
            "assistant_name", "Asistente" if lang == "es" else "Assistant"))
        tone_ph = ("Amable y profesional; breve, guiado." if lang ==
                   "es" else "Friendly and professional; concise, guided.")
        tone = st.text_area(t("Tono de la conversación", "Conversation tone"), value=cfg.get(
            "tone", tone_ph), placeholder=tone_ph)
        currency = st.text_input(
            t("Moneda (ej. USD)", "Currency (e.g., USD)"), value=cfg.get("currency", "USD"))

        if st.button(t("Guardar configuración", "Save settings")):
            update_config({
                "language": new_lang,
                "model": model,
                "temperature": float(temperature),
                "assistant_name": assistant_name,
                "tone": tone,
                "currency": currency,
            })
            st.success(t("Configuración guardada. Recarga la app si cambiaste idioma.",
                       "Settings saved. Reload app if you changed language."))

    with col2:
        st.markdown(t("**Banners del menú**", "**Menu banners**"))
        banners = fetch_menu_banners()
        if banners:
            _image_compat(banners[0])
        st.caption(t("Los banners por defecto se generan automáticamente en el primer arranque.",
                   "Default banners are auto-created on first run."))

    st.write("---")
    st.subheader(t("Limpieza de datos (uso con cuidado)",
                 "Data cleanup (use with care)"))
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(t("🧹 Limpiar órdenes", "🧹 Clear orders")):
            clear_orders()
            st.success("OK")
        if st.button(t("🧹 Limpiar interacciones difíciles", "🧹 Clear pendings")):
            clear_pendings()
            st.success("OK")
        if st.button(t("🧹 Limpiar FAQ", "🧹 Clear FAQ")):
            clear_faq()
            st.success("OK")
    with c2:
        if st.button(t("🧹 Limpiar menú (ítems)", "🧹 Clear menu items")):
            clear_menu()
            st.success("OK")
        if st.button(t("🧹 Limpiar imágenes del menú", "🧹 Clear menu images")):
            clear_menu_images()
            st.success("OK")
        if st.button(t("🧹 Limpiar banners", "🧹 Clear banners")):
            clear_banners()
            st.success("OK")
    with c3:
        if st.button(t("🧨 Reset total (todo)", "🧨 Full reset (all)")):
            reset_everything()
            st.success("OK; vuelve a cargar para reseed")
            ensure_db_and_seed()

    st.write("---")
    st.subheader(t("Config por defecto", "Default config"))
    if st.button(t("🔁 Restaurar config por defecto", "🔁 Restore default config")):
        reset_config()
        st.success("OK")


if __name__ == "__main__":
    main()
