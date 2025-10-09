# -*- coding: utf-8 -*-
"""
Created on Thu Sep 25 10:37:58 2025

@author: geam9
"""

# pages/2_Admin.py
from __future__ import annotations
import io
import csv
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from backend.db import (
    add_menu_item, fetch_menu, fetch_orders,
    fetch_pending_questions, answer_pending_question,
    export_orders_csv, export_convos_csv,
)

from backend.ocr import parse_menu_from_image

load_dotenv()
st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")


def _get_lang() -> str:
    return st.session_state.get("lang", "es")


def _t(es: str, en: str) -> str:
    return es if _get_lang() == "es" else en


def main():
    lang = _get_lang()
    st.title(_t("🛠️ Restaurante (Admin)", "🛠️ Restaurant (Admin)"))

    # Sidebar: Logs/Descargas
    st.sidebar.markdown("### " + _t("Logs y Descargas", "Logs & Downloads"))
    if st.sidebar.button(_t("Descargar Órdenes (CSV)", "Download Orders (CSV)")):
        export_orders_csv("logs/orders.csv")
        st.sidebar.success("logs/orders.csv listo")
    if st.sidebar.button(_t("Descargar Interacciones (CSV)", "Download Difficult (CSV)")):
        export_convos_csv("logs/difficult_convos.csv")
        st.sidebar.success("logs/difficult_convos.csv listo")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### " + _t("Agregar Ítem", "Add Item"))
        with st.form("add_one"):
            name = st.text_input("Nombre / Name")
            desc = st.text_area("Descripción / Description")
            price = st.number_input("Precio / Price", min_value=0.0, step=0.5)
            currency = st.selectbox(
                "Moneda / Currency", ["USD", "EUR", "MXN", "COP", "ARS", "PEN", "CLP"])
            if st.form_submit_button(_t("Agregar Ítem", "Add Item")) and name:
                try:
                    add_menu_item(name, desc, float(price), currency)
                    st.success("OK")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with c2:
        st.markdown("#### " + _t("Carga Masiva (CSV/TXT) + OCR",
                    "Bulk Upload (CSV/TXT) + OCR"))
        up = st.file_uploader("CSV/TXT", type=["csv", "txt"])
        if up is not None:
            content = up.getvalue().decode("utf-8", errors="ignore")
            rows = []
            if up.name.lower().endswith(".csv"):
                for r in csv.DictReader(io.StringIO(content)):
                    rows.append((r.get("name"), r.get("description", ""), r.get(
                        "price"), r.get("currency", "USD")))
            else:
                for line in content.splitlines():
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        rows.append(
                            (parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else "USD"))
            ok = 0
            for (nm, ds, pr, cur) in rows:
                try:
                    add_menu_item(nm, ds, float(pr), cur)
                    ok += 1
                except Exception:
                    pass
            st.success(_t(f"Agregados {ok}", f"Inserted {ok}"))
            st.rerun()

        img = st.file_uploader("Imagen (opcional)", type=[
                               "png", "jpg", "jpeg"])
        if img is not None:
            parsed = parse_menu_from_image(img.read())
            for (nm, ds, pr) in parsed:
                try:
                    add_menu_item(nm, ds, float(pr))
                except Exception:
                    pass
            st.success(_t(f"Agregados {len(parsed)} desde OCR", f"Inserted {
                       len(parsed)} from OCR"))
            st.rerun()

    # Menú cargado
    st.write("---")
    data = fetch_menu()
    if not data:
        st.info(_t("Aún no hay ítems en el menú.", "No items in the menu yet."))
    else:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Órdenes confirmadas & pendientes
    st.write("---")
    c3, c4 = st.columns(2)

    with c3:
        st.subheader(_t("Órdenes Confirmadas", "Confirmed Orders"))
        orders = fetch_orders() or []
        if not orders:
            st.info("—")
        else:
            for o in orders:
                with st.expander(f"{o.get('created_at', '')} — {o.get('client_name', 'N/A')} — {o.get('total', 0)} {o.get('currency', 'USD')} — {o.get('status', 'confirmed')}"):
                    st.code(o.get("items_json", "[]"), language="json")

    with c4:
        st.subheader(_t("Interacciones por confirmar (1 minuto)",
                     "Pending confirmations (1 minute)"))
        pendings = fetch_pending_questions() or []
        if not pendings:
            st.info("—")
        else:
            for p in pendings:
                pid = p.get("id")
                q = p.get("question", "")
                created_at = p.get("created_at", "")
                with st.expander(f"[{created_at}] {q[:90]}..."):
                    st.write(q)
                    c5, c6, c7 = st.columns([1, 1, 2])
                    if c5.button(_t("Aprobar", "Approve"), key=f"ap_{pid}"):
                        answer_pending_question(pid, "approved", _t(
                            "He confirmado tu solicitud. ¡Continuemos!", "I’ve confirmed your request. Let’s continue!"))
                        st.rerun()
                    if c6.button(_t("Negar", "Deny"), key=f"dn_{pid}"):
                        answer_pending_question(pid, "denied", _t("Lo siento, no es posible esa modificación. ¿Deseas otra opción?",
                                                "Sorry, that customization isn't possible. Would you like another option?"))
                        st.rerun()
                    custom = c7.text_input(
                        _t("Mensaje / Message", "Message"), key=f"cu_{pid}")
                    if st.button(_t("Enviar", "Send"), key=f"sn_{pid}"):
                        if custom.strip():
                            answer_pending_question(
                                pid, f"custom:{custom.strip()}", custom.strip())
                            st.rerun()


if __name__ == "__main__":
    main()
