import os
import uuid
import sqlite3
import mimetypes
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, abort, Response
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from db.core import get_db 
from app.readings.ocr import allowed_file, extract_kwh

readings_bp = Blueprint("readings", __name__, url_prefix="/readings", template_folder="templates")

def uploads_dir() -> str:
    """Get the upload directory path"""
    return current_app.config["UPLOAD_FOLDER"]

def secure_file_headers(mime: str) -> dict:
    """Generate secure headers for file responses"""
    return {
        "Cache-Control": "private, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
        "Content-Type": mime or "application/octet-stream",
    }

@readings_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded", "error")
            return redirect(request.url)

        file = request.files["file"]
        
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return redirect(request.url)

        try:
            # Generate unique filename while preserving extension
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            filename = secure_filename(unique_name)
            save_path = os.path.join(uploads_dir(), filename)
            
            # Ensure upload directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)

            try:
                kwh_value = extract_kwh(save_path)
            except ValueError as e:
                flash(f"OCR error: {str(e)}", "error")
                os.remove(save_path)
                return redirect(request.url)
            except Exception as e:
                flash("Failed to process meter reading", "error")
                os.remove(save_path)
                return redirect(request.url)

            # Store relative path in session for security
            session["pending_reading"] = {
                "image_filename": filename,
                "kwh": kwh_value
            }

            return redirect(url_for("readings.confirm"))
        
        except (IOError, OSError) as e:
            flash("Failed to save uploaded file", "error")
            return redirect(request.url)

    return render_template("readings/upload.html")

@readings_bp.route("/confirm", methods=["GET", "POST"])
def confirm():
    pending = session.get("pending_reading")
    if not pending:
        flash("No reading to confirm", "error")
        return redirect(url_for("readings.upload"))

    if request.method == "POST":
        kwh = request.form.get("kwh")
        try:
            kwh = float(kwh)
        except ValueError:
            flash(f"Invalid kWh value: {kwh}", "error")
            return redirect(request.url)
        
        # Security check - verify file exists and is in uploads directory
        save_path = safe_join(uploads_dir(), pending["image_filename"])
        if not save_path or not os.path.exists(save_path):
            abort(404)

        try:
            db = get_db()
            db.execute(
                "INSERT INTO meter_readings (user_id, kwh, image_path) VALUES (?, ?, ?)",
                (current_user.id, kwh, pending["image_filename"]),
            )
            db.commit()
        except sqlite3.Error as e:
            current_app.logger.error(f"Database error: {str(e)}")
            abort(500)

        session.pop("pending_reading", None)
        flash("Reading saved successfully", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("readings/confirm.html", pending=pending)

@readings_bp.route("/pending-image")
def pending_image():
    """Serve the pending image during confirmation"""
    pending = session.get("pending_reading")
    if not pending:
        abort(404)

    filename = pending.get("image_filename")
    if not filename:
        abort(404)

    path = safe_join(uploads_dir(), filename)
    if not path or not os.path.isfile(path):
        abort(404)

    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        data = f.read()
    headers = secure_file_headers(mime)
    return Response(data, headers=headers)

@readings_bp.route("/image/<int:reading_id>")
def reading_image(reading_id: int):
    """Serve an image for a saved reading if the current user owns it"""
    if not current_user.is_authenticated:
        abort(403)

    db = get_db()
    row = db.execute(
        "SELECT user_id, image_path FROM meter_readings WHERE id = ?",
        (reading_id,),
    ).fetchone()

    if not row:
        abort(404)
    if row["user_id"] != current_user.id:
        abort(403)

    filename = row["image_path"]
    path = safe_join(uploads_dir(), filename)
    if not path or not os.path.isfile(path):
        abort(404)

    mime, _ = mimetypes.guess_type(path)
    with open(path, "rb") as f:
        data = f.read()
    headers = secure_file_headers(mime)
    return Response(data, headers=headers)