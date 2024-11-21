import sqlite3

DATABASE = 'project.db'

def get_db_connection():
    """Retorna una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas como atributos
    return conn
