from flask import Blueprint, request, jsonify
import sqlite3
import hashlib
from models.database import get_db_connection

user_bp = Blueprint('user_routes', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['username', 'password', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Todos los campos son obligatorios"}), 400
            
        # Validar formato de email básico
        if '@' not in data['email']:
            return jsonify({"error": "Formato de email inválido"}), 400
            
        # Hash de la contraseña
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar nuevo usuario
        cursor.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            (data['username'], hashed_password, data['email'])
        )
        
        conn.commit()
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "username": data['username']
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "El usuario o email ya existe"
        }), 409
    except Exception as e:
        return jsonify({
            "error": f"Error en el registro: {str(e)}"
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"error": "Usuario y contraseña son requeridos"}), 400
            
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (data['username'], hashed_password)
        ).fetchone()
        
        if user:
            return jsonify({
                "message": "Login exitoso",
                "username": user['username']
            }), 200
        else:
            return jsonify({"error": "Credenciales inválidas"}), 401
            
    except Exception as e:
        return jsonify({"error": f"Error en el login: {str(e)}"}), 500
    finally:
        if 'conn' in locals():
            conn.close()