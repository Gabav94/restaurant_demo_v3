# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 22:16:39 2025

@author: geam9
"""

from __future__ import annotations
import streamlit as st
from backend.config import get_config
from backend.db import (
    ensure_db_and_seed, add_menu_item, fetch_menu, delete_menu_item,
    add_menu_image, fetch_menu_images_full, delete_menu_image,
    fetch_orders_queue, update_order_status, bump_priorities_if_sla_missed
)
from backend.utils import render_auto_carousel

st.set_page_config(page_title="Restaurante", page_icon="👩‍🍳", layout="wide")

st.markdown("""
<style>
@media (max-width: 900px){ .block-container { padding-top:.8rem; padding-bottom:2rem; } }
.card{border:1px solid #eee;border-radius:12px;padding:12px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.03);}
.tbl thead th{background:#fafafa}
</style>
""", unsafe_allow_html=True)


def _t(lang): return (lambda es, en: es if lang == "es" else en)


def main():
    ensure_db_and_seed()  # <- migración + seed
    cfg = get_config()
    lang = cfg.get("language", "es")
    t = _t(lang)
    currency = cfg.get("currency", "USD")

    st.title("👩‍🍳 " + ("Restaurante" if lang == "es" else "Restaurant"))

    # --- Carrusel de imágenes (gestión) ---
    st.subheader(t("Imágenes del menú (carrusel)", "Menu images (carousel)"))
    imgs = fetch_menu_images_full()
    colA, colB = st.columns([1.2, 1])
    with colA:
        if imgs:
            render_auto_carousel([r["path"]
                                 for r in imgs], height_px=180, interval_sec=4)
        else:
            st.info(t("Sin imágenes. Sube abajo.", "No images. Upload below."))
    with colB:
        up = st.file_uploader(t("Subir imágenes", "Upload images"), type=[
                              "png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
        if up:
            for f in up:
                try:
                    add_menu_image(f)
                except Exception as e:
                    st.error(f"Upload error: {e}")
            st.success(t("Imágenes cargadas.", "Images uploaded."))
            st.rerun()
        if imgs:
            st.write(t("Eliminar imagen", "Delete image"))
            for r in imgs:
                cols = st.columns([1, 3])
                with cols[0]:
                    if st.button("🗑️", key=f"del_{r['id']}"):
                        delete_menu_image(r["id"])
                        st.rerun()
                with cols[1]:
                    st.caption(r["path"])

    st.write("---")

    # --- Menú (tabla simple + alta) ---
    st.subheader(t("Menú", "Menu"))
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**"+t("Agregar ítem", "Add item")+"**")
        name = st.text_input(t("Nombre", "Name"))
        desc = st.text_area(t("Descripción", "Description"))
        price = st.number_input(t("Precio", "Price"), min_value=0.0, step=0.1)
        notes = st.text_input(t("Notas especiales (tags)", "Special notes (tags)"),
                              placeholder="vegetariano, sin gluten, picante…")
        if st.button(t("Agregar", "Add")):
            try:
                add_menu_item(name, desc, price, currency, notes)
                st.success(t("Ítem agregado.", "Item added."))
                st.rerun()
            except Exception as e:
                st.error(f"DB error: {e}")
    with c2:
        data = fetch_menu()
        if data:
            for m in data:
                cols = st.columns([3, 2, 2, 1])
                cols[0].markdown(f"**{m['name']}**")
                cols[1].markdown(f"{currency} {m['price']:.2f}")
                cols[2].markdown(f"`{m.get('special_notes', '')}`")
                if cols[3].button("🗑️", key=f"del_item_{m['id']}"):
                    delete_menu_item(m["id"])
                    st.rerun()
        else:
            st.info(t("No hay ítems aún.", "No items yet."))

    st.write("---")

    # --- Órdenes (cola) ---
    st.subheader(t("Órdenes", "Orders"))
    try:
        bump_priorities_if_sla_missed()
    except Exception as e:
        st.warning(f"SLA check: {e}")

    q = fetch_orders_queue()
    if not q:
        st.info(t("Sin órdenes aún.", "No orders yet."))
    else:
        for o in q:
            sla = "🔴" if o["sla_breached"] else "🟢"
            st.markdown(f"**{o['client_name']}** · {o['phone']
                                                    } · {o['delivery_type']} · {o['payment_method']} {sla}")
            st.caption(o["address"])
            st.write(o["items"])
            st.write(f"{o['currency']} {o['total']:.2f} · {o['status']}")
            c1, c2, c3 = st.columns(3)
            if c1.button("preparing", key=f"prep_{o['id']}"):
                update_order_status(o["id"], "preparing")
                st.rerun()
            if c2.button("ready", key=f"ready_{o['id']}"):
                update_order_status(o["id"], "ready")
                st.rerun()
            if c3.button("delivered", key=f"del_{o['id']}"):
                update_order_status(o["id"], "delivered")
                st.rerun()


if __name__ == "__main__":
    main()
