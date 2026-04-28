# Architecture - FamiliDocs

Document de synthese decrivant l'architecture logicielle, les patrons utilises et les
choix techniques. Pour les details d'implementation, voir `DOCUMENTATION_COMPLETE.md` ;
pour la securite, voir `POLITIQUE_SECURITE.md` ; pour le deploiement, voir `INSTALLATION.md`.

---

## 1. Vue d'ensemble

FamiliDocs est une **application web et bureau** qui suit le patron **MVC enrichi
d'une couche Services**.

```
+-----------------------------+
|       CLIENT                |
|  - Navigateur web (Bootstrap 5.3)
|  - Application bureau (CustomTkinter)
+-----------------------------+
              |
              v
+-----------------------------+
|       VUE                   |
|  50 templates Jinja2        |
|  + assets statiques (CSS, JS, images)
+-----------------------------+
              |
              v
+-----------------------------+
|       CONTROLEUR            |
|  10 blueprints Flask        |
|  96 endpoints HTTP          |
|  Middleware : CSRF, login_required, headers HTTP
+-----------------------------+
              |
              v
+-----------------------------+
|       SERVICES METIER       |
|  8 services :               |
|  Auth, Document, Permission, Encryption,
|  Notification, Search, Backup, Scheduler
+-----------------------------+
              |
              v
+-----------------------------+
|       MODELE                |
|  13 modeles SQLAlchemy      |
|  -> 14 tables PostgreSQL    |
+-----------------------------+
              |
              v
+-----------------------------+
|  POSTGRESQL 16              |
|  + dossier uploads/ (chiffre AES quand prive)
+-----------------------------+
```

Diagramme detaille : [`uml/composants.png`](uml/composants.png)

---

## 2. Couches et responsabilites

### Couche **Modele** (`app/models/`)
Definition des entites metier via SQLAlchemy 2.0.

- **13 fichiers** correspondant aux 14 tables (1 fichier `family.py` regroupe 3 modeles)
- Validation des donnees au niveau objet (decorateurs `@validates`)
- Methodes metier : `User.can_access_document()`, `Document.is_expired`, etc.
- Relations 1:N (User -> Documents) et N:N (Documents -> Tags via `document_tags`)
- Cascade automatique : suppression d'un User cascade ses Documents, Folders, Tasks, Logs

### Couche **Vue** (`app/templates/` + `app/static/`)
Rendu HTML cote serveur avec **Jinja2**.

- **50 templates** dont un layout maitre (`base.html`) avec sidebar, recherche AJAX,
  badge de notifications
- Macros reutilisables : `pagination.html`, `breadcrumbs.html`
- Assets statiques : Bootstrap 5.3, JavaScript pour AJAX (recherche, notifications,
  upload progress, raccourcis clavier)

### Couche **Controleur** (`app/routes/`)
Reception des requetes HTTP, validation des entrees, appel aux services, retour des
reponses (HTML ou JSON).

- **10 blueprints** Flask, un par domaine fonctionnel : `auth`, `user`, `document`,
  `task`, `family`, `admin`, `notification`, `search`, `version`, `message`
- **96 endpoints** au total
- Decorateurs de protection : `@login_required`, `@admin_required`
- Middleware global : protection CSRF (Flask-WTF), 7 en-tetes HTTP de securite

### Couche **Services** (`app/services/`)
Logique metier complexe, isolee des routes.

| Service | Role |
|---|---|
| `AuthService` | Hachage bcrypt, rate limiting, validation mot de passe |
| `DocumentService` | Upload, validation MIME, generation de noms uniques |
| `PermissionService` | 4 droits granulaires + expiration temporelle |
| `EncryptionService` | Chiffrement AES (Fernet) des documents prives |
| `NotificationService` | 12 types de notifications + envoi email (SMTP) |
| `SearchService` | Recherche multicritere + recherche globale AJAX |
| `BackupService` | Sauvegarde ZIP + restauration + export RGPD |
| `SchedulerService` | Thread daemon : verification echeances, cleanup logs RGPD |

### Couche **Donnees** (`PostgreSQL` + `uploads/`)
- **PostgreSQL 16** : base de donnees principale, relations ACID
- **Dossier `uploads/`** : fichiers physiques (chiffres `.enc` quand confidentialite = "private")
- **Cles** : `app/database/.secret_key` (Flask), `app/database/.encryption_key` (Fernet)

---

## 3. Patrons de conception utilises

### MVC + Service Layer
Le **MVC** classique (Modele-Vue-Controleur) est enrichi d'une **couche Services** entre
le Controleur et le Modele. Cela permet de respecter le **Single Responsibility Principle** :

- Controleur : ne gere que la requete HTTP
- Service : porte la logique metier (peut etre teste en isolation)
- Modele : ne represente que les donnees

### Factory Pattern
La fonction `create_app(config_name)` dans `app/__init__.py` est une **factory** qui cree
l'application Flask en fonction de l'environnement (`development`, `testing`, `production`).
Elle permet :
- De lancer les tests sans toucher la BDD de production (TestingConfig avec SQLite memoire)
- De valider les variables d'environnement obligatoires en production
- De configurer differemment chaque deploiement

### Repository (implicite via SQLAlchemy)
SQLAlchemy fournit un acces aux donnees orientees objet (`User.query.filter_by(...)`),
ce qui implemente de facto le pattern **Repository** : on n'ecrit jamais de SQL brut.

### Decorator Pattern
Les decorateurs Flask (`@login_required`, `@admin_required`, `@app.route`,
`@validates('role')`) implementent le pattern **Decorator** pour ajouter des comportements
transversaux sans modifier les fonctions cibles.

### Observer Pattern (a travers les notifications)
Quand une action declenche un evenement (partage de document, assignation de tache),
le `NotificationService` observe et cree des notifications pour les utilisateurs concernes.

---

## 4. Communication entre couches : exemple

**Cas d'usage** : un utilisateur uploade un document marque "prive".

1. **Vue** : formulaire HTML dans `templates/upload_document.html` (multipart/form-data)
2. **Controleur** : route `POST /documents/upload` dans `document_routes.py`
   - CSRF token verifie automatiquement par Flask-WTF
   - `@login_required` verifie l'authentification
   - Recupere les champs du formulaire
   - Appelle `DocumentService.upload_document(file, name, owner_id, ...)`
3. **Service `DocumentService`** :
   - Valide l'extension et le type MIME
   - Genere un nom de stockage unique
   - Sauvegarde le fichier sur disque (`uploads/<uuid>.<ext>`)
   - Cree la ligne dans la table `documents` (via SQLAlchemy)
   - Si `confidentiality == "private"`, appelle `EncryptionService.encrypt_file()`
   - Si `expiry_date` definie, cree automatiquement une `Task` de rappel
4. **Service `EncryptionService`** :
   - Recupere la cle Fernet (`get_encryption_key()`)
   - Chiffre le fichier en AES, ecrit `<uuid>.<ext>.enc`, supprime l'original
5. **Modele `Document`** : ligne creee via `db.session.add()` + `commit()`
6. **Modele `Log`** : trace de l'action (`action='document_upload'`)
7. **Reponse** : redirection vers `/documents/<id>` avec flash message

Diagramme detaille : [`uml/sequence_upload_partage.png`](uml/sequence_upload_partage.png)

---

## 5. Architecture matérielle (deploiement)

### En developpement
- **Tout local** : Flask serveur de dev (Werkzeug) + PostgreSQL local (WSL ou natif)
- Lancement : `python run.py` -> http://localhost:5000

### En production (cible)
- **Serveur Linux** : Ubuntu 22.04 LTS recommande
- **Reverse proxy** : **Nginx** en frontal (HTTPS via Let's Encrypt)
- **Serveur WSGI** : **Gunicorn** (4 workers minimum)
- **Base** : **PostgreSQL 16** (peut etre sur le meme serveur ou distant managed)
- **Stockage fichiers** : disque local ou S3 (a adapter)
- **Sauvegarde** : cron quotidien executant `BackupService.create_backup()`
- **Monitoring** : Sentry (erreurs), Prometheus + Grafana (metrics)

Diagramme : [`uml/deploiement.png`](uml/deploiement.png)

### Application bureau
La version desktop CustomTkinter accede directement a la **meme base PostgreSQL** via
SQLAlchemy. Aucun protocole HTTP entre desktop et BDD : la connexion est directe via le
driver `psycopg2-binary`. Les fichiers uploades sont aussi partages (meme dossier).

---

## 6. Choix techniques justifies

| Choix | Pourquoi |
|---|---|
| **Python 3.12** | Langage concis, ecosysteme web mature, productivite eleve pour un projet d'ecole |
| **Flask 3.0** (vs Django) | Micro-framework qui laisse choisir les composants, plus leger, meilleur pour comprendre chaque couche |
| **SQLAlchemy 2.0** | ORM standard de l'ecosysteme Python, abstrait le SGBD (permet SQLite en tests) |
| **PostgreSQL 16** (vs MySQL) | Conformite SQL stricte, transactions ACID, types avances (JSONB), le plus utilise avec Flask |
| **bcrypt** | Standard pour le hachage de mots de passe (sel automatique, cout configurable) |
| **Fernet AES** | Recette pre-cassee de la bibliotheque `cryptography`, AES-128-CBC + HMAC-SHA256 |
| **TOTP (pyotp)** | Standard RFC 6238 pour la 2FA, compatible avec toutes les apps d'authentification |
| **Bootstrap 5.3** | Responsive sans expertise CSS, ecosysteme de composants prets |
| **CustomTkinter** (desktop) | Tkinter avec un look moderne, dans la stdlib, compilable en .exe |
| **pytest 7.4** | Framework de test standard Python, fixtures + parametrize |
| **PyInstaller** | Compilation .exe Windows pour distribution sans Python installe |

---

## 7. Securite par conception

La securite est presente **a chaque couche** :

- **Vue** : echappement automatique Jinja2 (anti-XSS), token CSRF dans chaque formulaire
- **Controleur** : decorateurs `@login_required` et `@admin_required`, validation des entrees
- **Service** : `AuthService` rate limiting, `EncryptionService` chiffrement automatique
- **Modele** : `@validates('role')` sur `FamilyMember`, contraintes UNIQUE en BDD
- **Donnees** : mots de passe haches bcrypt, documents prives chiffres AES sur disque
- **Reseau** : 7 en-tetes HTTP de securite (CSP, HSTS, X-Frame-Options...)

Voir details dans [`POLITIQUE_SECURITE.md`](POLITIQUE_SECURITE.md) et [`ANALYSE_RISQUES.md`](ANALYSE_RISQUES.md).

---

## 8. Tests par niveau

La pyramide de tests reflete l'architecture en couches.

```
       /\        25 tests d'integration
      /  \       (workflows complets : login -> upload -> partage)
     /----\
    /      \     40 tests de routes
   /        \    (codes HTTP, redirections, controle d'acces)
  /----------\
 /            \  ~190 tests unitaires
/______________\ (modeles + services en isolation)
```

Plus 25 tests de securite (CSRF, injection, contournement) et 17 tests RGPD.
**Total : 307 tests** qui passent en ~75 secondes.

Detail : [`PLAN_TESTS.md`](PLAN_TESTS.md).

---

## 9. Evolutivite et maintenabilite

### Ce qui rend le projet maintenable
- **Separation des responsabilites** stricte (MVC + Services)
- **Tests automatises** qui valident le comportement (filet de securite pour le refactoring)
- **Documentation complete** : 11 fichiers .md + 11 diagrammes UML
- **CHANGELOG** versionne (4 versions majeures de v1.0 a v2.4)
- **Configuration externalisee** dans `.env` (pas de constantes magiques)
- **Migrations BDD** preparees (Flask-Migrate / Alembic)

### Comment ajouter une fonctionnalite (exemple : ajouter un commentaire sur les documents)
1. Creer un modele `Comment` dans `app/models/comment.py`
2. Generer une migration : `flask db migrate -m "add comments"`
3. Creer une route dans `document_routes.py` : `POST /documents/<id>/comment`
4. Ajouter un template ou un fragment partial pour le formulaire
5. Ecrire un test dans `tests/test_documents.py`
6. Mettre a jour `CHANGELOG.md`

Le tout en **moins de 50 lignes** de code grace a la separation en couches.

---

## 10. Limites et perspectives

### Limites connues
- **Pas de SPA** : tout est rendu cote serveur, pas d'experience reactive type Vue/React
- **Pas de WebSocket** : le chat familial utilise du polling AJAX, pas du push temps reel
- **Pas de microservices** : monolithe, mais bien structure (preparation possible pour decoupage)
- **Pas de CI/CD** : tests lances manuellement, deploiement manuel
- **Pas de monitoring** : pas de Sentry/Prometheus configures (juste les logs Python)

### Perspectives d'evolution
- **API REST** documentee avec OpenAPI/Swagger (decoupler frontend/backend)
- **Frontend Vue.js** ou **React** pour une vraie SPA
- **WebSocket** (Flask-SocketIO) pour le chat en temps reel
- **CI/CD** GitHub Actions (tests + lint + deploiement automatique)
- **Monitoring** Sentry + Prometheus
- **Application mobile native** iOS/Android (briefing prepare en interne)

---

## Annexes : documents associes

| Aspect | Document |
|---|---|
| Code detail | [`DOCUMENTATION_COMPLETE.md`](DOCUMENTATION_COMPLETE.md) |
| Modele de donnees | [`schema_bdd.md`](schema_bdd.md) |
| Securite | [`POLITIQUE_SECURITE.md`](POLITIQUE_SECURITE.md) |
| Risques | [`ANALYSE_RISQUES.md`](ANALYSE_RISQUES.md) |
| RGPD | [`CONFORMITE_RGPD.md`](CONFORMITE_RGPD.md) |
| Tests | [`PLAN_TESTS.md`](PLAN_TESTS.md) |
| Installation | [`INSTALLATION.md`](INSTALLATION.md) |
| Glossaire | [`GLOSSAIRE.md`](GLOSSAIRE.md) |
| Manuel utilisateur | [`MANUEL_UTILISATEUR.md`](MANUEL_UTILISATEUR.md) |
| Diagrammes UML | [`uml/`](uml/) (11 PNG) |
