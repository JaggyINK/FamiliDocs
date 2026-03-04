# Documentation Technique - FamiliDocs v2.1

## 1. Presentation generale

### 1.1 Description du projet
FamiliDocs est un coffre administratif numerique familial, developpe en Python avec le framework Flask. L'application permet aux familles de centraliser, organiser et securiser leurs documents administratifs tout en offrant un systeme de partage controle entre membres.

### 1.2 Contexte
Projet realise dans le cadre du BTS SIO option SLAM (Solutions Logicielles et Applications Metier), epreuve E5.

### 1.3 Objectifs
- Centraliser les documents administratifs familiaux
- Gerer les echeances et rappels automatiques
- Permettre le partage securise entre membres de confiance
- Assurer la tracabilite des acces et modifications
- Offrir un espace familial collaboratif (chat, taches partagees)

---

## 2. Architecture technique

### 2.1 Stack technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.8+ |
| Framework web | Flask | 3.0 |
| ORM | SQLAlchemy | 2.0 |
| Base de donnees | SQLite | 3 |
| Authentification | Flask-Login | 0.6 |
| Hashage | bcrypt | 4.1 |
| Chiffrement | cryptography | 41.0 |
| Frontend | Bootstrap | 5.3 |
| Tests | pytest | 7.4 |

### 2.2 Pattern architectural : MVC (Modele-Vue-Controleur)

L'application suit le pattern MVC adapte a Flask :

```
Modeles (app/models/)       -> Couche donnees (SQLAlchemy)
Services (app/services/)    -> Logique metier
Routes (app/routes/)        -> Controleurs (Blueprints Flask)
Templates (app/templates/)  -> Vues (Jinja2)
```

Cette separation garantit :
- La maintenabilite du code
- La testabilite de chaque couche
- La reutilisabilite de la logique metier

### 2.3 Structure du projet

```
FamiliDocs/
├── app/
│   ├── __init__.py                  # Factory Flask, error handlers, securite
│   ├── main.py                      # Point d'entree
│   ├── config/
│   │   └── config.py                # Configurations (dev/test/prod)
│   ├── models/                      # 13 modeles de donnees
│   │   ├── user.py                  # Utilisateurs, roles, photo profil
│   │   ├── document.py              # Documents, metadonnees, review
│   │   ├── folder.py                # Organisation en dossiers
│   │   ├── permission.py            # Droits d'acces granulaires
│   │   ├── task.py                  # Taches, echeances, assignation
│   │   ├── log.py                   # Journalisation (21 actions)
│   │   ├── notification.py          # Notifications (11 types)
│   │   ├── document_version.py      # Historique des versions
│   │   ├── tag.py                   # Etiquettes documents
│   │   ├── family.py                # Familles, membres, liens partage
│   │   └── message.py               # Chat familial
│   ├── services/                    # 7 services metier
│   │   ├── auth_service.py          # Authentification + rate limiting
│   │   ├── document_service.py      # Gestion documentaire
│   │   ├── permission_service.py    # Controle d'acces
│   │   ├── encryption_service.py    # Chiffrement AES
│   │   ├── backup_service.py        # Sauvegardes
│   │   ├── notification_service.py  # Notifications automatiques
│   │   └── search_service.py        # Recherche avancee + stats
│   ├── routes/                      # 10 blueprints
│   │   ├── auth_routes.py           # Connexion, inscription, invitations
│   │   ├── user_routes.py           # Dashboard, profil, dossiers, avatar
│   │   ├── document_routes.py       # CRUD documents, review, partage
│   │   ├── task_routes.py           # Gestion taches, assignation
│   │   ├── admin_routes.py          # Administration systeme
│   │   ├── notification_routes.py   # API notifications
│   │   ├── version_routes.py        # Versioning documents
│   │   ├── search_routes.py         # Recherche + tags
│   │   ├── family_routes.py         # Familles, roles, invitations
│   │   └── message_routes.py        # Chat familial
│   ├── templates/                   # 30+ templates HTML
│   │   ├── base.html                # Template de base (navbar, footer)
│   │   ├── errors/                  # Pages d'erreur (403, 404, 500)
│   │   └── ...                      # Templates fonctionnels
│   ├── static/
│   │   ├── css/style.css            # Styles personnalises
│   │   └── js/app.js                # JavaScript principal
│   └── database/                    # SQLite + uploads
├── tests/                           # 8 fichiers de tests (257 tests)
│   ├── conftest.py                  # Fixtures pytest partagees
│   ├── test_models.py               # 102 tests : tous les modeles
│   ├── test_services.py             # 28 tests : services metier
│   ├── test_routes.py               # 30 tests : routes + securite
│   ├── test_integration.py          # 17 tests : workflows complets
│   ├── test_documents.py            # Tests documents + auth
│   ├── test_versions.py             # Tests versioning
│   ├── test_tags.py                 # Tests tags + recherche
│   └── test_security.py             # Tests securite avancee
├── docs/                            # Documentation complete
│   ├── schema_bdd.md                # Schema base de donnees (15 tables)
│   ├── documentation_technique.md   # Ce document
│   └── tableau_E5.md                # Tableau competences BTS E5
├── .env.example                     # Variables d'environnement
├── backups/                         # Sauvegardes
└── requirements.txt                 # Dependances
```

---

## 3. Base de donnees

### 3.1 Schema relationnel (15 tables)

```
users (1) ──── (N) documents (1) ──── (N) document_versions
  │                    │
  │                    ├──── (N) permissions
  │                    ├──── (N) tasks
  │                    ├──── (N) logs
  │                    ├──── (N) notifications
  │                    └──── (N:N) document_tags ──── tags
  │
  ├──── (N) folders (auto-reference parent/enfant)
  ├──── (N) tasks (proprietaire + assignation)
  ├──── (N) logs
  ├──── (N) notifications
  ├──── (N) tags
  ├──── (N) families (createur)
  ├──── (N:N) family_members ──── families
  ├──── (N) messages
  └──── (N) share_links
```

### 3.2 Tables principales

#### `users` - Utilisateurs
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Identifiant |
| email | VARCHAR(120) | UNIQUE, NOT NULL, INDEX | Email |
| username | VARCHAR(80) | UNIQUE, NOT NULL | Pseudo |
| password_hash | VARCHAR(256) | NOT NULL | Hash bcrypt |
| first_name | VARCHAR(80) | NOT NULL | Prenom |
| last_name | VARCHAR(80) | NOT NULL | Nom |
| role | VARCHAR(20) | NOT NULL | admin/user/trusted |
| is_active | BOOLEAN | | Compte actif |
| profile_photo | VARCHAR(255) | | Chemin photo de profil |
| family_title | VARCHAR(50) | | Titre familial |
| last_login | DATETIME | | Derniere connexion |

#### `documents` - Documents
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| name | VARCHAR(200) | NOT NULL | Nom affiche |
| original_filename | VARCHAR(255) | NOT NULL | Nom original |
| stored_filename | VARCHAR(255) | UNIQUE | Nom stockage UUID |
| file_type | VARCHAR(50) | | pdf/word/excel/image |
| file_size | INTEGER | | Taille en octets |
| confidentiality | VARCHAR(20) | | public/private/restricted |
| is_encrypted | BOOLEAN | | Chiffrement AES |
| expiry_date | DATE | | Echeance document |
| next_review_date | DATE | | Date prochaine revision |
| last_reviewed_at | DATETIME | | Derniere revision effectuee |
| owner_id | INTEGER | FK users | Proprietaire |
| folder_id | INTEGER | FK folders | Dossier parent |

#### `tasks` - Taches
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| title | VARCHAR(200) | NOT NULL | Titre |
| description | TEXT | | Description |
| due_date | DATE | NOT NULL | Echeance |
| priority | VARCHAR(20) | | low/normal/high/urgent |
| status | VARCHAR(20) | | pending/in_progress/completed/cancelled |
| reminder_days | INTEGER | | Jours avant rappel |
| owner_id | INTEGER | FK users | Proprietaire |
| document_id | INTEGER | FK documents | Document lie |
| assigned_to_id | INTEGER | FK users | Membre famille assigne |
| completed_at | DATETIME | | Date completion |

#### `families` - Groupes familiaux
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| name | VARCHAR(100) | NOT NULL | Nom de la famille |
| description | TEXT | | Description |
| creator_id | INTEGER | FK users | Createur |
| created_at | DATETIME | | Date de creation |

#### `family_members` - Membres de famille
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| family_id | INTEGER | FK families | Famille |
| user_id | INTEGER | FK users | Membre |
| role | VARCHAR(30) | NOT NULL | 8 roles hierarchiques |
| joined_at | DATETIME | | Date d'adhesion |
| invited_by | INTEGER | FK users | Inviteur |

**Contrainte** : UNIQUE(family_id, user_id)

#### `share_links` - Liens de partage securises
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| token | VARCHAR(64) | UNIQUE, INDEX | Token securise |
| document_id | INTEGER | FK documents | Document (optionnel) |
| family_id | INTEGER | FK families | Famille (optionnel) |
| created_by | INTEGER | FK users | Createur |
| expires_at | DATETIME | NOT NULL | Expiration |
| max_uses | INTEGER | | Utilisations max |
| use_count | INTEGER | | Compteur |
| is_revoked | BOOLEAN | | Revoque |
| granted_role | VARCHAR(30) | | Role attribue |

#### `messages` - Chat familial
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| family_id | INTEGER | FK families | Famille |
| sender_id | INTEGER | FK users | Expediteur |
| content | TEXT | NOT NULL | Contenu |
| is_announcement | BOOLEAN | | Annonce importante |
| is_deleted | BOOLEAN | | Suppression douce |

#### `document_versions` - Historique versions
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| document_id | INTEGER | FK documents | Document parent |
| version_number | INTEGER | NOT NULL | Numero de version |
| stored_filename | VARCHAR(255) | | Fichier de la version |
| original_filename | VARCHAR(255) | | Nom original |
| file_size | INTEGER | | Taille |
| comment | TEXT | | Commentaire de version |
| uploaded_by | INTEGER | FK users | Auteur de la version |
| created_at | DATETIME | INDEX | Date de creation |

#### `tags` - Etiquettes
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK | Identifiant |
| name | VARCHAR(50) | INDEX | Nom du tag |
| color | VARCHAR(7) | | Couleur hexadecimale |
| owner_id | INTEGER | FK users | Proprietaire |

**Contrainte** : UNIQUE(name, owner_id)

#### `document_tags` - Association N:N
| Colonne | Type | Contraintes |
|---------|------|-------------|
| document_id | INTEGER | FK, PK |
| tag_id | INTEGER | FK, PK |

#### `permissions` - Droits d'acces
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | PK |
| document_id | INTEGER | FK documents |
| user_id | INTEGER | FK users (beneficiaire) |
| granted_by | INTEGER | FK users (accordeur) |
| can_view | BOOLEAN | Droit lecture |
| can_edit | BOOLEAN | Droit modification |
| can_download | BOOLEAN | Droit telechargement |
| can_share | BOOLEAN | Droit re-partage |
| end_date | DATE | Expiration (null = permanent) |

#### `notifications` - Notifications
| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | PK |
| user_id | INTEGER | FK users |
| type | VARCHAR(50) | 11 types possibles |
| title | VARCHAR(200) | Titre |
| message | TEXT | Contenu |
| priority | VARCHAR(20) | low/normal/high/urgent |
| is_read | BOOLEAN | Lu ou non |
| expires_at | DATETIME | Auto-suppression |

---

## 4. Fonctionnalites detaillees

### 4.1 Gestion des utilisateurs
- **Inscription** avec validation email/username unique et politique de mot de passe
- **Authentification** securisee avec bcrypt + limitation des tentatives (5 max, blocage 15 min)
- **3 roles** : administrateur (acces complet), utilisateur (CRUD propres docs), personne de confiance (acces partage)
- **Profil modifiable** avec photo de profil et titre familial
- **Changement de mot de passe** avec validation politique

### 4.2 Gestion documentaire
- **Upload** multi-format (PDF, images, Word, Excel, texte) avec limite 16 Mo
- **Organisation** en dossiers hierarchiques par categorie (5 dossiers par defaut)
- **Metadonnees** : nom, description, confidentialite, date d'echeance
- **Date de revision** obligatoire avec alertes et bouton "Marquer comme revise"
- **Recherche basique** par nom/description et filtrage par type/dossier
- **Telechargement securise** avec verification des droits
- **Validation** des extensions et niveaux de confidentialite

### 4.3 Versioning des documents
- **Historique complet** de toutes les versions d'un document
- **Upload de nouvelles versions** avec commentaire de modification
- **Restauration** d'anciennes versions en un clic
- **Telechargement** de n'importe quelle version
- **Sauvegarde automatique** de la version courante avant remplacement

### 4.4 Tags et recherche avancee
- **Tags personnalises** avec couleur au choix
- **Association N:N** entre documents et tags
- **Recherche multi-criteres** : texte, type, dossier, tags, dates, confidentialite
- **Tri configurable** : date, nom, taille (ascendant/descendant)
- **Recherche globale AJAX** pour resultats instantanes

### 4.5 Partage et permissions
- **Partage granulaire** : lecture, modification, telechargement, re-partage
- **Acces temporaire** avec date de debut et fin (max 90 jours renouvelable)
- **Partage multiple** : plusieurs utilisateurs en une seule operation
- **Partage de dossiers** : partager un dossier = partager tous ses documents
- **Exclusion automatique** : le partageur ne peut pas se selectionner
- **Revocation** immediate des droits
- **Liens de partage** securises avec token, expiration et nombre d'utilisations
- **Notifications automatiques** lors du partage ou de la revocation

### 4.6 Taches et echeances
- **Creation manuelle** ou automatique (liee a un document)
- **4 priorites** : basse, normale, haute, urgente
- **4 statuts** : en attente, en cours, terminee, annulee
- **Assignation** de taches a des membres de la famille
- **Rappels parametrables** (nombre de jours avant echeance)
- **Vue calendrier** et detection des retards
- **Validation des entrees** : titre obligatoire, date valide

### 4.7 Gestion familiale
- **Creation de famille** avec description
- **8 roles hierarchiques** : chef_famille, admin, parent, gestionnaire, enfant, editeur, lecteur, invite
- **Limite 2 chefs de famille** par foyer
- **Invitations intelligentes** : lien accessible sans connexion, redirection vers inscription ou connexion
- **Rejoindre famille** a l'inscription via token en session
- **Gestion des roles** : promotion/retrogradation selon privileges
- **Revocation auto** : quitter la famille = perdre l'acces aux fichiers partages

### 4.8 Chat familial
- **Messagerie temps reel** au sein de la famille
- **Annonces** reservees aux admin/chef/parent
- **Edition et suppression** de ses propres messages
- **Soft delete** : les messages supprimes affichent "[Message supprime]"
- **Notifications** pour les annonces importantes

### 4.9 Notifications
- **11 types** : echeances taches, expiration documents, partages, permissions, systeme, bienvenue, sauvegardes
- **Temps reel** dans la navbar avec compteur badge et dropdown AJAX
- **Rafraichissement automatique** toutes les 60 secondes
- **Gestion** : marquer lu/non-lu, suppression unitaire et en masse
- **Verification periodique** des echeances (manuellement ou via cron)
- **Support email** prepare (simule en developpement, logging en production)

### 4.10 Dashboard ameliore
- **4 compteurs** principaux : documents, dossiers, taches, partages
- **Repartition par type** de fichier avec barres de progression
- **Indicateurs cles** : espace utilise, taches en retard, documents a renouveler
- **Repartition taches par statut**
- **Graphique d'activite** des 6 derniers mois (cliquable vers details)
- **Alertes visuelles** : taches en retard (rouge), documents expirant (jaune)

### 4.11 Administration
- **Tableau de bord** avec statistiques systeme
- **Gestion utilisateurs** : creation, modification, activation/desactivation, reset mot de passe
- **Logs systeme** : consultation et filtrage de toutes les actions
- **Sauvegardes** : creation, restauration, suppression

---

## 5. Securite

### 5.1 Authentification
- **Hashage bcrypt** avec salt aleatoire (cout 12)
- **Politique de mot de passe** : 8+ caracteres, majuscule, minuscule, chiffre, caractere special
- **Limitation de tentatives** : 5 essais max, blocage 15 minutes par IP
- **Sessions securisees** : duree 2h, cookie HttpOnly, SameSite=Lax, Secure en production

### 5.2 Controle d'acces
- **RBAC** (Role-Based Access Control) : admin, user, trusted
- **Verification systematique** du proprietaire sur chaque action
- **Permissions granulaires** sur les documents partages
- **Protection CSRF** sur tous les formulaires POST
- **Validation serveur** de toutes les entrees (titres, dates, niveaux de confidentialite)

### 5.3 Protection des donnees
- **Chiffrement AES** optionnel des documents sensibles
- **Noms de stockage UUID** (pas de noms originaux sur le serveur)
- **Validation des extensions** de fichiers autorisees
- **Limite de taille** a 16 Mo par fichier
- **Cle secrete** generee automatiquement si non fournie

### 5.4 En-tetes HTTP de securite
- `X-Content-Type-Options: nosniff` - empeche le MIME sniffing
- `X-Frame-Options: SAMEORIGIN` - protege contre le clickjacking
- `X-XSS-Protection: 1; mode=block` - protection XSS navigateur
- `Referrer-Policy: strict-origin-when-cross-origin` - controle du referrer
- `Cache-Control: no-cache, no-store` - empeche la mise en cache de donnees sensibles

### 5.5 Journalisation
- **21 types d'actions** journalisees
- **Adresse IP** et User-Agent enregistres
- **Tracabilite complete** des acces aux documents
- **Historique des tentatives de connexion** echouees
- **Logging applicatif** structure avec le module `logging` Python

### 5.6 Pages d'erreur personnalisees
- **403 Forbidden** : acces refuse avec navigation
- **404 Not Found** : page introuvable avec liens de retour
- **500 Internal Server Error** : erreur serveur avec message utilisateur

---

## 6. API et routes

### 6.1 Endpoints principaux

| Methode | URL | Description | Auth |
|---------|-----|-------------|------|
| GET | `/` | Redirection login/dashboard | Non |
| GET/POST | `/login` | Connexion | Non |
| GET/POST | `/register` | Inscription | Non |
| GET | `/logout` | Deconnexion | Oui |
| GET | `/dashboard` | Tableau de bord | Oui |
| GET/POST | `/profile` | Profil utilisateur | Oui |
| POST | `/profile/avatar` | Upload photo de profil | Oui |
| GET | `/documents/` | Liste documents | Oui |
| GET/POST | `/documents/upload` | Upload document | Oui |
| GET | `/documents/<id>` | Detail document | Oui |
| GET | `/documents/<id>/download` | Telecharger | Oui |
| GET/POST | `/documents/<id>/edit` | Modifier | Oui |
| POST | `/documents/<id>/delete` | Supprimer | Oui |
| GET/POST | `/documents/<id>/share` | Partager | Oui |
| POST | `/documents/<id>/mark-reviewed` | Marquer revise | Oui |
| GET | `/documents/<id>/versions` | Historique versions | Oui |
| POST | `/documents/<id>/versions/upload` | Nouvelle version | Oui |
| POST | `/documents/<id>/versions/<vid>/restore` | Restaurer version | Oui |
| GET | `/documents/shared` | Documents partages recus | Oui |
| GET | `/documents/my-shared` | Documents partages par moi | Oui |
| GET | `/search` | Recherche avancee | Oui |
| GET | `/search/global` | Recherche AJAX | Oui |
| GET | `/tags` | Liste tags | Oui |
| POST | `/tags/create` | Creer tag | Oui |
| GET | `/tasks/` | Liste taches | Oui |
| GET/POST | `/tasks/create` | Creer tache | Oui |
| GET | `/tasks/<id>` | Detail tache | Oui |
| GET/POST | `/tasks/<id>/edit` | Modifier tache | Oui |
| GET | `/tasks/calendar` | Vue calendrier | Oui |
| GET | `/tasks/overdue` | Taches en retard | Oui |
| GET | `/tasks/upcoming` | Taches a venir | Oui |
| GET | `/families/` | Liste familles | Oui |
| GET/POST | `/families/create` | Creer famille | Oui |
| GET | `/families/<id>` | Detail famille | Oui |
| GET | `/families/<id>/chat` | Chat familial | Oui |
| GET | `/join/<token>` | Lien invitation smart | Non |
| GET | `/notifications/` | Liste notifications | Oui |
| GET | `/notifications/count` | Compteur AJAX | Oui |
| GET | `/activity` | Historique activite | Oui |
| GET | `/activity/detailed` | Activite detaillee | Oui |
| GET | `/folders` | Liste dossiers | Oui |
| GET | `/admin/` | Dashboard admin | Admin |
| GET | `/admin/users` | Gestion utilisateurs | Admin |
| GET | `/admin/logs` | Logs systeme | Admin |

### 6.2 API AJAX (JSON)

| URL | Description | Reponse |
|-----|-------------|---------|
| `/notifications/count` | Compteur non-lus | `{"count": N}` |
| `/notifications/recent` | 5 dernieres notifs | `{"notifications": [...]}` |
| `/search/global?q=...` | Recherche instantanee | `{"documents": [...], "tasks": [...], "tags": [...]}` |

---

## 7. Tests

### 7.1 Organisation
```
tests/
├── conftest.py              # Fixtures partagees (app, client, users, fixtures)
├── test_models.py           # 102 tests : User, Document, Task, Folder, Family,
│                            #   FamilyMember, ShareLink, Permission, Notification, Log
├── test_services.py         # 28 tests : AuthService, DocumentService, NotificationService
├── test_routes.py           # 30 tests : Auth, Documents, Tasks, User, Admin,
│                            #   Erreurs, En-tetes securite
├── test_integration.py      # 17 tests : Workflows complets (inscription->partage->tache)
├── test_documents.py        # Tests documents + authentification
├── test_versions.py         # Tests versioning documents
├── test_tags.py             # Tests tags + associations + recherche
└── test_security.py         # Tests securite avancee
```

### 7.2 Couverture des tests (257 tests)

| Categorie | Nb tests | Description |
|-----------|----------|-------------|
| Modeles | 102 | Creation, proprietes, methodes, relations |
| Services | 28 | Auth, documents, notifications, permissions |
| Routes | 30 | Acces, redirections, validation, erreurs |
| Integration | 17 | Workflows complets multi-etapes |
| Documents | 16 | Upload, modification, recherche |
| Securite | 14 | Headers HTTP, rate limiting, acces |
| Versioning | 4 | Upload, restauration, historique |
| Tags | 7 | CRUD, associations, recherche |
| **TOTAL** | **257** | |

### 7.3 Execution
```bash
# Tous les tests
pytest tests/ -v

# Par fichier
pytest tests/test_models.py -v
pytest tests/test_security.py -v

# Avec couverture
pytest tests/ --cov=app -v

# Tests specifiques par classe
pytest tests/test_models.py::TestUserModel -v
pytest tests/test_integration.py::TestDocumentSharingWorkflow -v
```

### 7.4 Couverture par couche
- **Modeles** : creation, proprietes calculees, methodes statiques, relations, contraintes
- **Services** : authentification, validation, hashage, logique metier, rate limiting
- **Routes** : accessibilite, redirections, authentification requise, validation entrees
- **Integration** : workflows complets (inscription -> document -> partage -> tache)
- **Securite** : headers HTTP, politique mots de passe, rate limiting, controle acces, permissions granulaires

---

## 8. Deploiement

### 8.1 Installation
```bash
# 1. Cloner le projet
git clone <url-du-repo>
cd FamiliDocs

# 2. Environnement virtuel
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux

# 3. Dependances
pip install -r requirements.txt

# 4. Configuration (optionnel)
cp .env.example .env
# Editer .env avec vos valeurs

# 5. Lancer
python app/main.py
```

### 8.2 Configuration
Les environnements sont configures dans `app/config/config.py` :
- **DevelopmentConfig** : debug active, SQLite fichier
- **TestingConfig** : SQLite memoire, mode test
- **ProductionConfig** : debug desactive, securite renforcee

Variables d'environnement (voir `.env.example`) :
- `FLASK_ENV` : development/testing/production
- `SECRET_KEY` : cle de session (generee automatiquement si absente)
- `DATABASE_URL` : URL de la base de donnees
- `ENCRYPTION_KEY` : cle de chiffrement AES
- `FAMILIDOCS_UPLOAD_FOLDER` : dossier des uploads
- `FAMILIDOCS_BACKUP_FOLDER` : dossier des sauvegardes
- `ADMIN_DEFAULT_PASSWORD` : mot de passe admin initial
- `LOG_LEVEL` : niveau de log (DEBUG/INFO/WARNING)

### 8.3 Compte administrateur
- **Email** : admin@familidocs.local
- **Mot de passe** : Admin123! (ou variable ADMIN_DEFAULT_PASSWORD)
- A modifier apres la premiere connexion

---

## 9. Diagrammes

### 9.1 Diagramme de cas d'utilisation

```
Utilisateur:
  - Se connecter / s'inscrire
  - Gerer son profil (photo, titre familial)
  - Uploader / modifier / supprimer des documents
  - Organiser en dossiers
  - Partager avec permissions granulaires
  - Gerer les tags
  - Rechercher des documents
  - Gerer les taches et echeances
  - Consulter les notifications
  - Voir l'historique des versions
  - Marquer un document comme revise
  - Rejoindre une famille via invitation
  - Participer au chat familial

Chef de famille (herite de Utilisateur):
  - Creer et gerer la famille
  - Gerer les roles des membres
  - Poster des annonces
  - Assigner des taches aux membres
  - Voir l'activite des membres

Administrateur (herite de Utilisateur):
  - Gerer les utilisateurs
  - Consulter les logs systeme
  - Creer / restaurer des sauvegardes
  - Activer / desactiver des comptes
```

### 9.2 Flux d'upload d'un document

```
Utilisateur
    |
    v
[Selectionner fichier]
    |
    v
[Validation extension + taille]
    |
    ├── Invalide -> Message d'erreur
    |
    v (valide)
[Validation confidentialite]
    |
    v
[Generer nom UUID]
    |
    v
[Sauvegarder sur disque]
    |
    v
[Creer entree BDD]
    |
    v
[Logger l'action]
    |
    v
[Creer tache si echeance]
    |
    v
[Redirection vers le document]
```

### 9.3 Flux d'invitation familiale

```
Chef de famille
    |
    v
[Generer lien d'invitation]
    |
    v
[Envoyer lien au destinataire]
    |
    v
Destinataire clique sur /join/<token>
    |
    ├── Deja connecte -> Accepter invitation -> Rejoindre famille
    |
    ├── Pas connecte, a un compte -> Connexion -> Accepter -> Rejoindre
    |
    └── Pas connecte, pas de compte -> Inscription -> Auto-join famille
```

### 9.4 Flux de versioning

```
[Document existant v1]
    |
    v
[Upload nouvelle version]
    |
    v
[Sauvegarder v1 dans document_versions]
    |
    v
[Stocker nouveau fichier (UUID)]
    |
    v
[Creer entree v2 dans document_versions]
    |
    v
[Mettre a jour le document principal]
    |
    v
[Logger la modification]
```

---

## 10. Points forts pour le jury

1. **Architecture solide** : separation MVC stricte, 7 services metier, 10 blueprints
2. **13 modeles de donnees** avec relations complexes (1:N, N:N, auto-reference, hierarchie de roles)
3. **Securite multi-couches** : bcrypt, CSRF, rate limiting, headers HTTP, journalisation, validation serveur
4. **Gestion familiale** : 8 roles hierarchiques, invitations intelligentes, chat, assignation de taches
5. **Versioning des documents** : tracabilite complete des modifications
6. **Tags et recherche avancee** : organisation flexible, filtrage multi-criteres
7. **Notifications temps reel** : AJAX, 11 types, rafraichissement automatique
8. **Dashboard statistiques** : graphiques, indicateurs, alertes visuelles
9. **257 tests automatises** couvrant modeles, services, routes, integration et securite
10. **Pages d'erreur personnalisees** (403, 404, 500) et logging structure
11. **Code documente** : docstrings, commentaires, documentation technique complete
12. **Extensible** : architecture modulaire, configuration multi-environnement, `.env.example`
