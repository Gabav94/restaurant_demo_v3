# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
from typing import List, Dict, Callable, Optional
import streamlit as st
import pandas as pd
import uuid

# ==========================================================
# ==== 1. Helpers de imagen / compatibilidad ==========
# ==========================================================


def _image(img, **kwargs):
    """Compatibilidad para versiones antiguas de Streamlit."""
    try:
        return st.image(img, use_container_width=True, **{k: v for k, v in kwargs.items() if k != "use_container_width"})
    except TypeError:
        try:
            return st.image(img, use_column_width=True, **{k: v for k, v in kwargs.items() if k != "use_container_width"})
        except TypeError:
            return st.image(img)


def _button(label: str, key: Optional[str] = None):
    return st.button(label, key=key)

# ==========================================================
# ==== 2. Carrusel automático de imágenes (sin JS) ==========
# ==========================================================


def render_auto_carousel(images: List[str], height_px: int = 220, interval_sec: float = 4.0):
    """
    Carrusel CSS-only.
    Recorre automáticamente las imágenes cada `interval_sec` segundos.
    """
    if not images:
        return

    cid = f"carousel_{uuid.uuid4().hex[:8]}"
    slides = "".join(
        [f"<div class='slide'><img src='file://{src}'/></div>" for src in images])
    n = max(1, len(images))
    steps = []
    for i in range(n):
        pct = int(i * (100 / n))
        x = int(-i * (100 / n))
        steps.append(f"{pct}% {{ transform: translateX({x}%); }}")
    steps.append("100% { transform: translateX(0%); }")

    css = f"""
    <style>
    #{cid} {{
      position: relative;
      width: 100%;
      overflow: hidden;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }}
    #{cid} .track {{
      display: flex;
      width: {n*100}%;
      animation: slide_{cid} {max(1.0, n*interval_sec)}s infinite ease-in-out;
    }}
    #{cid} .slide {{
      flex: 0 0 {100/n}%;
      display:flex;
      align-items:center;
      justify-content:center;
      background:#f7f7f7;
      height: {height_px}px;
    }}
    #{cid} .slide img {{
      max-height: {height_px-10}px;
      width: auto;
      object-fit: contain;
      border-radius: 8px;
    }}
    @keyframes slide_{cid} {{
      {" ".join(steps)}
    }}
    @media (max-width: 900px){{
      #{cid} .slide {{ height: {int(height_px*0.8)}px; }}
      #{cid} .slide img {{ max-height: {int((height_px-10)*0.8)}px; }}
    }}
    </style>
    """

    html = f"""
    {css}
    <div id="{cid}">
      <div class="track">
        {slides}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================================
# ==== 3. Tabla de ítems del menú ==========================
# ==========================================================


def menu_table_component(
    menu: List[Dict],
    lang: str = "es",
    deletable: bool = False,
    on_delete: Optional[Callable[[str], None]] = None,
):
    """Renderiza el menú como tabla editable o informativa."""
    if not menu:
        st.info("No hay ítems de menú." if lang == "es" else "No menu items.")
        return

    df = pd.DataFrame([{
        "id": m.get("id"),
        "Nombre" if lang == "es" else "Name": m.get("name", ""),
        "Descripción" if lang == "es" else "Description": m.get("description", ""),
        "Precio" if lang == "es" else "Price": f'{m.get("currency", "")} {float(m.get("price", 0.0)):.2f}',
        "Notas" if lang == "es" else "Notes": m.get("special_notes", ""),
    } for m in menu])

    try:
        st.dataframe(df, use_container_width=True, hide_index=True)
    except TypeError:
        st.dataframe(df)

    if deletable and on_delete:
        st.markdown("---")
        st.caption("Eliminar ítem del menú" if lang ==
                   "es" else "Delete menu item")
        ids = [m.get("id") for m in menu if m.get("id") is not None]
        if ids:
            sel = st.selectbox("ID", ids, key="menu_delete_id")
            if _button("Borrar" if lang == "es" else "Delete", key="btn_delete_menu"):
                try:
                    on_delete(sel)
                    st.success("Ítem eliminado." if lang ==
                               "es" else "Item deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(("No se pudo eliminar: " if lang ==
                             "es" else "Failed to delete: ") + str(e))

# ==========================================================
# ==== 4. Galería de imágenes más compacta ================
# ==========================================================


def menu_gallery_component(
    menu: List[Dict],
    lang: str = "es",
    images: Optional[List[str]] = None,
    columns: int = 3,
    compact: bool = True
):
    """
    Muestra una galería de ítems o imágenes.
    Compacta por defecto (baja altura).
    """
    if not menu and not images:
        st.info("No hay elementos para mostrar." if lang ==
                "es" else "Nothing to show.")
        return

    # -- Imágenes (rejilla) --
    if images:
        if columns < 1:
            columns = 1
        for i in range(0, len(images), columns):
            row = st.columns(columns)
            for j, col in enumerate(row):
                k = i + j
                if k < len(images):
                    with col:
                        height = 160 if compact else 240
                        try:
                            st.image(images[k], use_container_width=True)
                        except TypeError:
                            st.image(images[k], use_column_width=True)
                        st.markdown("<div style='height:4px'></div>",
                                    unsafe_allow_html=True)

    # -- Descripción textual --
    if menu:
        for m in menu:
            name = m.get("name", "")
            price = f'{m.get("currency", "")} {float(m.get("price", 0.0)):.2f}'
            notes = m.get("special_notes", "")
            desc = m.get("description", "")
            st.markdown(f"**{name}** — {price}")
            if notes:
                st.caption(notes)
            if desc:
                st.write(desc)
            st.write("")
