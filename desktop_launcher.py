"""
FamiliDocs - Lanceur Desktop avec fenetre native
Ce script lance l'application Flask dans une fenetre PyWebView (sans navigateur externe).
"""
import os
import sys
import threading
import time

def get_base_path():
    """Retourne le chemin de base, compatible avec PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Execution depuis un executable PyInstaller
        return sys._MEIPASS
    else:
        # Execution normale
        return os.path.dirname(os.path.abspath(__file__))

def setup_paths():
    """Configure les chemins pour l'application"""
    base_path = get_base_path()

    # Ajouter le chemin de base au PYTHONPATH
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    # Charger .env AVANT de configurer les chemins
    from dotenv import load_dotenv
    load_dotenv(os.path.join(base_path, '.env'))

    # Configurer les chemins des templates et static
    os.environ['FLASK_TEMPLATE_FOLDER'] = os.path.join(base_path, 'app', 'templates')
    os.environ['FLASK_STATIC_FOLDER'] = os.path.join(base_path, 'app', 'static')

    # Dossier de donnees (uploads, backups, cles)
    # La BDD est toujours PostgreSQL (partagee web + desktop)
    data_dir = os.path.join(base_path, 'app', 'database')

    os.environ['FAMILIDOCS_UPLOAD_FOLDER'] = os.path.join(data_dir, 'uploads')
    os.environ['FAMILIDOCS_BACKUP_FOLDER'] = os.path.join(data_dir, 'backups')

    for folder in ['uploads', 'backups', 'uploads/avatars']:
        os.makedirs(os.path.join(data_dir, folder), exist_ok=True)

def run_flask_server(app, port):
    """Lance le serveur Flask dans un thread"""
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        threaded=True,
        use_reloader=False
    )

def main():
    """Point d'entree principal"""
    setup_paths()

    # Import de l'application Flask
    from app import create_app
    import webview

    app = create_app()
    port = 5001

    # Lancer Flask dans un thread separe
    flask_thread = threading.Thread(target=run_flask_server, args=(app, port))
    flask_thread.daemon = True
    flask_thread.start()

    # Attendre que le serveur demarre
    time.sleep(1.5)

    # Creer la fenetre native avec PyWebView
    window = webview.create_window(
        title='FamiliDocs - Coffre Administratif Familial',
        url=f'http://127.0.0.1:{port}',
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600),
        text_select=True
    )

    # Lancer l'interface graphique (bloquant)
    webview.start()

if __name__ == '__main__':
    main()
