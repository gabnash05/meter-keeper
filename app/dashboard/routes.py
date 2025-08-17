from flask import Blueprint, render_template
from flask_login import login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard", template_folder="templates")

@dashboard_bp.route("/")
@login_required
def index():
    # Placeholder: later this will show charts/analytics
    return render_template("dashboard/index.html")
