# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:36:48 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from backend.config import get_config
from backend.db import ensure_db_and_seed, fetch_menu_images_full
from backend.utils import render_auto_carousel

st.set_page_config(page_title="InnovaChat • Restaurantes",
                   page_icon="🍽️", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){
  .block-container { padding-top: 0.8rem; padding-bottom: 2rem; }
}
.card{border:1px solid #eee;border-radius:12px;padding:14px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.03);}
.hint{color:#666;font-size:.9rem}
</style>
""", unsafe_allow_html=True)


def _t(lang):
    return (lambda es, en: es if lang == "es" else en)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)

    st.title(t("🍽️ RAIVA - InnovaChat para Restaurantes — Demo",
             "🍽️ RAIVA - InnovaChat for Restaurants — Demo"))
    st.caption(t("Bienvenido/a. Usa el menú lateral: **Cliente**, **Restaurante**, **Admin (Súper)**.",
                 "Welcome. Use the left sidebar: **Client**, **Restaurant**, **Admin (Super)**."))

    with st.expander(t("Inicialización (opcional)", "Initialization (optional)"), expanded=False):
        st.write(t("Si es tu primera vez, crea datos de ejemplo y carga imágenes de assets.",
                   "If this is your first time, create sample data and load images from assets."))
        if st.button(t("🔧 Asegurar DB y datos de ejemplo", "🔧 Ensure DB and sample data")):
            try:
                ensure_db_and_seed()
                st.success(t("Listo. Abre Cliente o Restaurante.",
                           "Done. Open Client or Restaurant."))
            except Exception as e:
                st.error(f"Init error: {e}")

    imgs = fetch_menu_images_full()
    colA, colB = st.columns([1.2, 1])
    with colA:
        st.subheader(t("Vista previa del carrusel", "Carousel preview"))
        if imgs:
            render_auto_carousel([r["path"]
                                 for r in imgs], height_px=220, interval_sec=4)
            st.caption(t("El Cliente verá este carrusel.",
                       "Client will see this carousel."))
        else:
            st.info(t("No hay imágenes aún. Sube desde **Restaurante** o corre la inicialización.",
                    "No images yet. Upload from **Restaurant** or run initialization."))

    with colB:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(t("Entrar a…", "Go to…"))
        st.write("• " + t("**Cliente** (chat)", "**Client** (chat)"))
        st.write("• " + t("**Restaurante** (gestión)", "**Restaurant** (ops)"))
        st.write("• " + t("**Admin (Súper)** (configuración)",
                 "**Admin (Super)** (settings)"))
        st.markdown('<div class="hint">'+t("Usa el menú lateral izquierdo.",
                    "Use the left sidebar.")+'</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    st.subheader(t("Configuración actual", "Current configuration"))
    st.write({
        "language": cfg.get("language"),
        "assistant_name": cfg.get("assistant_name"),
        "tone": cfg.get("tone"),
        "model": cfg.get("model"),
        "temperature": cfg.get("temperature"),
        "currency": cfg.get("currency"),
    })


if __name__ == "__main__":
    main()
