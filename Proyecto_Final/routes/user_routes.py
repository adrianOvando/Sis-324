from flask import Blueprint, request, render_template, jsonify, redirect, url_for, session, flash
import hashlib
import sqlite3
from models.database import get_db_connection
from functools import wraps

user_bp = Blueprint('user_routes', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión', 'warning')
            return redirect(url_for('user_routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def update_cart_count():
    """Actualiza el contador del carrito en la sesión"""
    if 'user_id' in session:
        conn = get_db_connection()
        try:
            count = conn.execute('''
                SELECT SUM(quantity) as total
                FROM cart_items
                WHERE user_id = ?
            ''', (session['user_id'],)).fetchone()
            session['cart_count'] = count['total'] if count['total'] else 0
        finally:
            conn.close()

def calcular_cuf(datos):
    # Completar campos con ceros a la izquierda
    nit_emisor = datos['nit_emisor'].zfill(15)
    fecha_hora = datos['fecha_hora']
    sucursal = datos['sucursal'].zfill(4)
    modalidad = datos['modalidad']
    tipo_emision = datos['tipo_emision']
    tipo_factura = datos['tipo_factura']
    tipo_documento = datos['tipo_documento'].zfill(2)
    numero_factura = datos['numero_factura'].zfill(10)
    pos = datos['pos'].zfill(4)

    # Concatenar campos
    cadena = f"{nit_emisor}{fecha_hora}{sucursal}{modalidad}{tipo_emision}{tipo_factura}{tipo_documento}{numero_factura}{pos}"

    # Obtener módulo 11
    modulo_11 = sum(int(d) for d in cadena) % 11
    cadena += str(modulo_11)

    # Aplicar Base 16
    cuf_base16 = hashlib.sha256(cadena.encode()).hexdigest().upper()

    # Concatenar con código de control
    codigo_control = "87D7B8EE1D88E74"  # Este valor debería ser dinámico
    cuf_final = f"{cuf_base16}{codigo_control}"

    return cuf_final

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        try:
            data = request.form
            
            required_fields = ['username', 'password', 'email']
            if not all(field in data for field in required_fields):
                flash("Todos los campos son obligatorios", "error")
                return redirect(url_for('user_routes.register'))
            
            if '@' not in data['email']:
                flash("Formato de email inválido", "error")
                return redirect(url_for('user_routes.register'))
            
            hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                (data['username'], hashed_password, data['email'], 'user')
            )
            
            conn.commit()
            flash("Registro exitoso. Por favor inicia sesión.", "success")
            return redirect(url_for('user_routes.login'))
            
        except sqlite3.IntegrityError:
            flash("El usuario o email ya existe", "error")
            return redirect(url_for('user_routes.register'))
        except Exception as e:
            flash(f"Error en el registro: {str(e)}", "error")
            return redirect(url_for('user_routes.register'))
        finally:
            if 'conn' in locals():
                conn.close()

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
        
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Usuario y contraseña son requeridos", "error")
            return redirect(url_for('user_routes.login'))
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        ).fetchone()
        
        if user:
            # Guardar datos de usuario en la sesión
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            # Actualizar contador del carrito
            update_cart_count()
            
            # Redirigir según el rol
            if user['role'] == 'admin':
                return redirect(url_for('category_routes.list_categories'))
            else:
                # Verificar si hay una URL guardada para redirección
                next_url = session.pop('next_url', None)
                if next_url:
                    return redirect(next_url)
                return redirect(url_for('category_routes.list_categories_user'))
        else:
            flash("Credenciales inválidas", "error")
            return redirect(url_for('user_routes.login'))
            
    except Exception as e:
        flash(f"Error en el login: {str(e)}", "error")
        return redirect(url_for('user_routes.login'))
    finally:
        if 'conn' in locals():
            conn.close()

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente", "success")
    return redirect(url_for('user_routes.login'))

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'GET':
        conn = get_db_connection()
        profile = conn.execute('SELECT * FROM user_profiles WHERE user_id = ?', 
                             (session['user_id'],)).fetchone()
        return render_template('edit_profile.html', profile=profile)
        
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT OR REPLACE INTO user_profiles (user_id, display_name, description)
                VALUES (?, ?, ?)
            ''', (session['user_id'], display_name, description))
            conn.commit()
            flash("Perfil actualizado exitosamente", "success")
        except Exception as e:
            flash(f"Error actualizando el perfil: {str(e)}", "error")
        finally:
            conn.close()
            
        return redirect(url_for('category_routes.list_categories_user'))

@user_bp.route('/users/list')
@login_required
def list_users():
    if session.get('role') != 'admin':
        flash("No tienes permiso para acceder a esta página", "error")
        return redirect(url_for('category_routes.list_categories_user'))

    try:
        conn = get_db_connection()
        users = conn.execute('''
            SELECT u.*, up.display_name 
            FROM users u 
            LEFT JOIN user_profiles up ON u.id = up.user_id 
            WHERE u.role != 'admin'
        ''').fetchall()
        
        return render_template('users_list.html', users=users)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('category_routes.list_categories'))
    finally:
        conn.close()

@user_bp.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({"success": False, "error": "No autorizado"}), 403

    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

@user_bp.route('/generar_cuf', methods=['POST'])
def generar_cuf():
    datos = request.json
    cuf = calcular_cuf(datos)
    return jsonify({"cuf": cuf})