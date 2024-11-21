from flask import Blueprint, request, jsonify, render_template
from models.database import get_db_connection

product_bp = Blueprint('product_routes', __name__)

@product_bp.route('/products', methods=['GET'])
def list_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        products = cursor.execute('SELECT * FROM products').fetchall()
        return render_template('products.html', products=products)
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
        return render_template('createproduct.html')
    
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
            return jsonify({"message": "Producto creado exitosamente"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
