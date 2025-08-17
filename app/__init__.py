import os
from flask import Flask
from flask_login import LoginManager
from db.core import init_db, get_db, close_db
from .auth.user_model import get_user_by_id

login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login passes id as str
    try:
        uid = int(user_id)
    except ValueError:
        return None
    return get_user_by_id(uid)

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-key"),
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH",
            os.path.join(app.instance_path, "app.sqlite"),
        ),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB
        WTF_CSRF_TIME_LIMIT=None,
    )

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    login_manager.init_app(app)

    app.teardown_appcontext(close_db)

    # Blueprints
    from .auth.routes import auth_bp
    from .readings.routes import readings_bp
    from .dashboard.routes import dashboard_bp
    from .alerts.routes import alerts_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(readings_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(alerts_bp)

    # Minimal index (redirect to dashboard or login)
    @app.route("/")
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))
    
    with app.app_context():
        init_db()

    return app
