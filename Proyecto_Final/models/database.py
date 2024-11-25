import sqlite3
from flask import Blueprint

DATABASE = 'project.db'

def get_db_connection():
    """Retorna una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = get_db_connection()
    try:
        # Crear tabla de usuarios
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor = conn.cursor()
        columns = cursor.execute("PRAGMA table_info(users)").fetchall()
        role_exists = any(column[1] == 'role' for column in columns)
        
        if not role_exists:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            
        cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'bryan'")
        cursor.execute("UPDATE users SET role = 'user' WHERE username = 'test_user'")
        
        
        
        # Crear tabla de categorías
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Crear tabla de productos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                category_id INTEGER,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                display_name TEXT NOT NULL DEFAULT 'User1',
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")
    finally:
        conn.close()

