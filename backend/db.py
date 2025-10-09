# -*- coding: utf-8 -*-
"""
Created on Wed Sep 24 10:37:58 2025

@author: geam9
"""

from __future__ import annotations
import os
import json
import uuid
import datetime as dt
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from PIL import Image, ImageDraw, ImageFont
from backend.config import get_config

DB_DIR = "data"
MEDIA_DIR = os.path.join(DB_DIR, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "app.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

# --------- MODELOS ---------


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    special_notes = Column(String, default="")


class MenuImage(Base):
    __tablename__ = "menu_images"
    id = Column(Integer, primary_key=True)
    path = Column(String)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class BannerImage(Base):
    __tablename__ = "banner_images"
    id = Column(Integer, primary_key=True)
    path = Column(String)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)  # UUID
    client_name = Column(String)
    phone = Column(String)
    delivery_type = Column(String)  # pickup | delivery
    address = Column(Text)
    pickup_eta_min = Column(Integer)
    payment_method = Column(String)

    items_json = Column(Text)
    total = Column(Float, default=0.0)
    currency = Column(String, default="USD")

    # confirmed, preparing, ready, delivered
    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    priority = Column(Integer, default=10)
    sla_deadline = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)


class PendingQuestion(Base):
    __tablename__ = "pending_questions"
    id = Column(String, primary_key=True)  # UUID
    conversation_id = Column(String)
    question = Column(Text)
    language = Column(String, default="es")
    # pending/approved/denied/custom/expired
    status = Column(String, default="pending")
    answer_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


Base.metadata.create_all(engine)


def _s(): return SessionLocal()

# --------- SEED / BANNERS (se mantienen para compat, pero ya no se usan en Cliente) ---------


def _generate_banner(text: str, price: str, desc: str, filename: str):
    path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(path):
        return path
    img = Image.new("RGB", (1024, 360), color=(245, 245, 245))
    d = ImageDraw.Draw(img)
    try:
        font_b = ImageFont.truetype("arial.ttf", 48)
        font_m = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        font_b = ImageFont.load_default()
        font_m = ImageFont.load_default()
    d.text((40, 40), text, fill=(25, 25, 25), font=font_b)
    d.text((40, 120), price, fill=(60, 60, 60), font=font_b)
    d.text((40, 190), desc, fill=(80, 80, 80), font=font_m)
    img.save(path, format="PNG")
    return path


def ensure_db_and_seed():
    Base.metadata.create_all(engine)
    s = _s()
    try:
        if s.query(MenuItem).count() == 0:
            cfg = get_config()
            cur = cfg.get("currency", "USD")
            s.add_all([
                MenuItem(name="Hamburguesa", description="Pan, queso, carne, tomate, lechuga, cebolla y salsa de la casa.",
                         price=5.99, currency=cur, special_notes="alto en sal"),
                MenuItem(name="Agua", description="Botella de agua servida en vaso; con o sin hielo extra.",
                         price=1.99, currency=cur, special_notes=""),
                MenuItem(name="Duraznos al jugo", description="Duraznos deshuesados en almíbar con un toque de canela.",
                         price=3.99, currency=cur, special_notes="vegetariano"),
            ])
            s.commit()
        # banners opcionales solo como respaldo visual
        if s.query(BannerImage).count() == 0:
            p1 = _generate_banner(
                "Hamburguesa", "$5.99", "Pan, queso, carne y salsa de la casa", "banner_hamburguesa.png")
            p2 = _generate_banner(
                "Agua", "$1.99", "Botella en vaso; con o sin hielo extra", "banner_agua.png")
            p3 = _generate_banner(
                "Duraznos al jugo", "$3.99", "Duraznos en almíbar con canela", "banner_duraznos.png")
            s.add_all([BannerImage(path=p1), BannerImage(
                path=p2), BannerImage(path=p3)])
            s.commit()
    finally:
        s.close()

# --------- MENÚ ---------


def fetch_menu() -> List[Dict]:
    s = _s()
    try:
        rows = s.query(MenuItem).order_by(MenuItem.name.asc()).all()
        return [{"id": r.id, "name": r.name, "description": r.description, "price": r.price, "currency": r.currency, "special_notes": r.special_notes} for r in rows]
    finally:
        s.close()


def add_menu_item(name: str, description: str, price: float, currency: str, special_notes: str = ""):
    s = _s()
    try:
        s.add(MenuItem(name=name, description=description, price=price,
              currency=currency, special_notes=special_notes))
        s.commit()
    finally:
        s.close()


def delete_menu_item(item_id: int):
    s = _s()
    try:
        it = s.query(MenuItem).get(item_id)
        if it:
            s.delete(it)
            s.commit()
    finally:
        s.close()

# --------- IMÁGENES DEL MENÚ (gestión completa) ---------


def add_menu_image(uploaded_file) -> str:
    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".png"
    fname = f"menu_{uuid.uuid4().hex}{ext}"
    path = os.path.join(MEDIA_DIR, fname)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    s = _s()
    try:
        s.add(MenuImage(path=path))
        s.commit()
    finally:
        s.close()
    return path


def fetch_menu_images() -> List[str]:
    s = _s()
    try:
        rows = s.query(MenuImage).order_by(MenuImage.created_at.desc()).all()
        return [r.path for r in rows]
    finally:
        s.close()


def fetch_menu_images_full() -> List[Dict]:
    s = _s()
    try:
        rows = s.query(MenuImage).order_by(MenuImage.created_at.desc()).all()
        return [{"id": r.id, "path": r.path, "created_at": r.created_at} for r in rows]
    finally:
        s.close()


def delete_menu_image(image_id: int) -> bool:
    s = _s()
    try:
        r = s.query(MenuImage).get(image_id)
        if not r:
            return False
        try:
            if r.path and os.path.isfile(r.path):
                os.remove(r.path)
        except Exception:
            pass
        s.delete(r)
        s.commit()
        return True
    finally:
        s.close()

# --------- BANNERS (compat) ---------


def fetch_menu_banners() -> List[str]:
    s = _s()
    try:
        rows = s.query(BannerImage).order_by(
            BannerImage.created_at.desc()).all()
        return [r.path for r in rows]
    finally:
        s.close()

# --------- ORDERS / PENDINGS / EXPORTS (igual que antes; omitido por brevedad si ya lo tienes) ---------
# ... (mantén aquí el resto de funciones de órdenes e interacciones que ya tienes) ...

# =========================
# ===== LIMPIEZAS (Admin)
# =========================


def _safe_remove_file(path: str) -> None:
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def clear_orders() -> int:
    """
    Elimina TODAS las órdenes.
    Retorna la cantidad de registros eliminados.
    """
    s = _s()
    try:
        cnt = s.query(Order).count()
        s.query(Order).delete(synchronize_session=False)
        s.commit()
        return cnt
    finally:
        s.close()


def clear_pending_questions() -> int:
    """
    Elimina TODAS las interacciones pendientes/difíciles.
    """
    s = _s()
    try:
        cnt = s.query(PendingQuestion).count()
        s.query(PendingQuestion).delete(synchronize_session=False)
        s.commit()
        return cnt
    finally:
        s.close()


def clear_menu_items() -> int:
    """
    Elimina TODOS los ítems del menú.
    """
    s = _s()
    try:
        cnt = s.query(MenuItem).count()
        s.query(MenuItem).delete(synchronize_session=False)
        s.commit()
        return cnt
    finally:
        s.close()


def clear_menu_item(item_id: int) -> int:
    """
    Elimina un ítem del menú por ID.
    Retorna 1 si se eliminó, 0 si no existía.
    """
    s = _s()
    try:
        obj = s.query(MenuItem).get(item_id)
        if not obj:
            return 0
        s.delete(obj)
        s.commit()
        return 1
    finally:
        s.close()


def clear_menu_images() -> int:
    """
    Elimina TODAS las imágenes del menú (base y archivos).
    """
    s = _s()
    try:
        rows = s.query(MenuImage).all()
        for r in rows:
            _safe_remove_file(r.path)
            s.delete(r)
        s.commit()
        return len(rows)
    finally:
        s.close()


def clear_menu_image(image_id: int) -> int:
    """
    Elimina una imagen del menú por ID (base y archivo).
    Retorna 1 si se eliminó, 0 si no existía.
    """
    s = _s()
    try:
        r = s.query(MenuImage).get(image_id)
        if not r:
            return 0
        _safe_remove_file(r.path)
        s.delete(r)
        s.commit()
        return 1
    finally:
        s.close()


def clear_banner_images() -> int:
    """
    Elimina TODOS los banners (base y archivos).
    Nota: aunque ya no los uses en Cliente, se limpian por compatibilidad.
    """
    s = _s()
    try:
        rows = s.query(BannerImage).all()
        for r in rows:
            _safe_remove_file(r.path)
            s.delete(r)
        s.commit()
        return len(rows)
    finally:
        s.close()


def clear_everything(keep_media_folder: bool = True) -> dict:
    """
    Limpieza masiva. Útil para el Súper Admin:
      - Órdenes
      - Pendientes
      - Ítems del menú
      - Imágenes del menú (y archivos)
      - Banners (y archivos)
    Retorna un resumen por tipo.
    """
    res = {
        "orders": clear_orders(),
        "pending_questions": clear_pending_questions(),
        "menu_items": clear_menu_items(),
        "menu_images": clear_menu_images(),
        "banner_images": clear_banner_images()
    }

    # Opcionalmente, limpiar también la carpeta media vacía (no recomendado en demo)
    if not keep_media_folder:
        try:
            if os.path.isdir(MEDIA_DIR) and not os.listdir(MEDIA_DIR):
                os.rmdir(MEDIA_DIR)
        except Exception:
            pass

    return res
