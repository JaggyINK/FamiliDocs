# lancement FamiliDocs - python run.py
import sys
import os

# path python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("FamiliDocs - Coffre Administratif Numerique Familial")
    print("=" * 50)
    print("URL: http://localhost:5000")
    print("Lancez 'python seed_demo_data.py' pour creer les comptes demo")
    print("=" * 50)
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    # par defaut : ecoute uniquement en local (127.0.0.1)
    # mettre FLASK_HOST=0.0.0.0 pour rendre accessible sur le reseau (en prod : Gunicorn + Nginx)
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    app.run(debug=debug, host=host, port=5000)
