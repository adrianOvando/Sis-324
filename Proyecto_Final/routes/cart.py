from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify, request
from werkzeug.security import check_password_hash
from functools import wraps
import sqlite3

def get_product_by_id(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        return product
    finally:
        conn.close()



cart_bp = Blueprint('cart', __name__)

def get_db_connection():
    conn = sqlite3.connect('project.db')
    conn.row_factory = sqlite3.Row
    return conn

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder al carrito', 'warning')
            # Guardar la URL a la que el usuario intentaba acceder
            session['next_url'] = request.url
            return redirect(url_for('user_routes.login'))
        return f(*args, **kwargs)
    return decorated_function

@cart_bp.route('/cart')
@login_required
def view_cart():
    conn = get_db_connection()
    try:
        cart_items = conn.execute('''
            SELECT cart_items.*, products.name, products.price, products.image_url
            FROM cart_items 
            JOIN products ON cart_items.product_id = products.id
            WHERE cart_items.user_id = ?
        ''', (session['user_id'],)).fetchall()
        
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        
        return render_template('cart.html', cart_items=cart_items, total=total)
    finally:
        conn.close()

@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT stock FROM products WHERE id = ?', 
                             (product_id,)).fetchone()
        
        if not product or product['stock'] <= 0:
            flash('Producto no disponible', 'error')
            return redirect(url_for('product_routes.product_detail', product_id=product_id))
        
        existing_item = conn.execute('''
            SELECT * FROM cart_items 
            WHERE user_id = ? AND product_id = ?
        ''', (session['user_id'], product_id)).fetchone()
        
        if existing_item:
            conn.execute('''
                UPDATE cart_items 
                SET quantity = quantity + 1
                WHERE user_id = ? AND product_id = ?
            ''', (session['user_id'], product_id))
        else:
            conn.execute('''
                INSERT INTO cart_items (user_id, product_id, quantity)
                VALUES (?, ?, 1)
            ''', (session['user_id'], product_id))
        
        conn.commit()
        update_cart_count()  # Actualizar el contador
        flash('Producto agregado al carrito', 'success')
        return redirect(url_for('cart.view_cart'))
    finally:
        conn.close()

@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    conn = get_db_connection()
    try:
        conn.execute('''
            DELETE FROM cart_items 
            WHERE user_id = ? AND product_id = ?
        ''', (session['user_id'], product_id))
        conn.commit()
        update_cart_count()  # Actualizar el contador
        flash('Producto eliminado del carrito', 'success')
        return redirect(url_for('cart.view_cart'))
    finally:
        conn.close()

@cart_bp.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_quantity(product_id):
    quantity = request.form.get('quantity', type=int)
    if not quantity or quantity < 1:
        flash('Cantidad inválida', 'error')
        return redirect(url_for('cart.view_cart'))
    
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE cart_items 
            SET quantity = ?
            WHERE user_id = ? AND product_id = ?
        ''', (quantity, session['user_id'], product_id))
        conn.commit()
        update_cart_count()  # Actualizar el contador
        flash('Cantidad actualizada', 'success')
        return redirect(url_for('cart.view_cart'))
    finally:
        conn.close()

@cart_bp.route('/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM cart_items WHERE user_id = ?', 
                    (session['user_id'],))
        conn.commit()
        update_cart_count()  # Actualizar el contador
        flash('Carrito vaciado', 'success')
        return redirect(url_for('cart.view_cart'))
    finally:
        conn.close()



