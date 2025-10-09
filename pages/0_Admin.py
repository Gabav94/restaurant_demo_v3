# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:14:54 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from backend.config import get_config, set_config
from backend.db import ensure_db_and_seed, fetch_menu_images_full
from backend.utils import render_auto_carousel

st.set_page_config(page_title="Admin (Súper)", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){ .block-container { padding-top:.8rem; padding-bottom:2rem; } }
.card{border:1px solid #eee;border-radius:12px;padding:12px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.03);}
.hint{color:#666;font-size:.9rem}
</style>
""", unsafe_allow_html=True)


def main():
    cfg = get_config()
    lang = cfg.get("language", "es")
    def t(es, en): return es if lang == "es" else en

    st.title("🛠️ Admin (Súper configuración)")
    with st.expander(t("Inicialización (DB/seed)", "Initialization (DB/seed)"), expanded=False):
        if st.button(t("🔧 Asegurar DB y datos de ejemplo", "🔧 Ensure DB and sample data")):
            try:
                ensure_db_and_seed()
                st.success(t("Listo.", "Done."))
            except Exception as e:
                st.error(f"Init error: {e}")

    st.subheader(t("Parámetros del asistente", "Assistant parameters"))
    with st.form("super_form"):
        c1, c2 = st.columns(2)
        with c1:
            assistant_name = st.text_input(t("Nombre del asistente", "Assistant name"),
                                           value=cfg.get("assistant_name", "Asistente" if lang == "es" else "Assistant"))
            tone_ph = "Amable y profesional; breve y guiado." if lang == "es" else "Friendly and professional; concise and guided."
            tone = st.text_input(t("Tono de conversación", "Conversation tone"),
                                 value=cfg.get("tone", tone_ph), placeholder=tone_ph)
            model = st.selectbox(t("Modelo", "Model"),
                                 ["gpt-4o-mini", "gpt-4o",
                                     "gpt-4.1-mini", "gpt-3.5-turbo"],
                                 index=0)
            temperature = st.slider(t("Temperatura", "Temperature"), 0.0, 1.0, float(
                cfg.get("temperature", 0.4)), 0.05)
        with c2:
            language = st.selectbox(t("Idioma de la app", "App language"), ["es", "en"],
                                    index=(0 if cfg.get("language", "es") == "es" else 1))
            currency = st.selectbox(t("Moneda por defecto", "Default currency"),
                                    ["USD", "EUR", "MXN", "ARS", "COP", "CLP"],
                                    index=(["USD", "EUR", "MXN", "ARS", "COP", "CLP"].index(cfg.get("currency", "USD"))
                                           if cfg.get("currency", "USD") in ["USD", "EUR", "MXN", "ARS", "COP", "CLP"] else 0))
        if st.form_submit_button(t("💾 Guardar", "💾 Save")):
            try:
                set_config({
                    "assistant_name": assistant_name.strip() or ("Asistente" if language == "es" else "Assistant"),
                    "tone": tone.strip() or tone_ph,
                    "model": model,
                    "temperature": float(temperature),
                    "language": language,
                    "currency": currency,
                })
                st.success(t("Configuración guardada.", "Settings saved."))
            except Exception as e:
                st.error(f"Save error: {e}")

    st.write("---")
    st.subheader(t("Vista previa del carrusel (solo lectura)",
                 "Carousel preview (read-only)"))
    imgs = fetch_menu_images_full()
    if imgs:
        render_auto_carousel([r["path"] for r in imgs],
                             height_px=180, interval_sec=4)
    else:
        st.info(t("No hay imágenes aún. Sube desde **Restaurante**.",
                "No images yet. Upload from **Restaurant**."))


if __name__ == "__main__":
    main()
