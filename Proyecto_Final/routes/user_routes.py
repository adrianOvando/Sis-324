from flask import Blueprint, request, render_template, jsonify, redirect, url_for
import hashlib
import sqlite3
from models.database import get_db_connection

user_bp = Blueprint('user_routes', __name__)

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')  # Renderiza el formulario de registro

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            data = request.form
            
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
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                (data['username'], hashed_password, data['email'], 'user')
            )
            
            conn.commit()
            return redirect(url_for('category_routes.list_categories_user'))
            
        except sqlite3.IntegrityError:
            return jsonify({"error": "El usuario o email ya existe"}), 409
        except Exception as e:
            return jsonify({"error": f"Error en el registro: {str(e)}"}), 500
        finally:
            if 'conn' in locals():
                conn.close()

from flask import Blueprint, request, jsonify, render_template, redirect, url_for

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
        
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error="Usuario y contraseña son requeridos")
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        ).fetchone()
        
        if user:
            if user['role'] == 'admin':
                return redirect(url_for('category_routes.list_categories'))  
            else:
                return redirect(url_for('category_routes.list_categories_user'))
        else:
            return render_template('login.html', error="Credenciales inválidas")
            
    except Exception as e:
        return render_template('login.html', error=f"Error en el login: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'GET':
        conn = get_db_connection()
        profile = conn.execute('SELECT * FROM user_profiles WHERE user_id = ?', 
                             (1,)).fetchone() 
        return render_template('edit_profile.html', profile=profile)
        
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT OR REPLACE INTO user_profiles (user_id, display_name, description)
                VALUES (?, ?, ?)
            ''', (1, display_name, description))  
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
            
        return redirect(url_for('category_routes.list_categories_user'))

@user_bp.route('/users/list')
def list_users():
    try:
        conn = get_db_connection()
        # Obtener usuarios y sus perfiles
        users = conn.execute('''
            SELECT u.*, up.display_name 
            FROM users u 
            LEFT JOIN user_profiles up ON u.id = up.user_id 
            WHERE u.role != 'admin'
        ''').fetchall()
        
        return render_template('users_list.html', users=users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):  # Agregamos el parámetro aquí
    try:
        conn = get_db_connection()
        # Primero eliminar el perfil si existe
        conn.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
        # Luego eliminar el usuario
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

