#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = 'data/sistema.db'

def patch_proyectos():
    if not os.path.exists(DB_PATH):
        print("Base de datos no encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(proyectos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = [
        ('razon_kill', 'TEXT'),
        ('fecha_kill', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                conn.execute(f"ALTER TABLE proyectos ADD COLUMN {col_name} {col_type}")
                print(f"✓ Columna '{col_name}' agregada.")
            except Exception as e:
                print(f"Error agregando '{col_name}': {e}")
        else:
            print(f"! La columna '{col_name}' ya existe.")
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    patch_proyectos()
