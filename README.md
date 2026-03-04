# FamiliDocs

Coffre Administratif Numerique Familial - Projet BTS SIO SLAM

## Description

FamiliDocs est une application web permettant aux familles de centraliser, organiser et securiser leurs documents administratifs, tout en offrant un partage controle entre membres et un espace collaboratif familial complet.

## Fonctionnalites

### Gestion documentaire
- Upload multi-format (PDF, Word, Excel, images, texte) avec limite 16 Mo
- Organisation en dossiers hierarchiques (5 dossiers par defaut a l'inscription)
- Versioning complet avec historique, restauration et telechargement par version
- Tags personnalises avec couleur et association N:N
- Recherche multi-criteres et recherche globale AJAX
- Date de revision obligatoire avec alertes et bouton "Marquer comme revise"

### Partage securise
- Permissions granulaires : lecture, modification, telechargement, re-partage
- Acces temporaire avec expiration (max 90 jours renouvelable)
- Partage multiple (plusieurs utilisateurs a la fois)
- Partage de dossiers complets
- Liens de partage securises avec token, expiration et nombre d'utilisations

### Gestion familiale
- Groupes familiaux avec 8 roles hierarchiques (chef_famille, admin, parent, gestionnaire, enfant, editeur, lecteur, invite)
- Invitations intelligentes : lien accessible sans connexion, redirection vers inscription ou connexion
- Chat familial avec systeme d'annonces
- Assignation de taches aux membres de la famille

### Taches et echeances
- Creation manuelle ou automatique (liee a un document)
- 4 priorites (basse, normale, haute, urgente) et 4 statuts
- Vue calendrier, taches en retard, taches a venir
- Rappels parametrables

### Notifications temps reel
- 11 types de notifications avec priorites
- AJAX dans la navbar avec rafraichissement automatique (60s)
- Support email prepare (simule en developpement)

### Dashboard et administration
- Statistiques par type de fichier, indicateurs cles, graphique d'activite
- Gestion utilisateurs, logs systeme, sauvegardes et restauration

## Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Python / Flask | 3.x / 3.0 |
| ORM | SQLAlchemy | 2.0 |
| Base de donnees | SQLite | 3 |
| Authentification | Flask-Login + bcrypt | 0.6 / 4.1 |
| Chiffrement | cryptography (AES) | 41.0 |
| Protection CSRF | Flask-WTF | 1.2 |
| Frontend | Bootstrap + Icons | 5.3 |
| Tests | pytest | 7.4 |

## Installation

### Prerequis

- Python 3.8 ou superieur
- pip (gestionnaire de paquets Python)

### Etapes

```bash
# 1. Cloner le projet
git clone <url-du-repo>
cd FamiliDocs

# 2. Creer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 3. Installer les dependances
pip install -r requirements.txt

# 4. (Optionnel) Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec vos valeurs

# 5. Lancer l'application
python app/main.py
```

Acceder a l'application : http://localhost:5000

## Compte administrateur par defaut

| Champ | Valeur |
|-------|--------|
| Email | admin@familidocs.local |
| Mot de passe | Admin123! |

> Changez le mot de passe apres la premiere connexion.

## Structure du projet

```
FamiliDocs/
├── app/
│   ├── __init__.py              # Factory Flask + CSRF + securite
│   ├── main.py                  # Point d'entree
│   ├── config/config.py         # Configuration multi-environnement
│   ├── models/                  # 13 modeles SQLAlchemy (15 tables)
│   ├── services/                # 7 services metier
│   ├── routes/                  # 10 blueprints Flask
│   ├── templates/               # 44 templates Jinja2
│   │   └── errors/              # Pages d'erreur (403, 404, 500)
│   ├── static/                  # CSS + JS
│   └── database/                # Base SQLite + uploads
├── tests/                       # 257 tests automatises
├── docs/                        # Documentation technique
│   ├── schema_bdd.md            # Schema BDD (15 tables)
│   ├── documentation_technique.md
│   └── tableau_E5.md
├── .env.example                 # Variables d'environnement
├── requirements.txt             # Dependances Python
├── SUIVI_AMELIORATIONS.md       # Historique des ameliorations
└── README.md
```

## Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec rapport de couverture
pytest tests/ --cov=app -v

# Par categorie
pytest tests/test_models.py -v       # 102 tests modeles
pytest tests/test_services.py -v     # 28 tests services
pytest tests/test_routes.py -v       # 30 tests routes
pytest tests/test_integration.py -v  # 17 tests integration
pytest tests/test_security.py -v     # 14 tests securite
```

**257 tests automatises** couvrant modeles, services, routes, integration et securite.

## Securite

- Hashage bcrypt des mots de passe (cout 12)
- Protection CSRF sur tous les formulaires (Flask-WTF)
- Sessions securisees (HttpOnly, SameSite=Lax)
- En-tetes HTTP : X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Cache-Control
- Limitation des tentatives de connexion (5 max, blocage 15 min)
- Chiffrement AES optionnel des documents sensibles
- Validation des extensions et du content-type des fichiers
- Journalisation de 21 types d'actions (IP + User-Agent)
- Pages d'erreur personnalisees (403, 404, 500)

## Documentation

- [Schema de base de donnees](docs/schema_bdd.md) - 15 tables, MCD, relations
- [Documentation technique](docs/documentation_technique.md) - Architecture, API, deploiement
- [Tableau E5](docs/tableau_E5.md) - Competences BTS SIO couvertes
- [Suivi des ameliorations](SUIVI_AMELIORATIONS.md) - Historique detaille des phases

## Licence

Projet realise dans le cadre du BTS SIO SLAM.
