# routes telechargement de l'application desktop (.exe)
import os
from flask import Blueprint, render_template, send_from_directory, current_app, abort
from flask_login import login_required, current_user

from app.models import db
from app.models.log import Log

download_bp = Blueprint('download', __name__)


def _desktop_app_path():
    """chemin (dossier, fichier) du .exe desktop sur le volume persistant"""
    folder = current_app.config['DOWNLOAD_FOLDER']
    filename = current_app.config['DESKTOP_APP_FILENAME']
    return folder, filename


@download_bp.route('/telecharger')
@login_required
def desktop_app():
    """page de telechargement de l'application de bureau"""
    folder, filename = _desktop_app_path()
    file_path = os.path.join(folder, filename)

    available = os.path.isfile(file_path)
    size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 1) if available else None

    return render_template(
        'telecharger.html',
        available=available,
        filename=filename,
        size_mb=size_mb
    )


@download_bp.route('/telecharger/application')
@login_required
def desktop_app_file():
    """sert le fichier .exe en telechargement"""
    folder, filename = _desktop_app_path()

    if not os.path.isfile(os.path.join(folder, filename)):
        abort(404)

    Log.create_log(
        user_id=current_user.id,
        action='desktop_app_download',
        details=f"Telechargement de l'application de bureau '{filename}'"
    )
    db.session.commit()

    return send_from_directory(folder, filename, as_attachment=True)
