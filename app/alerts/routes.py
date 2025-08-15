from flask import Blueprint
alerts_bp = Blueprint("alerts", __name__, url_prefix="/alerts", template_folder="templates")

@alerts_bp.route("/alerts")
def upload():
    return "ALERTS"