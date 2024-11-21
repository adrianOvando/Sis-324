from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from models.database import get_db_connection
import sqlite3

category_bp = Blueprint('category_routes', __name__)

@category_bp.route('/categories/create', methods=['GET', 'POST'])
def create_category():
    if request.method == 'GET':
        return render_template('createcategory.html')
        
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            
            if not name:
                return jsonify({"error": "El nombre de la categoría es requerido"}), 400
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO categories (name, description) VALUES (?, ?)',
                (name, description or '')
            )
            
            conn.commit()
            return redirect(url_for('category_routes.list_categories'))
            
        except sqlite3.IntegrityError:
            return jsonify({"error": "La categoría ya existe"}), 409
        except Exception as e:
            return jsonify({"error": f"Error creando categoría: {str(e)}"}), 500
        finally:
            conn.close()

@category_bp.route('/categories', methods=['GET'])
def list_categories():
    try:
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM categories').fetchall()
        return render_template('categories.html', categories=categories)
        
    except Exception as e:
        return jsonify({"error": f"Error obteniendo categorías: {str(e)}"}), 500
    finally:
        conn.close()

@category_bp.route('/categories/search', methods=['GET'])
def search_categories():
    try:
        search_term = request.args.get('name', '')
        
        if not search_term:
            return jsonify({"error": "Término de búsqueda requerido"}), 400
            
        conn = get_db_connection()
        categories = conn.execute(
            'SELECT * FROM categories WHERE name LIKE ? OR description LIKE ?',
            (f'%{search_term}%', f'%{search_term}%')
        ).fetchall()
        
        if not categories:
            return jsonify({"message": "No se encontraron categorías"}), 404
            
        return render_template('categories.html', categories=categories, search_term=search_term)
        
    except Exception as e:
        return jsonify({"error": f"Error en la búsqueda: {str(e)}"}), 500
    finally:
        conn.close()