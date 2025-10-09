# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:36:48 2025

@author: geam9
"""

# streamlit_app.py
import streamlit as st
from dotenv import load_dotenv, dotenv_values
from backend.config import get_config, ensure_default_config

load_dotenv()
st.set_page_config(page_title="RAIVA DEMO", page_icon="🍽️", layout="wide")


def main():
    ensure_default_config()
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = (lambda es, en: es if lang == "es" else en)

    st.title(t("🍽️ Demo AI Restaurante", "🍽️ AI Restaurant Demo"))
    st.markdown(t(
        """
        ### Bienvenido
        - Usa el menú de la izquierda para entrar como **Cliente** o **Restaurante**.
        - Todo el flujo usa un **agente LLM** configurable en **Admin (Superconfiguración)**.
        """,
        """
        ### Welcome
        - Use the left menu to go to **Client** or **Restaurant**.
        - The whole flow uses a configurable **LLM agent** in **Admin (Superconfig)**.
        """
    ))

    ok = dotenv_values().get("OPENAI_API_KEY")
    if not ok:
        st.warning(t("No se encontró `OPENAI_API_KEY` en .env",
                   "`OPENAI_API_KEY` not found in .env"))

    st.info(t("Selecciona una página del sidebar para empezar.",
            "Choose a page from the sidebar to start."))


if __name__ == "__main__":
    main()
