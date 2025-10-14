# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 12:37:34 2025

@author: geam9
"""

from __future__ import annotations
import os
import sqlite3
from typing import List, Tuple

"""
Patch/migración defensiva para la base SQLite del demo.
- Usa el mismo engine/ruta que backend.db (normalmente data/app.db)
- Crea tablas que falten (Base.metadata.create_all)
- Agrega columnas (ALTER TABLE) si faltan:
    orders.priority INTEGER DEFAULT 2
    orders.sla_deadline DATETIME NULL
    orders.sla_breached BOOLEAN DEFAULT 0
    pending_questions.status TEXT DEFAULT 'pending'
    menu_items.special_notes TEXT NULL
- Si el menú está vacío, siembra 3 items demo.

Ejecución:
    python -m backend.db_patch
o  python backend/db_patch.py
"""

try:
    from db import (
        engine, Base, SessionLocal,
        MenuItem, Order, PendingQuestion
    )
except Exception as e:
    raise SystemExit(f"[db_patch] No pude importar backend.db: {e}")

# Importa todo desde el módulo oficial de la app

DB_URL = str(engine.url)  # p.ej. sqlite:///data/app.db
if not DB_URL.startswith("sqlite"):
    print("[db_patch] Advertencia: este patch está pensado para SQLite.")
    print(f"[db_patch] URL actual: {DB_URL}")

# Ruta física de la base, asumiendo motor sqlite:///path


def _sqlite_path_from_url(url: str) -> str:
    # sqlalchemy normaliza: sqlite:////abs/path  ó sqlite:///relative/path
    if url.startswith("sqlite:///"):
        p = url[len("sqlite:///"):]
        return p
    elif url.startswith("sqlite://"):
        # in-memory u otros
        return ":memory:"
    return url


DB_PATH = _sqlite_path_from_url(DB_URL)


def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_dir(DB_PATH)
    return sqlite3.connect(DB_PATH)


def _table_columns(conn: sqlite3.Connection, table: str) -> List[Tuple]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    return cur.fetchall()  # (cid, name, type, notnull, dflt_value, pk)


def _has_column(conn: sqlite3.Connection, table: str, col: str) -> bool:
    try:
        cols = _table_columns(conn, table)
        names = [c[1] for c in cols]
        return col in names
    except Exception:
        return False


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
    return cur.fetchone() is not None


def _safe_alter(conn: sqlite3.Connection, sql: str) -> None:
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print(f"[db_patch] ALTER OK: {sql}")
    except Exception as e:
        print(f"[db_patch] ALTER ignorado: {sql} -> {e}")


def create_tables_if_missing() -> None:
    """
    Crea cualquier tabla declarada en los modelos si no existe.
    """
    print(f"[db_patch] Usando DB en: {DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("[db_patch] Base.metadata.create_all ejecutado.")


def add_missing_columns() -> None:
    """
    Agrega columnas que han faltado en distintos entornos de pruebas.
    """
    conn = _connect()
    try:
        # orders.*
        if _table_exists(conn, "orders"):
            if not _has_column(conn, "orders", "priority"):
                _safe_alter(
                    conn, "ALTER TABLE orders ADD COLUMN priority INTEGER DEFAULT 2;")
            if not _has_column(conn, "orders", "sla_deadline"):
                _safe_alter(
                    conn, "ALTER TABLE orders ADD COLUMN sla_deadline DATETIME;")
            if not _has_column(conn, "orders", "sla_breached"):
                _safe_alter(
                    conn, "ALTER TABLE orders ADD COLUMN sla_breached BOOLEAN DEFAULT 0;")
        else:
            print(
                "[db_patch] Tabla 'orders' no existe aún (se creará con Base.metadata).")

        # pending_questions.status
        if _table_exists(conn, "pending_questions"):
            if not _has_column(conn, "pending_questions", "status"):
                _safe_alter(
                    conn, "ALTER TABLE pending_questions ADD COLUMN status TEXT DEFAULT 'pending';")
        else:
            print(
                "[db_patch] Tabla 'pending_questions' no existe aún (se creará con Base.metadata).")

        # menu_items.special_notes
        if _table_exists(conn, "menu_items"):
            if not _has_column(conn, "menu_items", "special_notes"):
                _safe_alter(
                    conn, "ALTER TABLE menu_items ADD COLUMN special_notes TEXT;")
        else:
            print(
                "[db_patch] Tabla 'menu_items' no existe aún (se creará con Base.metadata).")
    finally:
        conn.close()


def seed_demo_if_empty() -> None:
    """
    Si el menú está vacío, siembra 3 ítems demo.
    No duplica si ya existen.
    """
    s = SessionLocal()
    try:
        count = s.query(MenuItem).count()
        if count > 0:
            print(f"[db_patch] Menú ya contiene {
                  count} ítems. No se siembra demo.")
            return

        items = [
            dict(name="Hamburguesa", description="Pan, queso, carne, tomate, lechuga, cebolla y salsa de la casa.",
                 price=5.99, currency="USD", special_notes="contiene gluten"),
            dict(name="Agua", description="Botella de agua servida en vaso, con o sin hielo extra.",
                 price=1.99, currency="USD", special_notes="apto celiacos, sin azúcar"),
            dict(name="Duraznos al jugo", description="Duraznos deshuesados en almíbar con un toque de canela.",
                 price=3.99, currency="USD", special_notes="vegetariano"),
        ]
        for it in items:
            s.add(MenuItem(**it))
        s.commit()
        print("[db_patch] Menú demo sembrado (3 ítems).")
    except Exception as e:
        s.rollback()
        print(f"[db_patch] Error al sembrar demo: {e}")
    finally:
        s.close()


def print_schema() -> None:
    conn = _connect()
    try:
        print("── Esquema de tablas ──")
        for tbl in ("menu_items", "orders", "pending_questions"):
            print(f"\n[{tbl}]")
            if not _table_exists(conn, tbl):
                print("  (no existe)")
                continue
            cols = _table_columns(conn, tbl)
            for c in cols:
                # (cid, name, type, notnull, dflt_value, pk)
                print(f"  - {c[1]}  {c[2]}  DEFAULT={c[4]}")
    finally:
        conn.close()


def main():
    # 1) Crea directorios y tablas que falten
    create_tables_if_missing()
    # 2) Intenta agregar columnas que detectamos en errores previos
    add_missing_columns()
    # 3) Vuelve a crear en caso de que el modelo agregue tablas nuevas
    create_tables_if_missing()
    # 4) Sembrar demo si el menú está vacío
    seed_demo_if_empty()
    # 5) Imprimir esquema
    print_schema()
    print("\n[db_patch] Listo. Si ves todas las columnas, reinicia la app y prueba de nuevo.")


if __name__ == "__main__":
    main()
