import os
import sqlite3
from flask import Flask, g, current_app, request
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key"),
        DATABASE=os.path.join(app.instance_path, "app.db"),  # SQLite file path
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB upload limit
    )

    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    login_manager.init_app(app)

    app.teardown_appcontext(close_db)

    from .auth.routes import auth_bp
    from .readings.routes import readings_bp
    from .dashboard.routes import dashboard_bp
    from .alerts.routes import alerts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(readings_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(alerts_bp)

    with app.app_context():
        init_db()
    
    return app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

################# Define table schema here ################# 
def init_db():
    db = get_db()

    schema_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'migrations',
        'schema.sql'
    )
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()

