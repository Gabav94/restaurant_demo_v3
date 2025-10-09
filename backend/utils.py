# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
import base64
import streamlit as st


def render_auto_carousel(paths, height_px=220, interval_sec=4):
    """
    Carrusel simple autónomo usando base64 embebido (no depende de st.image).
    paths: lista de rutas locales a imágenes.
    """
    if not paths:
        return
    imgs_b64 = []
    for p in paths:
        try:
            with open(p, "rb") as f:
                b = base64.b64encode(f.read()).decode()
            ext = (p.split(".")[-1] or "png").lower()
            if ext not in ("png", "jpg", "jpeg", "webp"):
                ext = "png"
            imgs_b64.append(f"data:image/{ext};base64,{b}")
        except Exception:
            continue
    if not imgs_b64:
        return

    html = f"""
    <style>
    .carousel-wrap {{
      position: relative; overflow: hidden; width: 100%;
      height: {height_px}px; border-radius: 12px; border:1px solid #eee;
    }}
    .carousel-track {{
      display: flex; width: {len(imgs_b64)*100}%;
      animation: slide {len(imgs_b64)*interval_sec}s infinite linear;
    }}
    .carousel-item {{
      flex: 0 0 calc(100% / {len(imgs_b64)}); display:flex; align-items:center; justify-content:center;
      background:#111;
    }}
    .carousel-item img {{ max-height: {height_px}px; width:auto; }}
    @keyframes slide {{
      0% {{ transform: translateX(0%); }}
      100% {{ transform: translateX(-{(len(imgs_b64)-1)*100}%); }}
    }}
    </style>
    <div class="carousel-wrap">
      <div class="carousel-track">
        {''.join(
        f'<div class="carousel-item"><img src="{src}"/></div>' for src in imgs_b64)}
      </div>
    </div>
    """
    st.components.v1.html(html, height=height_px+16, scrolling=False)
