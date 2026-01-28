"""
Script de lancement FamiliDocs
Lancer avec: python run.py
"""
import sys
import os

# Ajouter le repertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("FamiliDocs - Coffre Administratif Numerique Familial")
    print("=" * 50)
    print("URL: http://localhost:5000")
    print("Admin: admin@familidocs.local / Admin123!")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
