"""
UniMarket Pakistan — Flask Application Entry Point
Run:  python app.py
API:  http://localhost:5000/api/
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

from config import Config
from models import db, bcrypt, create_triggers
from routes.auth     import auth_bp
from routes.products import products_bp
from routes.rentals  import rentals_bp
from routes.reviews  import reviews_bp
from routes.orders   import orders_bp


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    Migrate(app, db)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(rentals_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(orders_bp)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'app': 'UniMarket Pakistan'})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': 'Server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        # Install PostgreSQL trigger for avg_rating auto-update
        create_triggers(db.engine)
    app.run(host="0.0.0.0", debug=True)
