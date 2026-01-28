# FamiliDocs

Coffre Administratif Numerique Familial - Projet BTS SIO SLAM

## Description

FamiliDocs est une application web permettant aux familles de centraliser, organiser et securiser leurs documents administratifs, tout en offrant un partage controle entre membres de confiance.

## Fonctionnalites

- **Gestion des utilisateurs** : Inscription, connexion, roles (admin/utilisateur/personne de confiance)
- **Gestion documentaire** : Upload, organisation en dossiers, recherche, filtrage
- **Partage securise** : Permissions granulaires, acces temporaire, revocation
- **Taches et echeances** : Rappels automatiques, priorites, calendrier
- **Administration** : Tableau de bord, logs, sauvegardes
- **Securite** : Hashage bcrypt, sessions securisees, journalisation

## Technologies

- **Backend** : Python 3.x, Flask 3.0
- **Base de donnees** : SQLite, SQLAlchemy
- **Frontend** : HTML5, CSS3, Bootstrap 5, JavaScript
- **Securite** : bcrypt, cryptography

## Installation

### Prerequis

- Python 3.8 ou superieur
- pip (gestionnaire de paquets Python)

### Etapes

1. **Cloner le projet**
```bash
git clone <url-du-repo>
cd FamiliDocs
```

2. **Creer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Installer les dependances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
python app/main.py
```

5. **Acceder a l'application**
Ouvrir un navigateur a l'adresse : http://localhost:5000

## Compte administrateur par defaut

- **Email** : admin@familidocs.local
- **Mot de passe** : Admin123!

> Important : Changez ce mot de passe apres la premiere connexion !

## Structure du projet

```
familidocs/
├── app/
│   ├── __init__.py         # Factory Flask
│   ├── main.py             # Point d'entree
│   ├── config/             # Configuration
│   ├── models/             # Modeles SQLAlchemy
│   ├── routes/             # Routes/Controleurs
│   ├── services/           # Logique metier
│   ├── templates/          # Templates HTML
│   ├── static/             # CSS, JS
│   └── database/           # Base SQLite
├── backups/                # Sauvegardes
├── docs/                   # Documentation
│   ├── cahier_des_charges.md
│   ├── schema_bdd.md
│   └── tableau_E5.md
├── tests/                  # Tests unitaires
├── requirements.txt        # Dependances
└── README.md
```

## Tests

Lancer les tests avec pytest :

```bash
pytest tests/ -v
```

## Documentation

- [Cahier des charges](docs/cahier_des_charges.md)
- [Schema de base de donnees](docs/schema_bdd.md)
- [Tableau E5](docs/tableau_E5.md)

## Utilisation

### Connexion
1. Accedez a la page de connexion
2. Entrez vos identifiants
3. Vous etes redirige vers le tableau de bord

### Ajouter un document
1. Cliquez sur "Ajouter un document"
2. Selectionnez un fichier
3. Renseignez les metadonnees
4. Cliquez sur "Ajouter"

### Partager un document
1. Ouvrez le document
2. Cliquez sur "Partager"
3. Selectionnez l'utilisateur
4. Definissez les permissions
5. Validez

### Gerer les taches
1. Accedez a "Taches"
2. Creez une nouvelle tache
3. Associez-la a un document si necessaire
4. Definissez la priorite et l'echeance

## Securite

- Mots de passe hashes avec bcrypt
- Sessions securisees avec Flask-Login
- Protection CSRF activee
- Validation des entrees utilisateur
- Journalisation des actions sensibles

## Contribution

1. Fork le projet
2. Creez une branche (`git checkout -b feature/amelioration`)
3. Committez (`git commit -m 'Ajout fonctionnalite'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## Licence

Projet realise dans le cadre du BTS SIO SLAM.

## Auteur

Projet FamiliDocs - BTS SIO SLAM
