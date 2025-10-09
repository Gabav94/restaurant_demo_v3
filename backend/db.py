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
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from PIL import Image, ImageDraw, ImageFont
from backend.config import get_config

DB_DIR = "data"
MEDIA_DIR = os.path.join(DB_DIR, "media")
ASSETS_DIR = os.path.join("assets", "menu_images")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "app.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()
def _s(): return SessionLocal()

# ---------------- Models ----------------


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


class BannerImage(Base):  # compat
    __tablename__ = "banner_images"
    id = Column(Integer, primary_key=True)
    path = Column(String)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)  # UUID
    client_name = Column(String)
    phone = Column(String)
    delivery_type = Column(String)  # pickup|delivery
    address = Column(Text)
    pickup_eta_min = Column(Integer)
    payment_method = Column(String)
    items_json = Column(Text)
    total = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    priority = Column(Integer, default=10)
    sla_deadline = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)


class PendingQuestion(Base):
    __tablename__ = "pending_questions"
    id = Column(String, primary_key=True)
    conversation_id = Column(String)
    question = Column(Text)
    language = Column(String, default="es")
    status = Column(String, default="pending")
    answer_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


Base.metadata.create_all(engine)

# ------------- Migration helpers -------------


def _column_missing(table: str, column: str) -> bool:
    insp = inspect(engine)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column not in cols


def migrate_orders_table():
    with engine.begin() as conn:
        needed = [
            ("client_name", "TEXT"), ("phone",
                                      "TEXT"), ("delivery_type", "TEXT"), ("address", "TEXT"),
            ("pickup_eta_min", "INTEGER"), ("payment_method",
                                            "TEXT"), ("items_json", "TEXT"),
            ("total", "FLOAT"), ("currency", "TEXT"), ("status",
                                                       "TEXT"), ("created_at", "DATETIME"),
            ("priority", "INTEGER"), ("sla_deadline",
                                      "DATETIME"), ("sla_breached", "BOOLEAN"),
        ]
        for col, typ in needed:
            if _column_missing("orders", col):
                conn.execute(
                    text(f"ALTER TABLE orders ADD COLUMN {col} {typ}"))

# ------------- Assets seed helpers -------------


def _list_asset_images() -> List[str]:
    if not os.path.isdir(ASSETS_DIR):
        return []
    valid = {".png", ".jpg", ".jpeg", ".webp"}
    return [os.path.join(ASSETS_DIR, f) for f in os.listdir(ASSETS_DIR) if os.path.splitext(f)[1].lower() in valid]


def seed_menu_images_from_assets() -> int:
    s = _s()
    try:
        if s.query(MenuImage).count() > 0:
            return 0
        paths = _list_asset_images()
        if not paths:
            return 0
        cnt = 0
        for ap in paths:
            ext = os.path.splitext(ap)[1].lower() or ".png"
            fname = f"menu_{uuid.uuid4().hex}{ext}"
            dst = os.path.join(MEDIA_DIR, fname)
            try:
                with open(ap, "rb") as fr, open(dst, "wb") as fw:
                    fw.write(fr.read())
                s.add(MenuImage(path=dst))
                cnt += 1
            except Exception:
                pass
        s.commit()
        return cnt
    finally:
        s.close()

# ------------- Seed -------------


def _generate_banner(text: str, price: str, desc: str, filename: str) -> str:
    path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(path):
        return path
    img = Image.new("RGB", (1024, 360), (245, 245, 245))
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
    img.save(path, "PNG")
    return path


def ensure_db_and_seed():
    Base.metadata.create_all(engine)
    migrate_orders_table()
    s = _s()
    try:
        if s.query(MenuItem).count() == 0:
            cur = get_config().get("currency", "USD")
            s.add_all([
                MenuItem(name="Hamburguesa", description="Pan, queso, carne, tomate, lechuga, cebolla y salsa de la casa.",
                         price=5.99, currency=cur, special_notes="alto en sal"),
                MenuItem(name="Agua", description="Botella de agua servida en vaso; con o sin hielo extra.",
                         price=1.99, currency=cur, special_notes=""),
                MenuItem(name="Duraznos al jugo", description="Duraznos deshuesados en almíbar con un toque de canela.",
                         price=3.99, currency=cur, special_notes="vegetariano"),
            ])
            s.commit()
        seed_menu_images_from_assets()
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

# ------------- Menu CRUD -------------


def fetch_menu() -> List[Dict[str, Any]]:
    s = _s()
    try:
        rows = s.query(MenuItem).order_by(MenuItem.name.asc()).all()
        return [{"id": r.id, "name": r.name, "description": r.description, "price": float(r.price or 0.0),
                 "currency": r.currency or "USD", "special_notes": r.special_notes or ""} for r in rows]
    finally:
        s.close()


def add_menu_item(name: str, description: str, price: float, currency: str, special_notes: str = "") -> None:
    s = _s()
    try:
        s.add(MenuItem(name=name.strip(), description=(description or "").strip(),
                       price=float(price or 0.0), currency=currency, special_notes=(special_notes or "").strip()))
        s.commit()
    finally:
        s.close()


def delete_menu_item(item_id: int) -> bool:
    s = _s()
    try:
        obj = s.query(MenuItem).get(item_id)
        if not obj:
            return False
        s.delete(obj)
        s.commit()
        return True
    finally:
        s.close()

# ------------- Menu images -------------


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


def fetch_menu_images_full() -> List[Dict[str, Any]]:
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

# ------------- Orders / Queue -------------


def _compute_total(items: List[Dict]) -> float:
    return round(sum(float(i.get("unit_price", 0.0))*int(i.get("qty", 1)) for i in (items or [])), 2)


def create_order_from_chat_ready(client: Dict[str, Any], items: List[Dict], currency: str = "USD") -> Dict[str, Any]:
    now = dt.datetime.utcnow()
    total = _compute_total(items)
    order_id = uuid.uuid4().hex
    if (client or {}).get("delivery_type") == "delivery":
        sla_deadline = now+dt.timedelta(minutes=30)
    else:
        eta = int((client or {}).get("pickup_eta_min") or 0) or 30
        sla_deadline = now+dt.timedelta(minutes=eta)
    o = Order(id=order_id, client_name=(client or {}).get("name", ""), phone=(client or {}).get("phone", ""),
              delivery_type=(client or {}).get("delivery_type", ""), address=(client or {}).get("address", ""),
              pickup_eta_min=int((client or {}).get("pickup_eta_min") or 0), payment_method=(client or {}).get("payment_method", ""),
              items_json=json.dumps(items, ensure_ascii=False), total=total, currency=currency,
              status="confirmed", created_at=now, priority=10, sla_deadline=sla_deadline, sla_breached=False)
    s = _s()
    try:
        s.add(o)
        s.commit()
        return {"id": o.id, "client_name": o.client_name, "phone": o.phone, "delivery_type": o.delivery_type,
                "address": o.address, "pickup_eta_min": o.pickup_eta_min, "payment_method": o.payment_method,
                "items": items, "total": total, "currency": currency, "status": "confirmed",
                "created_at": now.isoformat(), "priority": 10}
    finally:
        s.close()


def fetch_orders_queue() -> List[Dict[str, Any]]:
    s = _s()
    try:
        rows = s.query(Order).order_by(
            Order.priority.asc(), Order.created_at.asc()).all()
        out = []
        for r in rows:
            try:
                items = json.loads(r.items_json or "[]")
            except Exception:
                items = []
            out.append({"id": r.id, "client_name": r.client_name, "phone": r.phone, "delivery_type": r.delivery_type,
                        "address": r.address, "pickup_eta_min": r.pickup_eta_min, "payment_method": r.payment_method,
                        "items": items, "total": float(r.total or 0.0), "currency": r.currency or "USD",
                        "status": r.status, "created_at": r.created_at, "priority": int(r.priority or 10),
                        "sla_deadline": r.sla_deadline, "sla_breached": bool(r.sla_breached)})
        return out
    finally:
        s.close()


def update_order_status(order_id: str, new_status: str) -> bool:
    s = _s()
    try:
        r = s.query(Order).get(order_id)
        if not r:
            return False
        r.status = new_status
        if new_status == "delivered":
            r.priority = 999
        s.commit()
        return True
    finally:
        s.close()


def bump_priorities_if_sla_missed() -> int:
    now = dt.datetime.utcnow()
    s = _s()
    try:
        rows = s.query(Order).filter(
            Order.sla_deadline.isnot(None),
            Order.sla_deadline < now,
            Order.status != "delivered"
        ).all()
        cnt = 0
        for r in rows:
            if not r.sla_breached or (r.priority or 10) > 1:
                r.sla_breached = True
                r.priority = 1
                cnt += 1
        s.commit()
        return cnt
    finally:
        s.close()

# ------------- Pendings + Export -------------


def create_pending_question(conversation_id: str, question: str, language: str = "es", ttl_sec: int = 60) -> str:
    pid = uuid.uuid4().hex
    now = dt.datetime.utcnow()
    exp = now+dt.timedelta(seconds=int(ttl_sec or 60))
    s = _s()
    try:
        s.add(PendingQuestion(id=pid, conversation_id=conversation_id, question=question, language=language,
                              status="pending", created_at=now, expires_at=exp))
        s.commit()
        return pid
    finally:
        s.close()


def fetch_pending_questions() -> List[Dict[str, Any]]:
    s = _s()
    try:
        rows = s.query(PendingQuestion).order_by(
            PendingQuestion.created_at.desc()).all()
        return [{"id": r.id, "conversation_id": r.conversation_id, "question": r.question, "language": r.language,
                 "status": r.status, "answer_msg": r.answer_msg, "created_at": r.created_at, "expires_at": r.expires_at}
                for r in rows]
    finally:
        s.close()


def answer_pending_question(pending_id: str, status: str, message: Optional[str] = None) -> bool:
    s = _s()
    try:
        r = s.query(PendingQuestion).get(pending_id)
        if not r:
            return False
        r.status = status
        if message:
            r.answer_msg = message
        s.commit()
        return True
    finally:
        s.close()


def autoapprove_expired_pendings(default_message_es="Aprobado por tiempo.", default_message_en="Approved due to timeout.") -> int:
    now = dt.datetime.utcnow()
    s = _s()
    try:
        rows = s.query(PendingQuestion).filter(
            PendingQuestion.status == "pending",
            PendingQuestion.expires_at.isnot(None),
            PendingQuestion.expires_at < now
        ).all()
        cnt = 0
        for r in rows:
            r.status = "approved"
            r.answer_msg = default_message_es if (
                r.language or "es") == "es" else default_message_en
            cnt += 1
        s.commit()
        return cnt
    finally:
        s.close()


def export_orders_csv() -> str:
    import csv
    from io import StringIO
    s = _s()
    try:
        rows = s.query(Order).order_by(Order.created_at.asc()).all()
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "client_name", "phone", "delivery_type", "address", "pickup_eta_min", "payment_method",
                   "items_json", "total", "currency", "status", "priority", "sla_deadline", "sla_breached", "created_at"])
        for r in rows:
            w.writerow([r.id, r.client_name, r.phone, r.delivery_type, r.address, r.pickup_eta_min, r.payment_method, r.items_json,
                        f"{float(r.total or 0.0):.2f}", r.currency, r.status, r.priority,
                        r.sla_deadline.isoformat() if r.sla_deadline else "", "1" if r.sla_breached else "0",
                        r.created_at.isoformat() if r.created_at else ""])
        return buf.getvalue()
    finally:
        s.close()


def export_pendings_csv() -> str:
    import csv
    from io import StringIO
    s = _s()
    try:
        rows = s.query(PendingQuestion).order_by(
            PendingQuestion.created_at.asc()).all()
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "conversation_id", "question", "language",
                   "status", "answer_msg", "created_at", "expires_at"])
        for r in rows:
            w.writerow([r.id, r.conversation_id, r.question, r.language, r.status, r.answer_msg or "",
                        r.created_at.isoformat() if r.created_at else "",
                        r.expires_at.isoformat() if r.expires_at else ""])
        return buf.getvalue()
    finally:
        s.close()
