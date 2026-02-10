#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = 'data/sistema.db'

def patch_db():
    if not os.path.exists(DB_PATH):
        print("Base de datos no encontrada. Saltando parche.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("ALTER TABLE proyectos ADD COLUMN version INTEGER DEFAULT 1")
        conn.commit()
        print("✓ Columna 'version' agregada a tabla 'proyectos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("! La columna 'version' ya existe.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    patch_db()
