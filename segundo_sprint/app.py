from flask import Flask
from routes.user_routes import user_bp
from routes.category_routes import category_bp
from routes.product_routes import product_bp
from models.database import init_db

def create_app():
    app = Flask(__name__, template_folder='templates')
    
    # Registrar los blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(product_bp)
    
    # Inicializar la base de datos al arrancar
    init_db()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)