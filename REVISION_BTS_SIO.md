# REVISION BTS SIO SLAM - FamiliDocs
## Epreuve E5 - Preparation a l'oral

---

# PARTIE 1 : COMPETENCES COUVERTES PAR FAMILIDOCS

## Competence 1 : Gerer le patrimoine informatique

**Ce que tu dois savoir expliquer :**
FamiliDocs gere un patrimoine documentaire familial avec une base de donnees structuree.

| Ce que tu as fait | Ou dans le code | Explication simple |
|---|---|---|
| Schema BDD 15 tables (PostgreSQL) | `docs/schema_bdd.md` | Chaque table represente une entite (utilisateurs, documents, dossiers, taches...) |
| 13 modeles SQLAlchemy | `app/models/` | Chaque fichier `.py` dans models/ correspond a une table. Ex: `user.py` = table `users` |
| Gestion des sauvegardes | `app/services/backup_service.py` | Export complet en ZIP (BDD + fichiers), restauration, suppression |
| Niveaux d'habilitation | `app/models/user.py` lignes role | 3 roles app : `admin`, `user`, `trusted` |
| Roles famille | `app/models/family.py` FamilyMember.ROLES | 8 roles hierarchiques : chef_famille > parent > tuteur > ... > invite |
| Documentation technique | `docs/documentation_technique.md` | Architecture, API, securite, deploiement |

**Phrase cle pour l'oral :**
> "J'ai concu une base de donnees relationnelle **PostgreSQL** de 15 tables avec SQLAlchemy comme ORM. Chaque modele Python correspond a une table et definit les colonnes, les relations et les methodes metier. Les sauvegardes sont automatisables et exportent la BDD en JSON + les fichiers uploades dans un ZIP. L'ORM permet de changer de SGBD facilement : PostgreSQL en dev/prod, SQLite en memoire pour les tests."

---

## Competence 2 : Repondre aux incidents et demandes

**Ce que tu dois savoir expliquer :**
FamiliDocs journalise toutes les actions et gere les erreurs.

| Ce que tu as fait | Ou dans le code | Explication simple |
|---|---|---|
| Journalisation (21 types) | `app/models/log.py` ligne 46 ACTION_TYPES | Chaque action utilisateur est enregistree avec IP, date, details |
| Pages d'erreur | `app/templates/errors/403.html`, `404.html`, `500.html` | Pages personnalisees pour chaque type d'erreur HTTP |
| Logging Python | `app/__init__.py` fonction `_setup_logging()` | Les erreurs sont ecrites dans les logs serveur avec date et niveau |
| Nettoyage RGPD | `app/models/log.py` `cleanup_old_logs()` | Suppression automatique des vieux logs au demarrage |

**Phrase cle pour l'oral :**
> "Chaque action utilisateur est tracee dans la table `logs` : connexion, upload, partage, etc. L'administrateur peut consulter ces logs filtres par utilisateur ou par type d'action. Les pages d'erreur 403/404/500 sont personnalisees pour guider l'utilisateur."

---

## Competence 3 : Developper la presence en ligne

**Ce que tu dois savoir expliquer :**
FamiliDocs est une application web responsive accessible via navigateur.

| Ce que tu as fait | Ou dans le code | Explication simple |
|---|---|---|
| Interface responsive | `app/templates/base.html` | Bootstrap 5.3 : s'adapte mobile/tablette/PC |
| Dashboard statistiques | `app/templates/dashboard.html` | Graphiques, compteurs, alertes visuelles |
| Recherche AJAX | `app/routes/search_routes.py` `global_search()` | Recherche instantanee sans recharger la page |
| Navigation intuitive | `app/templates/base.html` sidebar | Menu lateral avec icones, breadcrumbs, notifications |

**Phrase cle pour l'oral :**
> "L'interface utilise Bootstrap 5.3 pour etre responsive. Le dashboard affiche des statistiques en temps reel. La recherche globale fonctionne en AJAX : quand l'utilisateur tape, une requete est envoyee au serveur qui renvoie du JSON, et JavaScript affiche les resultats sans recharger la page."

---

## Competence 4 : Travailler en mode projet

**Ce que tu dois savoir expliquer :**
Le projet est organise en architecture MVC avec Git et des tests automatises.

| Ce que tu as fait | Ou dans le code | Explication simple |
|---|---|---|
| Architecture MVC | `app/models/`, `app/routes/`, `app/templates/` | Modeles = donnees, Routes = logique, Templates = affichage |
| 10 Blueprints Flask | `app/__init__.py` `_register_blueprints()` | Chaque Blueprint gere un domaine : auth, documents, taches, admin... |
| 7 Services | `app/services/` | Logique metier separee des routes (ex: DocumentService, BackupService) |
| 302 tests automatises | `tests/` (11 fichiers) | Tests modeles, services, routes, integration, securite, RGPD |
| Git versionning | `.git/` | Historique des modifications avec commits |
| Documentation | `docs/` | Doc technique, schema BDD, tableau E5, suivi ameliorations |

**Phrase cle pour l'oral :**
> "Le projet suit l'architecture MVC : les Modeles definissent les donnees avec SQLAlchemy, les Routes (controleurs) gerent les requetes HTTP, et les Templates (vues) affichent les pages HTML. Les 10 Blueprints Flask permettent de separer le code par fonctionnalite. J'ai ecrit 302 tests automatises avec pytest pour valider chaque composant."

---

## Competence 5 : Mettre a disposition un service informatique

**Ce que tu dois savoir expliquer :**
FamiliDocs est deploye et teste de bout en bout.

| Ce que tu as fait | Ou dans le code | Explication simple |
|---|---|---|
| 302 tests pytest | `tests/conftest.py` + `tests/test_*.py` | Fixtures pour BDD en memoire, tests unitaires et d'integration |
| Config multi-env | `app/config/config.py` | 3 configurations : Development (PostgreSQL), Testing (SQLite memoire), Production (PostgreSQL) |
| Version desktop | `desktop_launcher.py` | L'app peut aussi tourner en local sans serveur web |
| Notifications | `app/models/notification.py` | 11 types de notifications pour accompagner l'utilisateur |
| Messages flash | Partout dans les routes | Retours visuels a chaque action (succes, erreur, warning) |

**Phrase cle pour l'oral :**
> "J'ai ecrit 302 tests automatises repartis en tests unitaires (modeles, services), tests d'integration (enchainement de routes), et tests de securite (CSRF, injection, acces non autorise). L'application utilise PostgreSQL en developpement et production, et SQLite en memoire pour les tests (grace a l'ORM qui abstrait le SGBD). Elle peut aussi etre packagee en executable desktop."

---

## Competence 6 : Organiser son developpement professionnel

**Ce que tu dois savoir expliquer :**
Ce projet t'a permis d'apprendre et maitriser de nouvelles technologies.

| Ce que tu as fait | Preuve |
|---|---|
| Framework Flask | Architecture complete MVC |
| ORM SQLAlchemy | 13 modeles avec relations |
| Chiffrement AES (Fernet) | `app/services/encryption_service.py` |
| Hashage bcrypt | `app/services/auth_service.py` |
| Tests pytest | 302 tests dans 11 fichiers |
| RGPD/CNIL | Retention logs, export donnees, suppression compte |
| Bootstrap 5 | Interface responsive |
| Git | Versionning du code |

**Phrase cle pour l'oral :**
> "Ce projet m'a permis de maitriser Flask, SQLAlchemy et l'architecture MVC. J'ai appris a implementer la securite (bcrypt, chiffrement AES, CSRF) et la conformite RGPD. Mon portfolio est accessible a l'adresse m-sagar.vercel.app."

---

---

# PARTIE 2 : QUESTIONS PROBABLES DU JURY (avec reponses)

---

## ARCHITECTURE & CONCEPTION

### Q1 : "Expliquez l'architecture MVC de votre projet"

**Reponse :**
> MVC = Modele-Vue-Controleur. C'est un patron de conception qui separe le code en 3 couches :
> - **Modele** (`app/models/`) : definit les tables de la BDD et les regles metier. Exemple : `User` definit les colonnes email, username, password_hash et des methodes comme `is_admin()`.
> - **Vue** (`app/templates/`) : les fichiers HTML avec Jinja2 qui affichent les donnees. Exemple : `dashboard.html` affiche les statistiques.
> - **Controleur** (`app/routes/`) : recoit les requetes HTTP, appelle les modeles, et renvoie les vues. Exemple : la route `/documents` recupere les documents de l'utilisateur et les passe au template.
>
> En plus, j'ai ajoute une couche **Services** (`app/services/`) pour la logique metier complexe, ce qui allege les routes.

### Q2 : "Qu'est-ce qu'un Blueprint Flask ?"

**Reponse :**
> Un Blueprint est un moyen de regrouper des routes par fonctionnalite. Au lieu d'avoir toutes les routes dans un seul fichier, je les separe :
> - `auth_bp` : connexion, inscription, deconnexion
> - `document_bp` : upload, telechargement, partage de documents
> - `admin_bp` : gestion des utilisateurs, logs, sauvegardes
>
> Chaque Blueprint a son propre prefix d'URL. Exemple : `admin_bp` a le prefix `/admin`, donc toutes ses routes commencent par `/admin/...`.
>
> Fichier : `app/__init__.py` lignes 114-136, fonction `_register_blueprints()`

### Q3 : "Pourquoi avoir choisi SQLAlchemy plutot que du SQL brut ?"

**Reponse :**
> SQLAlchemy est un ORM (Object-Relational Mapping). Au lieu d'ecrire du SQL, on manipule des objets Python :
> ```python
> # Avec SQL brut :
> cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
>
> # Avec SQLAlchemy :
> user = User.query.filter_by(email=email).first()
> ```
> Avantages : plus lisible, protection contre les injections SQL, et surtout **changement de SGBD facile**. On utilise PostgreSQL en developpement et production, et SQLite en memoire pour les tests automatises, sans changer une seule ligne de code metier.
>
> Fichier : `app/models/user.py` - exemple de modele SQLAlchemy
> Fichier : `app/config/config.py` - `DevelopmentConfig` pointe vers PostgreSQL, `TestingConfig` vers SQLite

### Q4 : "Comment fonctionne la relation entre documents et dossiers ?"

**Reponse :**
> C'est une relation **1:N** (un-a-plusieurs) : un dossier peut contenir plusieurs documents, mais un document appartient a un seul dossier.
>
> Dans le modele `Document` (`app/models/document.py`) :
> ```python
> folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
> ```
> La cle etrangere `folder_id` fait reference a la table `folders`. SQLAlchemy cree automatiquement la relation grace a `db.relationship()` dans le modele `Folder`.

---

## SECURITE

### Q5 : "Comment sont stockes les mots de passe ?"

**Reponse :**
> Les mots de passe ne sont **jamais stockes en clair**. On utilise **bcrypt** pour les hasher.
>
> Fichier : `app/services/auth_service.py`
> ```python
> # Hashage a l'inscription
> password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
>
> # Verification a la connexion
> bcrypt.checkpw(password.encode('utf-8'), user.password_hash)
> ```
> bcrypt ajoute un "sel" (salt) aleatoire a chaque hashage, donc deux utilisateurs avec le meme mot de passe auront des hash differents. C'est irreversible : on ne peut pas retrouver le mot de passe a partir du hash.

### Q6 : "Qu'est-ce que la protection CSRF et pourquoi c'est important ?"

**Reponse :**
> CSRF = Cross-Site Request Forgery (falsification de requete inter-site).
>
> Sans protection, un site malveillant pourrait soumettre un formulaire vers FamiliDocs a l'insu de l'utilisateur connecte (ex: supprimer un document).
>
> Protection : Flask-WTF genere un **token unique** dans chaque formulaire. Quand le formulaire est soumis, le serveur verifie que le token est valide. Un site externe ne peut pas connaitre ce token.
>
> Fichier : `app/__init__.py` ligne 23 : `csrf = CSRFProtect()`
> Templates : chaque `<form>` contient automatiquement un champ cache avec le token.

### Q7 : "Comment fonctionne le chiffrement des documents ?"

**Reponse :**
> J'utilise le chiffrement **AES via Fernet** (bibliotheque `cryptography` de Python).
>
> Fichier : `app/services/encryption_service.py`
> - Une cle de chiffrement est generee et stockee dans un fichier `.encryption_key`
> - Quand on chiffre un document, on lit le fichier, on le chiffre avec Fernet, et on sauvegarde le resultat
> - Quand on telecharge, on dechiffre le fichier avant de l'envoyer
> - C'est du chiffrement **symetrique** : la meme cle sert a chiffrer et dechiffrer

### Q8 : "Comment gerez-vous les roles et permissions ?"

**Reponse :**
> Il y a deux niveaux de roles :
>
> **Roles applicatifs** (table `users`, colonne `role`) :
> - `admin` : acces total, gestion utilisateurs, logs, sauvegardes
> - `user` : utilisateur standard
> - `trusted` : personne de confiance (droits etendus)
>
> **Roles familiaux** (table `family_members`, colonne `role`) :
> - 8 roles hierarchiques : chef_famille, parent, tuteur, adulte, adolescent, enfant, invite, lecteur
>
> **Permissions documents** (table `permissions`) :
> - Droits granulaires par document : lecture, edition, telechargement, partage
> - Expiration automatique (date de fin)
>
> Fichiers : `app/models/user.py`, `app/models/family.py`, `app/models/permission.py`

### Q9 : "Qu'avez-vous fait pour la conformite RGPD ?"

**Reponse :**
> Plusieurs mesures :
> 1. **Chiffrement** des documents sensibles (AES/Fernet) - `encryption_service.py`
> 2. **Retention des logs** : suppression automatique apres X jours (configurable via `LOG_RETENTION_DAYS`) - `app/models/log.py`
> 3. **Suppression de compte** : l'utilisateur peut supprimer son compte et ses donnees - `app/routes/user_routes.py`
> 4. **Export de donnees** : l'utilisateur peut exporter ses donnees personnelles
> 5. **Hashage** des mots de passe (bcrypt) : les donnees sensibles ne sont jamais en clair
> 6. **Permissions expirables** : les acces partages ont une date d'expiration

### Q10 : "Quels en-tetes HTTP de securite avez-vous mis en place ?"

**Reponse :**
> Fichier : `app/__init__.py` fonction `_setup_security_headers()`
>
> 5 en-tetes :
> - `X-Content-Type-Options: nosniff` : empeche le navigateur de deviner le type MIME
> - `X-Frame-Options: SAMEORIGIN` : empeche l'affichage dans une iframe externe (protection clickjacking)
> - `X-XSS-Protection: 1; mode=block` : active le filtre anti-XSS du navigateur
> - `Referrer-Policy` : controle les informations envoyees dans le header Referer
> - `Cache-Control: no-cache` : empeche la mise en cache des pages sensibles

---

## BASE DE DONNEES

### Q11 : "Expliquez le schema de votre base de donnees"

**Reponse :**
> J'utilise **PostgreSQL** comme SGBD relationnel, avec 15 tables :
> - `users` : les utilisateurs (email, mot de passe hashe, role)
> - `documents` : les fichiers uploades (nom, type, taille, proprietaire)
> - `folders` : les dossiers pour organiser les documents
> - `permissions` : qui a acces a quel document (lecture, edition, partage)
> - `tasks` : les taches avec echeance et priorite
> - `logs` : journal de toutes les actions (21 types)
> - `notifications` : alertes pour les utilisateurs
> - `families` et `family_members` : groupes familiaux
> - `document_versions` : historique des versions de fichiers
> - `tags` et `document_tags` : etiquettes sur les documents (relation N:N)
> - `share_links` : liens de partage avec token
> - `messages` : chat familial
>
> PostgreSQL est configure dans `app/config/config.py` (`DevelopmentConfig`).
> Le schema complet est dans `docs/schema_bdd.md`.

### Q11b : "Pourquoi PostgreSQL et pas MySQL ?"

**Reponse :**
> PostgreSQL est un SGBD open-source reconnu pour sa robustesse et sa conformite SQL. Il gere bien les transactions ACID, les index, et les types de donnees avances. C'est aussi le SGBD le plus utilise avec Python/Flask en production. La connexion se fait via l'URI : `postgresql://jagadmin:pass@localhost:5432/familidocs` (fichier `app/config/config.py` ligne 129-130).

### Q12 : "Qu'est-ce qu'une relation N:N et ou l'utilisez-vous ?"

**Reponse :**
> N:N = plusieurs-a-plusieurs. Un document peut avoir plusieurs tags, et un tag peut etre sur plusieurs documents.
>
> En BDD, on utilise une **table d'association** `document_tags` avec deux cles etrangeres :
> ```python
> # Fichier : app/models/tag.py
> document_tags = db.Table('document_tags',
>     db.Column('document_id', db.Integer, db.ForeignKey('documents.id')),
>     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
> )
> ```

---

## FONCTIONNALITES

### Q13 : "Comment fonctionne le systeme de notifications ?"

**Reponse :**
> Fichier : `app/models/notification.py` et `app/services/notification_service.py`
>
> 11 types de notifications : tache en retard, document expire, document partage, etc.
>
> Fonctionnement :
> 1. Un service verifie periodiquement les echeances (`scheduler_service.py`)
> 2. Il cree des notifications dans la table `notifications`
> 3. Cote client, un script JavaScript interroge le serveur toutes les 60 secondes en AJAX
> 4. Le badge dans la sidebar affiche le nombre de notifications non lues

### Q14 : "Comment fonctionne le versioning des documents ?"

**Reponse :**
> Fichier : `app/routes/version_routes.py` et `app/models/document_version.py`
>
> Quand on uploade une nouvelle version :
> 1. On sauvegarde la version actuelle dans la table `document_versions`
> 2. On remplace le fichier du document principal par le nouveau
> 3. On peut telecharger n'importe quelle ancienne version
> 4. On peut restaurer une ancienne version (elle devient la version courante)

### Q15 : "Comment fonctionne la recherche AJAX ?"

**Reponse :**
> Fichier : `app/routes/search_routes.py` fonction `global_search()` et `app/static/js/app.js`
>
> 1. L'utilisateur tape dans la barre de recherche
> 2. JavaScript envoie une requete GET a `/search/global?q=...`
> 3. Le serveur cherche dans les documents, taches et tags de l'utilisateur
> 4. Il renvoie un JSON avec les resultats
> 5. JavaScript affiche les resultats dans un dropdown sans recharger la page

---

## TESTS

### Q16 : "Comment fonctionnent vos tests automatises ?"

**Reponse :**
> Outil : **pytest** (framework de test Python)
>
> Fichier de configuration : `tests/conftest.py`
> - Cree une application Flask en mode test (`TestingConfig`)
> - Utilise une BDD SQLite **en memoire** (pas de fichier, tout en RAM)
> - Fournit des **fixtures** : des objets pre-crees (utilisateur test, document test)
>
> Types de tests :
> - **Tests unitaires** : on teste chaque modele et service independamment
> - **Tests d'integration** : on teste un enchainement complet (ex: inscription → connexion → upload)
> - **Tests de securite** : on verifie qu'un utilisateur non-admin ne peut pas acceder a `/admin`
>
> Pour lancer : `python -m pytest tests/ -v`

### Q17 : "Qu'est-ce qu'une fixture pytest ?"

**Reponse :**
> Une fixture est une fonction qui prepare des donnees de test reutilisables.
>
> Fichier : `tests/conftest.py`
> ```python
> @pytest.fixture
> def test_user(app):
>     """Cree un utilisateur de test"""
>     user = User(email='test@test.com', username='testuser', ...)
>     db.session.add(user)
>     db.session.commit()
>     return user
> ```
> On l'utilise ensuite dans les tests en la passant en parametre :
> ```python
> def test_login(client, test_user):
>     # test_user est deja cree en BDD
>     response = client.post('/login', data={'email': 'test@test.com', ...})
> ```

---

---

# PARTIE 3 : MODIFICATIONS QU'ON POURRAIT TE DEMANDER

Le jury peut te demander de modifier du code en direct. Voici les scenarios les plus probables :

---

### Modification 1 : "Ajoutez un nouveau type de notification"

**Fichier a modifier :** `app/models/notification.py`
**Ligne :** 44-58 (dictionnaire `NOTIFICATION_TYPES`)

**Ce qu'il faut faire :**
```python
# Ajouter dans le dictionnaire NOTIFICATION_TYPES :
'family_joined': 'Nouveau membre dans la famille',
```

Puis dans `app/services/notification_service.py`, creer la methode qui envoie cette notification quand quelqu'un rejoint une famille.

---

### Modification 2 : "Ajoutez un nouveau champ au modele Document"

**Fichier a modifier :** `app/models/document.py`

**Ce qu'il faut faire :**
Ajouter une colonne, par exemple `priority` :
```python
priority = db.Column(db.String(20), default='normal')  # low, normal, high
```

Puis mettre a jour :
- Le formulaire d'upload dans `app/templates/documents.html`
- La route d'upload dans `app/routes/document_routes.py`
- Eventuellement les filtres de recherche dans `app/services/search_service.py`

---

### Modification 3 : "Ajoutez une nouvelle route qui affiche les taches en retard"

**Fichier a modifier :** `app/routes/task_routes.py`

**Ce qu'il faut faire :**
```python
@task_bp.route('/overdue')
@login_required
def overdue_tasks():
    """Affiche les taches en retard"""
    today = date.today()
    tasks = Task.query.filter(
        Task.owner_id == current_user.id,
        Task.due_date < today,
        Task.status != 'completed',
        Task.status != 'cancelled'
    ).order_by(Task.due_date).all()

    return render_template('overdue_tasks.html', tasks=tasks)
```

---

### Modification 4 : "Ajoutez une validation sur la taille du fichier uploade"

**Fichier a modifier :** `app/services/document_service.py`

**Ce qu'il faut faire :**
Dans la methode `upload_document()`, ajouter :
```python
# Verifier la taille du fichier (16 Mo max)
file.seek(0, 2)  # Aller a la fin du fichier
file_size = file.tell()  # Lire la position = taille
file.seek(0)  # Revenir au debut

if file_size > 16 * 1024 * 1024:
    return False, "Le fichier est trop volumineux (max 16 Mo)"
```

---

### Modification 5 : "Ajoutez un filtre par date dans la liste des documents"

**Fichier a modifier :** `app/routes/document_routes.py` fonction `list_documents()`

**Ce qu'il faut faire :**
Ajouter un parametre de requete et filtrer :
```python
date_from = request.args.get('date_from', '')
if date_from:
    try:
        date_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Document.created_at >= date_obj)
    except ValueError:
        pass  # Date invalide, on ignore
```

---

### Modification 6 : "Ajoutez un nouveau role utilisateur"

**Fichier a modifier :** `app/config/config.py`

**Ce qu'il faut faire :**
```python
USER_ROLES = {
    'admin': 'Administrateur',
    'user': 'Utilisateur',
    'trusted': 'Personne de confiance',
    'moderator': 'Moderateur'  # Nouveau role
}
```

Puis verifier dans les routes ou on teste `is_admin()` si le moderateur doit avoir des droits supplementaires. Fichier : `app/models/user.py`

---

### Modification 7 : "Ajoutez un compteur de telechargements sur les documents"

**Fichiers a modifier :**
1. `app/models/document.py` : ajouter la colonne
```python
download_count = db.Column(db.Integer, default=0)
```

2. `app/routes/document_routes.py` dans la route `download()` :
```python
document.download_count = document.download_count + 1
db.session.commit()
```

3. `app/templates/view_document.html` : afficher le compteur
```html
<p>Telecharge {{ document.download_count }} fois</p>
```

---

### Modification 8 : "Changez la duree de session de 2h a 30 minutes"

**Fichier a modifier :** `app/config/config.py` ligne 69

```python
# Avant :
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

# Apres :
PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
```

---

### Modification 9 : "Ajoutez un test pour verifier qu'un utilisateur ne peut pas supprimer le document d'un autre"

**Fichier a modifier :** `tests/test_routes.py`

```python
def test_cannot_delete_other_user_document(self):
    """Verifie qu'un utilisateur ne peut pas supprimer le document d'un autre"""
    # Creer un deuxieme utilisateur
    other_user = User(
        email='other@test.com',
        username='other',
        password_hash=AuthService.hash_password('Test1234!'),
        first_name='Other',
        last_name='User'
    )
    db.session.add(other_user)
    db.session.commit()

    # Se connecter avec le premier utilisateur
    self.client.post('/login', data={
        'email': 'test@test.com',
        'password': 'Test1234!'
    })

    # Essayer de supprimer le document de l'autre
    response = self.client.post(f'/documents/{other_doc_id}/delete')
    assert response.status_code in (302, 403)
```

---

### Modification 10 : "Ajoutez une API REST qui renvoie la liste des documents en JSON"

**Fichier a modifier :** `app/routes/document_routes.py`

```python
@document_bp.route('/api/list')
@login_required
def api_list_documents():
    """API JSON - Liste des documents de l'utilisateur"""
    documents = Document.query.filter_by(owner_id=current_user.id).all()

    documents_json = []
    for doc in documents:
        documents_json.append({
            'id': doc.id,
            'name': doc.name,
            'type': doc.file_type,
            'size': doc.file_size,
            'created_at': doc.created_at.isoformat()
        })

    return jsonify({'documents': documents_json})
```

---

---

# PARTIE 4 : VOCABULAIRE TECHNIQUE A CONNAITRE

| Terme | Definition simple |
|---|---|
| **MVC** | Patron de conception : Modele (donnees), Vue (affichage), Controleur (logique) |
| **ORM** | Object-Relational Mapping : manipuler la BDD (PostgreSQL, SQLite...) avec des objets Python au lieu de SQL |
| **Blueprint** | Moyen de regrouper des routes Flask par fonctionnalite |
| **CRUD** | Create, Read, Update, Delete : les 4 operations de base sur les donnees |
| **API REST** | Interface pour communiquer en HTTP (GET, POST, PUT, DELETE) avec du JSON |
| **AJAX** | Requete HTTP envoyee par JavaScript sans recharger la page |
| **CSRF** | Attaque qui force un utilisateur a executer une action a son insu |
| **XSS** | Injection de code JavaScript malveillant dans une page web |
| **Injection SQL** | Insertion de code SQL dans un champ de formulaire pour manipuler la BDD |
| **bcrypt** | Algorithme de hashage de mots de passe (irreversible, avec sel aleatoire) |
| **AES/Fernet** | Algorithme de chiffrement symetrique (meme cle pour chiffrer et dechiffrer) |
| **Token** | Chaine de caracteres unique et temporaire utilisee pour l'authentification |
| **Middleware** | Code execute avant/apres chaque requete (ex: en-tetes de securite) |
| **Fixture** | Donnees de test pre-preparees reutilisables (pytest) |
| **Migration** | Mise a jour du schema de BDD sans perdre les donnees existantes |
| **RGPD** | Reglement General sur la Protection des Donnees (loi europeenne) |
| **Hashage** | Transformation irreversible d'une donnee (ex: mot de passe → hash) |
| **Chiffrement** | Transformation reversible d'une donnee avec une cle (ex: fichier → fichier chiffre) |
| **Session** | Donnees stockees cote serveur pour identifier un utilisateur connecte |
| **Cookie** | Petit fichier stocke dans le navigateur pour maintenir la session |
| **Rate limiting** | Limitation du nombre de requetes pour empecher les attaques par force brute |

---

---

# PARTIE 5 : ARCHITECTURE DES FICHIERS (carte mentale)

```
FamiliDocs/
├── app/
│   ├── __init__.py          ← Factory Flask, creation de l'app
│   ├── config/
│   │   └── config.py        ← 3 configs : Dev, Test, Prod
│   ├── models/              ← MODELES (13 fichiers = 13 tables)
│   │   ├── user.py          ← Utilisateurs, roles, auth
│   │   ├── document.py      ← Documents uploades
│   │   ├── folder.py        ← Dossiers hierarchiques
│   │   ├── task.py          ← Taches avec echeances
│   │   ├── permission.py    ← Droits d'acces granulaires
│   │   ├── log.py           ← Journal des actions (21 types)
│   │   ├── notification.py  ← Alertes utilisateur (11 types)
│   │   ├── family.py        ← Familles et membres (8 roles)
│   │   ├── tag.py           ← Etiquettes (relation N:N)
│   │   ├── document_version.py ← Historique versions
│   │   ├── share_link.py    ← Liens de partage
│   │   └── message.py       ← Chat familial
│   ├── routes/              ← CONTROLEURS (10 blueprints)
│   │   ├── auth_routes.py   ← Connexion, inscription
│   │   ├── document_routes.py ← Upload, telechargement, partage
│   │   ├── task_routes.py   ← CRUD taches
│   │   ├── admin_routes.py  ← Administration
│   │   ├── family_routes.py ← Gestion familles
│   │   ├── user_routes.py   ← Profil, dashboard, activite
│   │   ├── notification_routes.py ← Notifications
│   │   ├── search_routes.py ← Recherche + tags
│   │   ├── version_routes.py ← Versioning documents
│   │   └── message_routes.py ← Chat
│   ├── services/            ← LOGIQUE METIER (7 services)
│   │   ├── auth_service.py  ← Hashage, validation, inscription
│   │   ├── document_service.py ← Upload, types fichiers
│   │   ├── permission_service.py ← Gestion des droits
│   │   ├── search_service.py ← Recherche multi-criteres
│   │   ├── notification_service.py ← Envoi notifications
│   │   ├── backup_service.py ← Sauvegardes ZIP
│   │   └── encryption_service.py ← Chiffrement AES
│   ├── templates/           ← VUES HTML (30+ fichiers)
│   └── static/              ← CSS, JS, images
├── tests/                   ← 302 TESTS (11 fichiers)
├── docs/                    ← Documentation
└── requirements.txt         ← Dependances Python
```

---

---

# PARTIE 6 : CHIFFRES CLES A RETENIR

| Metrique | Valeur |
|---|---|
| Modeles SQLAlchemy | 13 |
| Tables en BDD | 15 (13 + 2 associations) |
| Blueprints Flask | 10 |
| Services metier | 7 |
| Tests automatises | 302 |
| Types d'actions loggees | 21 |
| Types de notifications | 11 |
| Roles familiaux | 8 |
| Roles applicatifs | 3 |
| En-tetes de securite | 5 |
| Extensions fichiers acceptees | 10 |
| Taille max upload | 16 Mo |

---

---

# PARTIE 7 : CONSEILS POUR L'ORAL

1. **Commence toujours par le "pourquoi"** avant le "comment". Ex: "J'ai mis en place bcrypt **parce que** stocker les mots de passe en clair est une faille de securite majeure."

2. **Cite les fichiers** quand tu expliques. Ex: "Cette logique se trouve dans `app/services/auth_service.py`."

3. **Utilise les termes techniques** : MVC, ORM, Blueprint, CRUD, AJAX, CSRF, bcrypt, AES.

4. **Si tu ne sais pas**, dis "Je n'ai pas eu l'occasion d'implementer cette fonctionnalite, mais je sais que..." plutot que d'inventer.

5. **Prepare une demo** : montre l'inscription → connexion → upload → partage → notification en 2 minutes.

6. **Connais tes chiffres** : 302 tests, 13 modeles, 10 blueprints, 7 services, 15 tables.
