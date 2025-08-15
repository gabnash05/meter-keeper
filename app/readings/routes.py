from flask import Blueprint
readings_bp = Blueprint("readings", __name__, url_prefix="/readings", template_folder="templates")

@readings_bp.route("/upload")
def upload():
    return "UPLOAD PAGE"