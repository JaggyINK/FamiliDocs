# Documentation Technique - FamiliDocs v2.0

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
│   ├── __init__.py                  # Factory Flask, configuration
│   ├── main.py                      # Point d'entree
│   ├── config/
│   │   └── config.py                # Configurations (dev/test/prod)
│   ├── models/                      # 9 modeles de donnees
│   │   ├── user.py                  # Utilisateurs et roles
│   │   ├── document.py              # Documents et metadonnees
│   │   ├── folder.py                # Organisation en dossiers
│   │   ├── permission.py            # Droits d'acces granulaires
│   │   ├── task.py                  # Taches et echeances
│   │   ├── log.py                   # Journalisation
│   │   ├── notification.py          # Notifications temps reel
│   │   ├── document_version.py      # Historique des versions
│   │   └── tag.py                   # Etiquettes documents
│   ├── services/                    # 7 services metier
│   │   ├── auth_service.py          # Authentification + rate limiting
│   │   ├── document_service.py      # Gestion documentaire
│   │   ├── permission_service.py    # Controle d'acces
│   │   ├── encryption_service.py    # Chiffrement AES
│   │   ├── backup_service.py        # Sauvegardes
│   │   ├── notification_service.py  # Notifications automatiques
│   │   └── search_service.py        # Recherche avancee + stats
│   ├── routes/                      # 8 blueprints
│   │   ├── auth_routes.py           # Connexion, inscription
│   │   ├── user_routes.py           # Dashboard, profil, dossiers
│   │   ├── document_routes.py       # CRUD documents
│   │   ├── task_routes.py           # Gestion taches
│   │   ├── admin_routes.py          # Administration
│   │   ├── notification_routes.py   # API notifications
│   │   ├── version_routes.py        # Versioning documents
│   │   └── search_routes.py         # Recherche + tags
│   ├── templates/                   # 20 templates HTML
│   ├── static/
│   │   ├── css/style.css            # Styles personnalises
│   │   └── js/app.js                # JavaScript principal
│   └── database/                    # SQLite + uploads
├── tests/                           # 4 fichiers de tests
│   ├── conftest.py                  # Fixtures pytest
│   ├── test_documents.py            # Tests documents + auth
│   ├── test_versions.py             # Tests versioning
│   ├── test_tags.py                 # Tests tags + recherche
│   └── test_security.py            # Tests securite
├── docs/                            # Documentation
├── backups/                         # Sauvegardes
└── requirements.txt                 # Dependances
```

---

## 3. Base de donnees

### 3.1 Schema relationnel (9 tables)

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
  ├──── (N) tasks
  ├──── (N) logs
  ├──── (N) notifications
  └──── (N) tags
```

### 3.2 Tables principales

#### `users` - Utilisateurs
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Identifiant |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Email |
| username | VARCHAR(80) | UNIQUE, NOT NULL | Pseudo |
| password_hash | VARCHAR(256) | NOT NULL | Hash bcrypt |
| first_name | VARCHAR(80) | NOT NULL | Prenom |
| last_name | VARCHAR(80) | NOT NULL | Nom |
| role | VARCHAR(20) | NOT NULL | admin/user/trusted |
| is_active | BOOLEAN | | Compte actif |
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
| owner_id | INTEGER | FK users | Proprietaire |
| folder_id | INTEGER | FK folders | Dossier parent |

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
- **Profil modifiable** et changement de mot de passe

### 4.2 Gestion documentaire
- **Upload** multi-format (PDF, images, Word, Excel, texte) avec limite 16 Mo
- **Organisation** en dossiers hierarchiques par categorie
- **Metadonnees** : nom, description, confidentialite, date d'echeance
- **Recherche basique** par nom/description et filtrage par type/dossier
- **Telechargement securise** avec verification des droits

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
- **Acces temporaire** avec date de debut et fin
- **Revocation** immediate des droits
- **Notifications automatiques** lors du partage ou de la revocation

### 4.6 Taches et echeances
- **Creation manuelle** ou automatique (liee a un document)
- **4 priorites** : basse, normale, haute, urgente
- **4 statuts** : en attente, en cours, terminee, annulee
- **Rappels parametrables** (nombre de jours avant echeance)
- **Vue calendrier** et detection des retards

### 4.7 Notifications
- **11 types** : echeances taches, expiration documents, partages, permissions, systeme, bienvenue, sauvegardes
- **Temps reel** dans la navbar avec compteur badge et dropdown AJAX
- **Rafraichissement automatique** toutes les 60 secondes
- **Gestion** : marquer lu/non-lu, suppression unitaire et en masse
- **Verification periodique** des echeances (manuellement ou via cron)
- **Support email** prepare (simule en developpement)

### 4.8 Dashboard ameliore
- **4 compteurs** principaux : documents, dossiers, taches, partages
- **Repartition par type** de fichier avec barres de progression
- **Indicateurs cles** : espace utilise, taches en retard, documents a renouveler
- **Repartition taches par statut**
- **Graphique d'activite** des 6 derniers mois
- **Alertes visuelles** : taches en retard (rouge), documents expirant (jaune)

### 4.9 Administration
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
- **Sessions securisees** : duree 2h, cookie HttpOnly

### 5.2 Controle d'acces
- **RBAC** (Role-Based Access Control) : admin, user, trusted
- **Verification systematique** du proprietaire sur chaque action
- **Permissions granulaires** sur les documents partages
- **Protection CSRF** sur tous les formulaires POST

### 5.3 Protection des donnees
- **Chiffrement AES** optionnel des documents sensibles
- **Noms de stockage UUID** (pas de noms originaux sur le serveur)
- **Validation des extensions** de fichiers autorisees
- **Limite de taille** a 16 Mo par fichier

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
| GET | `/documents/` | Liste documents | Oui |
| GET/POST | `/documents/upload` | Upload document | Oui |
| GET | `/documents/<id>` | Detail document | Oui |
| GET | `/documents/<id>/download` | Telecharger | Oui |
| GET/POST | `/documents/<id>/edit` | Modifier | Oui |
| POST | `/documents/<id>/delete` | Supprimer | Oui |
| GET/POST | `/documents/<id>/share` | Partager | Oui |
| GET | `/documents/<id>/versions` | Historique versions | Oui |
| POST | `/documents/<id>/versions/upload` | Nouvelle version | Oui |
| POST | `/documents/<id>/versions/<vid>/restore` | Restaurer version | Oui |
| GET | `/search` | Recherche avancee | Oui |
| GET | `/search/global` | Recherche AJAX | Oui |
| GET | `/tags` | Liste tags | Oui |
| POST | `/tags/create` | Creer tag | Oui |
| GET | `/tasks/` | Liste taches | Oui |
| GET | `/notifications/` | Liste notifications | Oui |
| GET | `/notifications/count` | Compteur AJAX | Oui |
| GET | `/admin/` | Dashboard admin | Admin |

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
├── conftest.py          # Fixtures partagees (app, client, auth)
├── test_documents.py    # 16 tests : modeles, services, auth, routes
├── test_versions.py     # 4 tests : versioning documents
├── test_tags.py         # 7 tests : tags, associations, recherche
└── test_security.py     # 14 tests : headers, mdp, rate limit, acces
```

### 7.2 Execution
```bash
# Tous les tests
pytest tests/ -v

# Par fichier
pytest tests/test_security.py -v

# Avec couverture
pytest tests/ --cov=app -v
```

### 7.3 Couverture
- **Modeles** : creation, proprietes, methodes statiques
- **Services** : authentification, validation, logique metier
- **Securite** : headers HTTP, politique mots de passe, rate limiting, controle acces
- **Routes** : accessibilite, redirections, authentification requise

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

# 4. Lancer
python app/main.py
```

### 8.2 Configuration
Les environnements sont configures dans `app/config/config.py` :
- **DevelopmentConfig** : debug active, SQLite fichier
- **TestingConfig** : SQLite memoire, mode test
- **ProductionConfig** : debug desactive

Variables d'environnement supportees :
- `FLASK_ENV` : development/testing/production
- `SECRET_KEY` : cle de session (obligatoire en production)
- `DATABASE_URL` : URL de la base de donnees
- `ENCRYPTION_KEY` : cle de chiffrement AES

### 8.3 Compte administrateur
- **Email** : admin@familidocs.local
- **Mot de passe** : Admin123!
- A modifier apres la premiere connexion

---

## 9. Diagrammes

### 9.1 Diagramme de cas d'utilisation

```
Utilisateur:
  - Se connecter / s'inscrire
  - Gerer son profil
  - Uploader / modifier / supprimer des documents
  - Organiser en dossiers
  - Partager avec permissions
  - Gerer les tags
  - Rechercher des documents
  - Gerer les taches et echeances
  - Consulter les notifications
  - Voir l'historique des versions

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

### 9.3 Flux de versioning

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

1. **Architecture solide** : separation MVC stricte, 7 services metier, 8 blueprints
2. **9 modeles de donnees** avec relations complexes (1:N, N:N, auto-reference)
3. **Securite multi-couches** : bcrypt, CSRF, rate limiting, headers HTTP, journalisation
4. **Versioning des documents** : tracabilite complete des modifications
5. **Tags et recherche avancee** : organisation flexible, filtrage multi-criteres
6. **Notifications temps reel** : AJAX, 11 types, rafraichissement automatique
7. **Dashboard statistiques** : graphiques, indicateurs, alertes visuelles
8. **41+ tests unitaires** couvrant modeles, services, securite et routes
9. **Code documente** : docstrings, commentaires, documentation technique
10. **Extensible** : architecture modulaire, configuration multi-environnement
