import os
from flask import Flask, send_from_directory
from config import Config
from models import db
from routes.polish import polish_bp


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(polish_bp, url_prefix='/api')

    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')

    @app.route('/')
    def index():
        return send_from_directory(static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_files(path):
        file_path = os.path.join(static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(static_folder, path)
        return send_from_directory(static_folder, 'index.html')

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app


app = create_app()
