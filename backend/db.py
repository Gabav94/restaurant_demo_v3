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
from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, and_
)
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from PIL import Image, ImageDraw, ImageFont

from config import get_config

# DB_DIR = "data"
# MEDIA_DIR = os.path.join(DB_DIR, "media")
# os.makedirs(MEDIA_DIR, exist_ok=True)
# Ancla rutas a la raíz del proyecto (carpeta que contiene /backend)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_DIR = os.path.join(ROOT_DIR, "data")
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
    # created+30min or pickup ETA
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


def _colnames(table: str) -> set:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return {r[1] for r in rows}  # r[1] = name


def _table_exists(table: str) -> bool:
    with engine.connect() as conn:
        try:
            conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            return True
        except Exception:
            return False


def ensure_schema():
    with engine.begin() as conn:
        # pending_questions
        if not _table_exists("pending_questions"):
            # crear tabla completa
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pending_questions (
              id TEXT PRIMARY KEY,
              conversation_id TEXT,
              question TEXT,
              language TEXT DEFAULT 'es',
              status TEXT DEFAULT 'pending',
              answer_msg TEXT,
              created_at TIMESTAMP,
              expires_at TIMESTAMP
            )
            """))
        else:
            cols = _colnames("pending_questions")
            if "status" not in cols:
                conn.execute(
                    text("ALTER TABLE pending_questions ADD COLUMN status TEXT DEFAULT 'pending'"))
            if "answer_msg" not in cols:
                conn.execute(
                    text("ALTER TABLE pending_questions ADD COLUMN answer_msg TEXT"))
            if "expires_at" not in cols:
                conn.execute(
                    text("ALTER TABLE pending_questions ADD COLUMN expires_at TIMESTAMP"))


def _s(): return SessionLocal()

# --------- SEED / BANNERS ---------


def _abs(p): return os.path.abspath(p)


def _generate_banner(text: str, price: str, desc: str, filename: str):
    path = _abs(os.path.join(MEDIA_DIR, filename))  # <-- absoluto
    if os.path.exists(path):
        return path
    # banner 1024x360
    img = Image.new("RGB", (1024, 360), color=(245, 245, 245))
    d = ImageDraw.Draw(img)
    # tipografía genérica
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


def normalize_media_records() -> tuple[int, int]:
    """
    - Reemplaza backslashes por slashes. Cuida en Cloud
    - Reancora cada imagen a MEDIA_DIR usando basename.
    - Si el archivo no existe físicamente, borra la fila.
    Devuelve: (actualizadas, eliminadas)
    """
    s = _s()
    changed = 0
    deleted = 0
    try:
        rows = s.query(MenuImage).all()
        for r in rows:
            raw = (r.path or "").replace("\\", "/")
            base = os.path.basename(raw)
            abs_guess = _abs(os.path.join(MEDIA_DIR, base))
            if os.path.isfile(abs_guess):
                if r.path != abs_guess:
                    r.path = abs_guess
                    changed += 1
            else:
                # archivo no existe en el filesystem -> fila huérfana
                s.delete(r)
                deleted += 1
        s.commit()
        return changed, deleted
    finally:
        s.close()


def ensure_db_and_seed():
    # crea tablas si no existen
    Base.metadata.create_all(engine)
    ensure_schema()
    s = _s()
    try:
        # Seed de menú si está vacío
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
        # Seed de banners si no existen
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
        # Al finalizar seed, normalizamos/limpiamos índices de media
        try:
            normalize_media_records()
        except Exception:
            pass
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


def add_menu_image(uploaded_file) -> str:
    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".png"
    fname = f"menu_{uuid.uuid4().hex}{ext}"
    path = _abs(os.path.join(MEDIA_DIR, fname))  # <-- absoluto
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
    # Normaliza/limpia antes de devolver
    try:
        normalize_media_records()
    except Exception:
        pass
    s = _s()
    try:
        rows = s.query(MenuImage).order_by(MenuImage.created_at.desc()).all()
        return [r.path for r in rows]
    finally:
        s.close()


def fetch_menu_banners() -> List[str]:
    s = _s()
    try:
        rows = s.query(BannerImage).order_by(
            BannerImage.created_at.desc()).all()
        return [r.path for r in rows]
    finally:
        s.close()

# --------- ORDERS ---------


def _compute_total(items: List[Dict]) -> float:
    try:
        return round(sum(float(i.get("qty", 1))*float(i.get("unit_price", 0.0)) for i in items), 2)
    except Exception:
        return 0.0


def create_order_from_chat_ready(client: Dict, items: List[Dict], currency: str) -> Dict:
    s = _s()
    try:
        oid = uuid.uuid4().hex
        total = _compute_total(items)
        now = dt.datetime.utcnow()
        if client.get("delivery_type") == "delivery":
            deadline = now + dt.timedelta(minutes=30)
        else:
            try:
                mins = int(client.get("pickup_eta_min") or 30)
            except Exception:
                mins = 30
            deadline = now + dt.timedelta(minutes=mins)
        o = Order(
            id=oid, client_name=client.get("name", ""), phone=client.get("phone", ""),
            delivery_type=client.get("delivery_type", "pickup"), address=client.get("address", ""),
            pickup_eta_min=int(client.get("pickup_eta_min") or 30), payment_method=client.get("payment_method", ""),
            items_json=json.dumps(items), total=total, currency=currency,
            status="confirmed", created_at=now, priority=10, sla_deadline=deadline, sla_breached=False
        )
        s.add(o)
        s.commit()
        return {"id": oid, "total": total}
    finally:
        s.close()


def fetch_orders_queue() -> List[Dict]:
    s = _s()
    try:
        rows = s.query(Order).order_by(
            Order.priority.asc(), Order.created_at.asc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id, "client_name": r.client_name, "phone": r.phone,
                "delivery_type": r.delivery_type, "address": r.address,
                "pickup_eta_min": r.pickup_eta_min, "payment_method": r.payment_method,
                "items": json.loads(r.items_json or "[]"),
                "total": r.total, "currency": r.currency,
                "status": r.status, "created_at": r.created_at,
                "priority": r.priority, "sla_breached": r.sla_breached
            })
        return out
    finally:
        s.close()


def update_order_status(order_id: str, new_status: str):
    s = _s()
    try:
        o = s.query(Order).get(order_id)
        if o:
            o.status = new_status
            if new_status == "delivered":
                o.priority = 99
            s.commit()
    finally:
        s.close()


def bump_priorities_if_sla_missed() -> int:
    """
    Marca pedidos con SLA vencido como prioridad 1 y sla_breached=True cuando existan
    dichos campos. Ignora filas problemáticas. No rompe la app si el esquema es antiguo.
    """
    s = _s()
    updated = 0
    try:
        now = datetime.now(timezone.utc)
        orders = s.query(Order).filter(Order.status != "delivered").all()
        for o in orders:
            try:
                dd = getattr(o, "sla_deadline", None)
                if not dd:
                    continue
                if getattr(dd, "tzinfo", None) is None:
                    dd = dd.replace(tzinfo=timezone.utc)
                if now <= dd:
                    continue

                changed = False
                if hasattr(o, "priority"):
                    if getattr(o, "priority", None) != 1:
                        o.priority = 1
                        changed = True
                if hasattr(o, "sla_breached"):
                    if not getattr(o, "sla_breached", False):
                        o.sla_breached = True
                        changed = True

                if changed:
                    updated += 1
            except Exception:
                # Fila problemática → se ignora
                continue

        if updated:
            try:
                s.commit()
            except Exception:
                s.rollback()
                return 0
        else:
            s.rollback()
        return updated
    except Exception:
        try:
            s.rollback()
        except Exception:
            pass
        return 0
    finally:
        s.close()

# --------- PENDING QUESTIONS ---------


def create_pending_question(conversation_id: str, question: str, language: str = "es", ttl_seconds: int = 60):
    s = _s()
    try:
        pid = uuid.uuid4().hex
        now = dt.datetime.utcnow()
        exp = now + dt.timedelta(seconds=ttl_seconds)
        p = PendingQuestion(id=pid, conversation_id=conversation_id, question=question,
                            language=language, status="pending", created_at=now, expires_at=exp)
        s.add(p)
        s.commit()
        return pid
    finally:
        s.close()


def fetch_pending_questions() -> List[Dict]:
    s = _s()
    try:
        rows = s.query(PendingQuestion).filter(PendingQuestion.status ==
                                               "pending").order_by(PendingQuestion.created_at.asc()).all()
        return [{"id": r.id, "conversation_id": r.conversation_id, "question": r.question, "language": r.language, "created_at": r.created_at, "expires_at": r.expires_at} for r in rows]
    finally:
        s.close()


def answer_pending_question(pending_id: str, status: str, msg: str = ""):
    s = _s()
    try:
        p = s.query(PendingQuestion).get(pending_id)
        if p and p.status == "pending":
            p.status = status
            p.answer_msg = msg
            s.commit()
            if status in ("approved", "custom"):
                from backend.faq import add_faq
                add_faq(pattern=p.question,
                        answer=msg or "Aprobado por cocina.", language=p.language)
    finally:
        s.close()


def autoapprove_expired_pendings():
    now = dt.datetime.utcnow()
    s = _s()
    try:
        rows = s.query(PendingQuestion).filter(
            PendingQuestion.status == "pending").all()
        for p in rows:
            if p.expires_at and now > p.expires_at:
                p.status = "approved"
                p.answer_msg = "Aprobado (timeout 1 min)."
                from backend.faq import add_faq
                add_faq(pattern=p.question, answer=p.answer_msg,
                        language=p.language)
        s.commit()
    finally:
        s.close()

# --------- EXPORTS / LIMPIEZA ---------


def export_orders_csv() -> str:
    """
    Devuelve CSV como texto con las órdenes (para descarga).
    """
    import io
    import csv
    s = _s()
    try:
        rows = s.query(Order).order_by(Order.created_at.asc()).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "client_name", "phone", "delivery_type", "address", "pickup_eta_min", "payment_method",
                   "items_json", "total", "currency", "status", "created_at", "priority", "sla_deadline", "sla_breached"])
        for r in rows:
            w.writerow([r.id, r.client_name, r.phone, r.delivery_type, r.address, r.pickup_eta_min, r.payment_method, r.items_json, r.total, r.currency,
                       r.status, r.created_at.isoformat() if r.created_at else "", r.priority, r.sla_deadline.isoformat() if r.sla_deadline else "", r.sla_breached])
        return buf.getvalue()
    finally:
        s.close()


def export_pendings_csv() -> str:
    import io
    import csv
    s = _s()
    try:
        rows = s.query(PendingQuestion).order_by(
            PendingQuestion.created_at.asc()).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "conversation_id", "question", "language",
                   "status", "answer_msg", "created_at", "expires_at"])
        for p in rows:
            w.writerow([p.id, p.conversation_id, p.question, p.language, p.status, p.answer_msg or "", p.created_at.isoformat(
            ) if p.created_at else "", p.expires_at.isoformat() if p.expires_at else ""])
        return buf.getvalue()
    finally:
        s.close()


def clear_orders():
    s = _s()
    try:
        s.query(Order).delete()
        s.commit()
    finally:
        s.close()


def clear_pendings():
    s = _s()
    try:
        s.query(PendingQuestion).delete()
        s.commit()
    finally:
        s.close()


def clear_menu():
    s = _s()
    try:
        s.query(MenuItem).delete()
        s.commit()
    finally:
        s.close()


def clear_menu_images():
    s = _s()
    try:
        imgs = s.query(MenuImage).all()
        for im in imgs:
            try:
                if im.path and os.path.isfile(im.path):
                    os.remove(im.path)
            except Exception:
                pass
        s.query(MenuImage).delete()
        s.commit()
    finally:
        s.close()


def clear_banners():
    s = _s()
    try:
        imgs = s.query(BannerImage).all()
        for im in imgs:
            try:
                if im.path and os.path.isfile(im.path):
                    os.remove(im.path)
            except Exception:
                pass
        s.query(BannerImage).delete()
        s.commit()
    finally:
        s.close()


def reset_everything():
    clear_orders()
    clear_pendings()
    clear_menu_images()
    clear_banners()
    clear_menu()
    # FAQ se limpia desde backend/faq.py
