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
        # Crear tabla de usuarios si no existe
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
        # Verificar si la columna role existe
        columns = cursor.execute("PRAGMA table_info(users)").fetchall()
        role_exists = any(column[1] == 'role' for column in columns)
        
        if not role_exists:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        
        # Lista de usuarios admin por defecto con el email correcto para adrian
        default_admins = [
            ('bryan', 'bryan@example.com'),
            ('adrian', 'adria@gmail.com')  # Email corregido
        ]
        
        # Asegurarse de que los usuarios admin existan y tengan el rol correcto
        for admin_user, admin_email in default_admins:
            # Verificar si el usuario ya existe
            existing_user = cursor.execute(
                "SELECT * FROM users WHERE username = ?", 
                (admin_user,)
            ).fetchone()
            
            if not existing_user:
                # Si no existe, crear el usuario con una contraseña hasheada
                import hashlib
                default_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO users (username, password, email, role)
                    VALUES (?, ?, ?, 'admin')
                ''', (admin_user, default_password, admin_email))
            else:
                # Si existe, asegurarse de que tenga rol de admin
                cursor.execute('''
                    UPDATE users SET role = 'admin'
                    WHERE username = ?
                ''', (admin_user,))
        
        # Resto de la inicialización de la base de datos...
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE (user_id, product_id)  -- Asegura que un producto no se repita en el carrito del mismo usuario
            )
        ''')
        
        conn.commit()
        print("Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")
    finally:
        conn.close()
