# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
from typing import List, Dict, Callable, Optional
import streamlit as st
import pandas as pd


def _image(img, **kwargs):
    try:
        return st.image(img, use_container_width=True, **{k: v for k, v in kwargs.items() if k != "use_container_width"})
    except TypeError:
        try:
            return st.image(img, use_column_width=True, **{k: v for k, v in kwargs.items() if k != "use_container_width"})
        except TypeError:
            return st.image(img)


def _button(label: str, key: Optional[str] = None):
    return st.button(label, key=key)


def menu_table_component(
    menu: List[Dict],
    lang: str = "es",
    deletable: bool = False,
    on_delete: Optional[Callable[[str], None]] = None,
):
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


def menu_gallery_component(
    menu: List[Dict],
    lang: str = "es",
    images: Optional[List[str]] = None,
    columns: int = 2,
):
    if not menu and not images:
        st.info("No hay elementos para mostrar." if lang ==
                "es" else "Nothing to show.")
        return
    if images:
        if columns < 1:
            columns = 1
        for i in range(0, len(images), columns):
            row = st.columns(columns)
            for j, col in enumerate(row):
                k = i + j
                if k < len(images):
                    with col:
                        _image(images[k])
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
