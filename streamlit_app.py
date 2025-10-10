# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:36:48 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from backend.config import ensure_default_config, get_config, update_config
from backend.db import ensure_db_and_seed

ensure_db_and_seed()
ensure_default_config()

st.set_page_config(page_title="Restaurant AI Demo",
                   page_icon="🍽️", layout="wide")


def _image_compat(img):
    try:
        st.image(img, width='stretch')
    except TypeError:
        st.image(img, use_column_width=True)


def main():
    # Asegurar config y DB con seed
    # ensure_default_config()
    # ensure_db_and_seed()

    cfg = get_config()
    lang = cfg.get("language", "es")

    st.title("🍽️ Restaurant AI Demo v4")
    st.caption("Conversational Ordering • Streamlit • OpenAI • OCR • Voice")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            "Bienvenido" if lang == "es" else "Welcome"
        )
        st.markdown(
            """
            **Cliente:** chat tipo WhatsApp con voz, detección de datos y confirmación de pedido.  
            **Restaurante:** gestión de menú, órdenes, OCR, voz, FAQ dinámica.  
            **Admin:** idioma, modelo, tono, limpieza de datos y banners.
            """
            if lang == "es" else
            """
            **Client:** WhatsApp-like chat with voice, data detection and order confirmation.  
            **Restaurant:** menu management, orders, OCR, voice, dynamic FAQ.  
            **Admin:** language, model, tone, data cleanup and banners.
            """
        )
        st.info("Usa el menú lateral para navegar." if lang ==
                "es" else "Use the left sidebar to navigate.")

    with col2:
        st.subheader("Idioma / Language")
        new_lang = st.radio(
            "Idioma / Language",   # antes estaba vacío
            options=["es", "en"],
            index=0 if lang == "es" else 1,
            horizontal=True
        )
        if new_lang != lang:
            update_config({"language": new_lang})
            st.rerun()

    st.write("---")
    st.write("**Páginas:**")
    st.write("- 1️⃣ Cliente")
    st.write("- 2️⃣ Restaurante")
    st.write("- 3️⃣ Admin (Súper admin)")


if __name__ == "__main__":
    main()
