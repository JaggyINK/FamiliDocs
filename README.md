# FamiliDocs

> **Coffre-fort numerique familial** — projet BTS SIO SLAM 2025/2026

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Tests](https://img.shields.io/badge/tests-307%20passing-success)
![License](https://img.shields.io/badge/license-Educational-lightgrey)

Application **web + bureau** qui permet a une famille de centraliser, organiser et partager
de maniere securisee ses documents administratifs (factures, identites, contrats, sante...).

---

## Sommaire

1. [Apercu fonctionnel](#apercu-fonctionnel)
2. [Demarrage rapide](#demarrage-rapide)
3. [Comptes de test](#comptes-de-test)
4. [Stack technique](#stack-technique)
5. [Architecture](#architecture)
6. [Documentation](#documentation)
7. [Tests](#tests)
8. [Securite](#securite)
9. [Application desktop](#application-desktop)
10. [Diagrammes UML](#diagrammes-uml)
11. [Licence](#licence)

---

## Apercu fonctionnel

| Fonctionnalite | Description |
|---|---|
| **Documents** | Upload multi-format (16 Mo max), versionnement, tags couleur, recherche multicritere + AJAX |
| **Dossiers** | Hierarchiques (5 par defaut a l'inscription), partage de dossiers complets |
| **Partage** | 4 droits granulaires (lire / modifier / telecharger / re-partager) avec expiration (max 90 j) |
| **Familles** | 8 roles hierarchiques (responsable, admin, parent, gestionnaire, enfant, editeur, lecteur, invite) |
| **Chat familial** | Messagerie au sein de la famille avec annonces |
| **Taches** | 4 priorites, 4 statuts, vue calendrier, assignation entre membres |
| **Notifications** | 12 types, AJAX temps reel, support email |
| **2FA TOTP** | QR code scannable avec Google Authenticator / Authy |
| **Chiffrement AES** | Auto pour les documents prives (Fernet) |
| **RGPD** | Export JSON, droit a l'oubli (cascade), retention logs 180j |
| **Admin** | Logs (27 actions), sauvegardes ZIP, gestion utilisateurs |
| **Desktop** | Application native CustomTkinter, **meme base PostgreSQL** que le web |

---

## Demarrage rapide

### Prerequis
- Python 3.10+ (recommande 3.12)
- PostgreSQL 16
- Git

### Installation

```bash
# 1. Cloner
git clone <url-du-repo> FamiliDocs
cd FamiliDocs

# 2. Environnement virtuel
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Dependances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Editer .env : DATABASE_URL=postgresql://jagadmin:pass@localhost:5432/familidocs

# 5. Base PostgreSQL (psql)
sudo -u postgres psql -c "CREATE USER jagadmin WITH PASSWORD 'pass';"
sudo -u postgres psql -c "CREATE DATABASE familidocs OWNER jagadmin;"

# 6. Donnees de demo
python seed_demo_data.py

# 7. Lancement web
python run.py
# Ouvrir http://localhost:5000

# 8. Lancement desktop (autre terminal)
python desktop_app.py
```

Guide detaille : [docs/INSTALLATION.md](docs/INSTALLATION.md)

---

## Comptes de test

Apres `python seed_demo_data.py`, **5 comptes** sont disponibles avec le meme mot de passe `Demo2024!` :

| Email | Role applicatif | Role familial | Description |
|---|---|---|---|
| `jean.dupont@email.com` | admin | Papa - Responsable | 8 documents, 3 taches, partage avec Marie |
| `marie.dupont@email.com` | admin | Maman - Responsable | 5 documents, 2 taches |
| `lucas.dupont@email.com` | user | Fils - Editeur | 4 documents (scolaires) |
| `emma.dupont@email.com` | user | Fille - Lecteur | 2 documents |
| `pierre.dupont@email.com` | user | Grand-Pere - Parent | 1 document (sante) |

> Les parents Jean et Marie ont les droits administrateur de l'application.

Donnees de demo creees : 20 documents, 19 partages, 9 taches, 14 messages chat, 10 notifications.

Plus de details : [`DEMO_IDENTIFIANTS.txt`](DEMO_IDENTIFIANTS.txt)

---

## Stack technique

| Composant | Technologie | Version |
|---|---|---|
| Langage | Python | 3.12 |
| Framework web | Flask | 3.0 |
| ORM | SQLAlchemy | 2.0 |
| Base de donnees | PostgreSQL | 16 |
| Authentification | Flask-Login + bcrypt | 0.6 / 4.1 |
| Chiffrement | cryptography (Fernet AES) | 41.0 |
| 2FA | pyotp + qrcode | 2.9 / 7.4 |
| Protection CSRF | Flask-WTF | 1.2 |
| Frontend | Bootstrap | 5.3 |
| Application bureau | CustomTkinter | 5.2 |
| Compilation .exe | PyInstaller | 6.11 |
| Tests | pytest | 7.4 |
| Migrations BDD | Flask-Migrate / Alembic | 4.0 |
| Scheduler | schedule | 1.2 |

---

## Architecture

Patron **MVC + Service Layer** :

```
Navigateur / Desktop
        |
        v
+-------------------+
|  Routes Flask     |  10 blueprints (auth, documents, taches, famille...)
|  (Controleurs)    |
+-------------------+
        |
        v
+-------------------+
|  Services metier  |  8 services (auth, document, permission, encryption,
|                   |    notification, search, backup, scheduler)
+-------------------+
        |
        v
+-------------------+
|  Modeles ORM      |  13 modeles SQLAlchemy = 14 tables PostgreSQL
+-------------------+
        |
        v
+-------------------+
|  PostgreSQL       |  meme BDD pour web et desktop
+-------------------+
```

Diagramme detaille : [`docs/uml/composants.png`](docs/uml/composants.png)

### Chiffres cles

- **13 modeles** SQLAlchemy = **14 tables** (13 entites + 1 association `document_tags`)
- **10 blueprints** Flask
- **8 services** metier
- **50 templates** Jinja2
- **96 endpoints** HTTP
- **27 types** d'actions journalisees
- **12 types** de notifications
- **8 roles** familiaux
- **307 tests** automatises (100% passent) repartis en 14 fichiers

---

## Documentation

### Pour les utilisateurs
- [Manuel utilisateur](docs/MANUEL_UTILISATEUR.md) — guide pas a pas
- [Identifiants de demo](DEMO_IDENTIFIANTS.txt) — comptes + scenario

### Pour les developpeurs
- [Documentation technique complete](docs/DOCUMENTATION_COMPLETE.md) — architecture detaillee
- [Schema de BDD](docs/schema_bdd.md) — MCD + analyse normalisation 3FN
- [Plan de tests](docs/PLAN_TESTS.md) — strategie de tests
- [Guide d'installation](docs/INSTALLATION.md) — dev + production
- [Glossaire](docs/GLOSSAIRE.md) — 40+ termes techniques

### Pour le BTS SIO
- [Cahier des charges](docs/cahier_des_charges.md)
- [Tableau competences E5](docs/tableau_E5.md)
- [Politique de securite](docs/POLITIQUE_SECURITE.md)
- [Conformite RGPD](docs/CONFORMITE_RGPD.md)
- [Analyse de risques (EBIOS)](docs/ANALYSE_RISQUES.md)
- [Preparation oral E5](ORAL_E5_PREPARATION.md)
- [Revision BTS SIO](REVISION_BTS_SIO.md)
- [Changelog v1.0 -> v2.3](CHANGELOG.md)

---

## Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec rapport de couverture
pytest tests/ --cov=app -v

# Par fichier (14 disponibles)
pytest tests/test_models.py -v
pytest tests/test_services.py -v
pytest tests/test_routes.py -v
pytest tests/test_integration.py -v
pytest tests/test_security.py -v
pytest tests/test_rgpd.py -v
pytest tests/test_encryption.py -v
pytest tests/test_families.py -v
pytest tests/test_chat.py -v
pytest tests/test_admin.py -v
pytest tests/test_documents.py -v
pytest tests/test_versions.py -v
pytest tests/test_tags.py -v
pytest tests/test_share_links.py -v
```

Resultat attendu : **307 passed** en ~75s.

Strategie complete : [docs/PLAN_TESTS.md](docs/PLAN_TESTS.md)

---

## Securite

L'application implemente une securite **multi-couches** :

- **Mots de passe** : haches bcrypt avec sel aleatoire
- **2FA TOTP** (RFC 6238) optionnelle, QR code Google Authenticator
- **Rate limiting** : 5 tentatives -> blocage 15 minutes
- **Sessions** : HttpOnly + SameSite=Lax + Secure (prod) + duree 2h
- **CSRF** : token Flask-WTF sur tous les formulaires
- **Chiffrement AES** : automatique pour les documents prives (Fernet)
- **7 en-tetes HTTP** : CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Cache-Control, X-XSS-Protection
- **Path traversal** : protection avec `os.path.realpath()`
- **Anti-enumeration** : message d'erreur identique pour email inexistant ou mot de passe incorrect
- **Validation MIME + extension** a chaque upload
- **Logs RGPD** : 27 types d'actions, retention 180 jours

Document complet : [docs/POLITIQUE_SECURITE.md](docs/POLITIQUE_SECURITE.md)

---

## Application desktop

L'application bureau est ecrite en **CustomTkinter** et utilise la **meme base PostgreSQL** que le web. Les deux versions sont synchronisees en temps reel.

```bash
# Mode script
python desktop_app.py

# Mode executable (Windows uniquement)
build_exe.bat
.\dist\FamiliDocs.exe
```

Fonctionnalites desktop :
- Tableau de bord avec statistiques
- Documents : dossiers en grille, tri, filtres, recherche
- Partages avec droits, duree, revocation
- Taches : 3 onglets (mes taches, assignees par moi, terminees)
- Famille : membres, dashboard avec progression par membre
- Chat familial integre
- Gestion des roles (responsables uniquement)

---

## Diagrammes UML

11 diagrammes couvrant tous les aspects du projet :

| Diagramme | Type | Fichier |
|---|---|---|
| Cas d'usage | Comportemental | [`cas_usage.png`](docs/uml/cas_usage.png) |
| Classes | Structurel | [`classes.png`](docs/uml/classes.png) |
| Modele Conceptuel de Donnees (MCD) | Donnees | [`mcd.png`](docs/uml/mcd.png) |
| Composants | Architecture | [`composants.png`](docs/uml/composants.png) |
| Paquetages | Modules | [`paquetages.png`](docs/uml/paquetages.png) |
| Deploiement | Infrastructure | [`deploiement.png`](docs/uml/deploiement.png) |
| Sequence : upload + partage | Comportemental | [`sequence_upload_partage.png`](docs/uml/sequence_upload_partage.png) |
| Sequence : login + 2FA | Comportemental | [`sequence_login_2fa.png`](docs/uml/sequence_login_2fa.png) |
| Activite : invitation famille | Comportemental | [`activite_invitation.png`](docs/uml/activite_invitation.png) |
| Etat : cycle de vie document | Comportemental | [`etat_document.png`](docs/uml/etat_document.png) |
| Etat : cycle de vie tache | Comportemental | [`etat_task.png`](docs/uml/etat_task.png) |

---

## Licence

Projet realise dans le cadre du **BTS SIO option SLAM** (Solutions Logicielles et Applications Metiers), promotion 2025/2026.

Auteur : MIR Sagar
Etablissement : Digital School of Paris - IEF2I
