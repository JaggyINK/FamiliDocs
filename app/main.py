"""
Point d'entrée principal de l'application FamiliDocs
"""
from app import create_app

# Création de l'application
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
