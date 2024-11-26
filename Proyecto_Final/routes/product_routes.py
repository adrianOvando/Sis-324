from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from models.database import get_db_connection

product_bp = Blueprint('product_routes', __name__)

@product_bp.route('/products/<int:category_id>', methods=['GET'])
def list_products(category_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        category = cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,)).fetchone()
        category_name = category['name'] if category else 'Categoría no encontrada'
        products = cursor.execute('SELECT * FROM products WHERE category_id = ?', (category_id,)).fetchall()
        is_admin = True
        if is_admin:
            return render_template('listproducts.html', products=products, category_name=category_name)
        else:
            return render_template('listproducts_user.html', products=products, category_name=category_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@product_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        product = cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        return render_template('product_detail.html', product=product)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@product_bp.route('/product/create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'GET':
        # Obtener categorías para el formulario
        conn = get_db_connection()
        cursor = conn.cursor()
        categories = cursor.execute('SELECT * FROM categories').fetchall()  
        return render_template('createproduct.html', categories=categories)
    
    if request.method == 'POST':
        try:
            data = request.form
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(''' 
                INSERT INTO products (name, description, price, stock, category_id, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['description'],
                float(data['price']),
                int(data['stock']),
                int(data['category_id']) if data.get('category_id') else None,
                data.get('image_url', '')
            ))
            
            conn.commit()

            # Redirigir a la lista de productos de la categoría
            return redirect(url_for('product_routes.list_products', category_id=data['category_id']))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

@product_bp.route('/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        flash("Producto eliminado exitosamente", "success")
    except Exception as e:
        flash(f"Error al eliminar el producto: {str(e)}", "error")
    finally:
        conn.close()
    
    return redirect(url_for('product_routes.list_products', category_id=1))  # Cambia el ID de categoría según sea necesario


