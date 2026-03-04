# SUIVI DES AMELIORATIONS - FamiliDocs v2.2

## Objectif
Passer le projet au niveau "vraiment lourd" pour BTS SIO SLAM + Version executable

---

## RESUME RAPIDE

| Categorie | Termine | En cours | A faire |
|-----------|---------|----------|---------|
| Fonctionnalites v2.0 | 8/8 | 0 | 0 |
| Bugs critiques v2.1 | 10/10 | 0 | 0 |
| Ameliorations partage | 6/6 | 0 | 0 |
| Gestion famille/roles | 7/7 | 0 | 0 |
| Nouvelles fonctionnalites | 6/6 | 0 | 0 |
| Qualite & Securite | 6/6 | 0 | 0 |
| Tests complets | 5/5 | 0 | 0 |
| Documentation | 4/4 | 0 | 0 |
| Audit & Correctifs finaux | 19/19 | 0 | 0 |
| Fonctionnalites manquantes (Phase 8) | 0/10 | 0 | 10 |
| UX & Qualite pro (Phase 9) | 0/10 | 0 | 10 |
| Tests supplementaires (Phase 10) | 0/6 | 0 | 6 |
| Polish & Finitions (Phase 11) | 0/8 | 0 | 8 |
| Version executable (Phase 12) | 0/2 | 0 | 2 |
| **TOTAL** | **71/107** | **0** | **36** |

---

## v2.0 - TERMINE (Sessions 1-2)

| # | Fonctionnalite | Statut | Date |
|---|----------------|--------|------|
| 1 | Notifications automatiques | TERMINE | 28/01/2026 |
| 2 | Versioning des documents | TERMINE | 29/01/2026 |
| 3 | Recherche avancee + Tags | TERMINE | 29/01/2026 |
| 4 | Dashboard ameliore | TERMINE | 29/01/2026 |
| 5 | Securite renforcee | TERMINE | 29/01/2026 |
| 6 | Tests unitaires (41+) | TERMINE | 29/01/2026 |
| 7 | Documentation technique | TERMINE | 29/01/2026 |
| 8 | Multi-utilisateurs | TERMINE | 29/01/2026 |

---

## v2.1 - TERMINE (Sauf executable)

### PHASE 1 : BUGS CRITIQUES - TERMINE

| # | Bug | Fichier concerne | Impact | Statut |
|---|-----|------------------|--------|--------|
| B1 | Template `create_task.html` manquant | `app/templates/` | /tasks/create inaccessible | TERMINE |
| B2 | Template `calendar.html` manquant | `app/templates/` | /tasks/calendar inaccessible | TERMINE |
| B3 | Template `view_task.html` manquant | `app/templates/` | Detail tache inaccessible | TERMINE |
| B4 | Template `edit_task.html` manquant | `app/templates/` | Edition tache impossible | TERMINE |
| B5 | Template `view_folder.html` manquant | `app/templates/` | Ouverture dossier impossible | TERMINE |
| B6 | Template `edit_folder.html` manquant | `app/templates/` | Edition dossier impossible | TERMINE |
| B7 | Template `edit_document.html` manquant | `app/templates/` | Edition document impossible | TERMINE |
| B8 | Erreur suppression document avec versions | `app/models/document_version.py` | IntegrityError NOT NULL | TERMINE |
| B9 | Template `overdue_tasks.html` manquant | `app/templates/` | /tasks/overdue inaccessible | TERMINE |
| B10 | Template `upcoming_tasks.html` manquant | `app/templates/` | /tasks/upcoming inaccessible | TERMINE |

---

### PHASE 2 : AMELIORATIONS PARTAGE - TERMINE

| # | Amelioration | Description | Fichiers | Statut |
|---|--------------|-------------|----------|--------|
| P1 | Exclure soi-meme du partage | Le partageur ne peut pas se selectionner | `permission_service.py` | TERMINE |
| P2 | Voir ses documents partages | Liste des docs qu'on a partage avec d'autres | `document_routes.py`, `my_shared_documents.html` | TERMINE |
| P3 | Selection multiple | Partager avec plusieurs personnes a la fois | `share_document.html`, `permission_service.py` | TERMINE |
| P4 | Duree max 90 jours | Limite de partage renouvelable | `permission_service.py`, `document_routes.py` | TERMINE |
| P5 | Partage dossiers complets | Partager un dossier = partager tous ses docs | `user_routes.py`, `share_folder.html` | TERMINE |
| P6 | Revocation auto exclusion famille | Quitter famille = perdre acces fichiers | `family_routes.py`, `permission_service.py` | TERMINE |

---

### PHASE 3 : GESTION FAMILLE ET ROLES - TERMINE

| # | Fonctionnalite | Description | Fichiers | Statut |
|---|----------------|-------------|----------|--------|
| F1 | Gestionnaire != Admin | Gestionnaire ne peut pas se promouvoir admin | `family_routes.py` | TERMINE |
| F2 | Gestionnaire != Virer membres | Seul admin/createur peut exclure editeurs+ | `family_routes.py` | TERMINE |
| F3 | 2 chefs de famille max | Role "chef_famille" limite a 2 par foyer | `family_routes.py` | TERMINE |
| F4 | Roles enfants/autres | Ajouter roles: enfant, parent, chef_famille | `family.py` | TERMINE |
| F5 | Affecter tache a membre | Assigner une tache a un membre famille | `task.py`, `task_routes.py`, `create_task.html` | TERMINE |
| F6 | Lien invitation smart | Invite -> connexion ou inscription | `family_routes.py`, `auth_routes.py`, `join_family.html` | TERMINE |
| F7 | Choix rejoindre famille | A l'inscription, option rejoindre famille | `register.html`, `auth_routes.py` | TERMINE |

**F6-F7 Details (Session 4) :**
- Route `/join/<token>` accessible sans connexion
- Stockage du token en session
- Affichage des infos famille sur login/register
- Connexion automatique apres inscription
- Redirection vers l'acceptation d'invitation

---

### PHASE 4 : NOUVELLES FONCTIONNALITES - TERMINE

| # | Fonctionnalite | Description | Fichiers | Statut |
|---|----------------|-------------|----------|--------|
| N1 | Messagerie/Chat famille | Chat public avec autorisations admin | `message.py`, `message_routes.py`, `chat.html` | TERMINE |
| N2 | Date MAJ obligatoire doc | Rappel de mise a jour document | `document.py`, `edit_document.html`, `view_document.html` | TERMINE |
| N3 | Photo de profil | Upload avatar + stockage | `user.py`, `profile.html`, `user_routes.py` | TERMINE |
| N4 | Titre/Role famille | Papa/Maman/Enfant/Autre affiche | `user.py`, `profile.html` | TERMINE |
| N5 | Historique pliable | Accordeon pour historique document | `view_document.html` (accordion Bootstrap) | TERMINE |
| N6 | Activite 6 mois cliquable | Page detail activite + admin voit famille | `user_routes.py`, `activity_detailed.html` | TERMINE |

**Phase 4 Details (Session 4) :**

**N1 - Chat Famille :**
- Modele `Message` avec annonces, soft delete
- Route `/families/<id>/chat` avec envoi/edition/suppression
- Interface temps reel avec liste membres
- Seuls admin/chef/parent peuvent poster des annonces
- Notifications pour les annonces

**N2 - Date revision obligatoire :**
- Champ `next_review_date` et `last_reviewed_at` dans Document
- Alertes sur view_document si revision requise
- Bouton "Marquer comme revise"
- Route `/documents/<id>/mark-reviewed`

**N3 - Photo de profil :**
- Champ `profile_photo` dans User
- Routes upload/delete avatar
- Affichage avec initiales si pas de photo
- Limite 2 Mo, formats JPG/PNG/GIF

**N4 - Titre familial :**
- Champ `family_title` dans User
- Selection Papa/Maman/Fils/Fille/etc.
- Propriete `display_name` formatee
- Affichage dans profil et chat

**N5 - Historique pliable :**
- Accordeon Bootstrap pour historique
- Section versions aussi pliable
- Icones selon type d'action
- Compteurs dans les headers

**N6 - Activite detaillee :**
- Page `/activity/detailed` avec filtres
- Statistiques sur la periode
- Filtres: periode (1w/1m/3m/6m), type d'action
- Admin/chef peut voir l'activite des membres famille

---

### PHASE 6 : QUALITE, SECURITE ET TESTS - TERMINE

#### 6A - Securite et qualite de code

| # | Amelioration | Description | Fichiers | Statut |
|---|--------------|-------------|----------|--------|
| S1 | Pages erreur personnalisees | Templates 403, 404, 500 pour error handlers | `app/templates/errors/` | TERMINE |
| S2 | .env.example | Documentation variables d'environnement | `.env.example` | TERMINE |
| S3 | Logging applicatif | Remplacement print() par logging Python | `notification_service.py` | TERMINE |
| S4 | Validation confidentialite | Validation serveur du niveau de confidentialite | `document_routes.py` | TERMINE |
| S5 | Config securisee | Cle secrete auto-generee, sessions HttpOnly/SameSite | `config.py` | TERMINE |
| S6 | Validation entrees taches | Titre obligatoire, date valide cote serveur | `task_routes.py` | TERMINE |

#### 6B - Tests complets (257 tests)

| # | Suite de tests | Nb tests | Description | Statut |
|---|----------------|----------|-------------|--------|
| T1 | test_models.py | 102 | Tous les modeles (User, Document, Task, Folder, Family, etc.) | TERMINE |
| T2 | test_services.py | 28 | AuthService, DocumentService, NotificationService | TERMINE |
| T3 | test_routes.py | 30 | Auth, Documents, Tasks, User, Admin, Erreurs, Headers | TERMINE |
| T4 | test_integration.py | 17 | Workflows complets multi-etapes | TERMINE |
| T5 | conftest.py | - | Fixtures partagees (app, client, users, documents) | TERMINE |

**Total : 257 tests (204 nouveaux + 53 existants) - TOUS PASSENT**

#### 6C - Documentation mise a jour

| # | Document | Modifications | Statut |
|---|----------|---------------|--------|
| D1 | schema_bdd.md | +4 tables (families, family_members, share_links, messages), +colonnes | TERMINE |
| D2 | documentation_technique.md | v2.1, 13 modeles, 10 blueprints, 257 tests, nouvelles features | TERMINE |
| D3 | tableau_E5.md | Features famille/chat, 257 tests, securite v2.1 | TERMINE |
| D4 | SUIVI_AMELIORATIONS.md | Phase 6 complete | TERMINE |

---

### PHASE 7 : AUDIT COMPLET & CORRECTIFS FINAUX - TERMINE

Audit approfondi du projet (routes, templates, services, securite, accessibilite, frontend) suivi de 3 rounds de correctifs.

#### 7A - Correctifs critiques et securite (Round 1)

| # | Correctif | Description | Fichiers | Statut |
|---|-----------|-------------|----------|--------|
| A1 | Templates admin manquants | Crash a la creation/edition d'utilisateur | `admin/create_user.html`, `admin/edit_user.html` | TERMINE |
| A2 | Bug context processor | `app_context_processor` n'existe pas sur Blueprint | `notification_routes.py:253` | TERMINE |
| A3 | Protection CSRF globale | CSRFProtect + meta tag + auto-injection JS dans tous les formulaires POST | `__init__.py`, `base.html` | TERMINE |
| A4 | .gitignore manquant | venv, __pycache__, .db, .idea dans le repo | `.gitignore` | TERMINE |
| A5 | README complet | Documentation complete du projet (features, stack, install, tests, securite) | `README.md` | TERMINE |
| A6 | URL hardcodee chat | URL JS hardcodee remplacee par `url_for()` + token CSRF dans modal | `chat.html:184` | TERMINE |
| A7 | Validation content-type | Verification MIME type a l'upload (PDF, Word, Excel, images, texte) | `document_service.py:61-70` | TERMINE |

#### 7B - Correctifs fonctionnels (Round 2)

| # | Correctif | Description | Fichiers | Statut |
|---|-----------|-------------|----------|--------|
| A8 | Endpoint version casse | `version.download` → `version.download_version` avec document_id + version_id | `view_document.html:200` | TERMINE |
| A9 | Icone type fichier invalide | `bi-file-earmark-other` n'existe pas → conditionnel avec fallback | `view_document.html:34` | TERMINE |
| A10 | Clipboard sans .catch() | Ajout fallback `execCommand` pour navigateurs sans Clipboard API | `share_document.html:316` | TERMINE |
| A11 | Chemin BDD fragile backup | Remplacement hack `UPLOAD_FOLDER/../` par parsing `SQLALCHEMY_DATABASE_URI` | `backup_service.py:42` | TERMINE |
| A12 | Guard URL calendrier | Protection contre `event.url` undefined dans le modal calendrier | `calendar.html:111` | TERMINE |
| A13 | Flask-Migrate | Ajout du systeme de migrations BDD (Alembic) | `requirements.txt`, `__init__.py` | TERMINE |

#### 7C - Qualite et accessibilite (Round 3)

| # | Correctif | Description | Fichiers | Statut |
|---|-----------|-------------|----------|--------|
| A14 | Fetch sans .catch() | Ajout `.catch()` sur le refresh compteur notifications | `base.html:222` | TERMINE |
| A15 | Context processor duplique | Suppression du doublon dans notification_routes (deja dans __init__.py) | `notification_routes.py:252-260` | TERMINE |
| A16 | Accessibilite clavier | `div onclick` remplaces par `<a href>` sur les cartes familles | `families.html:19,44` | TERMINE |
| A17 | Validation avatar type | Verification JS du type fichier (JPG/PNG/GIF) avant upload | `profile.html:199` | TERMINE |
| A18 | Accessibilite chat | Ajout `aria-label="Message"` sur l'input du chat | `chat.html:85` | TERMINE |

**Total Phase 7 : 18 correctifs + 1 ajout (Flask-Migrate) = 19 taches - TOUTES TERMINEES**

**257 tests - TOUS PASSENT apres chaque round de correctifs**

---

### PHASE 5 : VERSION EXECUTABLE - PRET A BUILDER

| # | Tache | Description | Outils | Statut |
|---|-------|-------------|--------|--------|
| E1 | Creer executable .exe | Application desktop standalone | PyInstaller | PRET |

**Fichiers crees pour l'executable :**
- `desktop_launcher.py` - Lanceur adapte pour mode desktop
- `familidocs.spec` - Configuration PyInstaller complete
- `build_exe.bat` - Script de build automatique Windows

**Pour creer l'executable (Windows) :**
```batch
REM Double-cliquer sur build_exe.bat
REM OU executer manuellement:
venv\Scripts\activate
pip install pyinstaller
pyinstaller familidocs.spec
```

**Resultat :**
- L'executable sera dans `dist\FamiliDocs.exe`
- Les donnees utilisateur seront stockees dans `%USERPROFILE%\.familidocs\`
- La base de donnees SQLite sera creee automatiquement
- Le navigateur s'ouvre automatiquement au lancement

---

## FICHIERS CREES/MODIFIES - SESSION 4

### Nouveaux fichiers :
- `app/models/message.py` - Modele Message pour chat
- `app/routes/message_routes.py` - Routes chat
- `app/templates/chat.html` - Interface chat famille
- `app/templates/join_family.html` - Page invitation smart
- `app/templates/activity_detailed.html` - Activite detaillee

### Fichiers modifies :
- `app/models/__init__.py` - Import Message
- `app/models/user.py` - profile_photo, family_title, initials, display_name
- `app/models/document.py` - next_review_date, last_reviewed_at, needs_review
- `app/__init__.py` - Register message_bp
- `app/routes/auth_routes.py` - Gestion invitations pending
- `app/routes/family_routes.py` - Route /join/<token>
- `app/routes/user_routes.py` - Avatar upload, activity_detailed
- `app/routes/document_routes.py` - mark_reviewed route
- `app/services/document_service.py` - next_review_date update
- `app/templates/login.html` - Affichage invitation pending
- `app/templates/register.html` - Affichage invitation pending
- `app/templates/profile.html` - Photo + titre + stats
- `app/templates/view_document.html` - Accordeon historique + review
- `app/templates/edit_document.html` - Champ next_review_date
- `app/templates/view_family.html` - Bouton chat + lien smart
- `app/templates/dashboard.html` - Lien vers activite detaillee
- `app/templates/activity.html` - Lien vers activite detaillee

---

## COMMANDES UTILES

```bash
# Environnement
python -m venv venv
venv\Scripts\activate  # Windows

# Dependances
pip install -r requirements.txt

# Lancer l'app
set PYTHONPATH=.python -m app.main
# URL: http://localhost:5000
# Admin: admin@familidocs.local / Admin123!

# Tests
pytest tests/ -v
pytest tests/ --cov=app -v

# Creer executable
pip install pyinstaller
pyinstaller --onefile --windowed app/main.py
```

---

## HISTORIQUE DES SESSIONS

| Session | Date | Travail | Statut |
|---------|------|---------|--------|
| 1 | 28/01/2026 | Notifications completes | TERMINE |
| 2 | 29/01/2026 | Versioning + Tags + Recherche + Dashboard + Securite + Tests | TERMINE |
| 3 | 09/02/2026 | Bugs critiques + Phase 2 Partage + Phase 3 Famille (partiel) | TERMINE |
| 4 | 09/02/2026 | Phase 3 complete + Phase 4 complete | TERMINE |
| 5 | 20/02/2026 | Phase 6 : Securite + 257 tests + Documentation | TERMINE |
| 6 | 20/02/2026 | Phase 7 : Audit complet + 19 correctifs finaux | TERMINE |

**Session 4 - Details :**
- Invitation smart (F6) : Route /join accessible sans login
- Rejoindre famille a l'inscription (F7) : Token en session + auto-join
- Chat famille (N1) : Modele Message + routes + template complet
- Photo de profil (N3) : Upload/delete + affichage initiales
- Titre familial (N4) : Selection dans profil
- Date revision (N2) : Champs + alertes + action marquer
- Historique pliable (N5) : Accordeon Bootstrap
- Activite detaillee (N6) : Stats + filtres + vue famille

**Session 5 - Details (Phase 6) :**
- Templates erreur 403/404/500 pour les error handlers existants
- .env.example documente avec commandes de generation des cles
- Remplacement print() par logging.getLogger dans notification_service
- Validation confidentialite serveur dans document_routes (upload)
- Config securisee : SECRET_KEY auto-generee, sessions HttpOnly/SameSite
- Validation entrees taches : titre obligatoire, format date, cote serveur
- 204 nouveaux tests (102 modeles, 28 services, 30 routes, 17 integration)
- conftest.py refait avec fixtures partagees (function-scoped pour isolation)
- Documentation technique mise a jour (v2.1, 13 modeles, 10 blueprints, 257 tests)
- Schema BDD mis a jour (+4 tables, +colonnes)
- Tableau E5 mis a jour avec toutes les nouvelles features et tests

**Session 6 - Details (Phase 7 - Audit & Correctifs finaux) :**

*Round 1 - Critiques et securite :*
- 2 templates admin manquants crees (create_user, edit_user)
- Bug `app_context_processor` corrige sur blueprint notification
- Protection CSRF globale : CSRFProtect + meta tag + auto-injection JS tous formulaires
- .gitignore cree (venv, pycache, db, ide, dist, build)
- README.md reecrit complet (features, stack, install, tests, securite, archi)
- URL hardcodee chat → url_for() + CSRF token dans modal edition
- Validation content-type MIME a l'upload de documents

*Round 2 - Fonctionnels :*
- Endpoint version download casse corrige (document_id + version_id)
- Icone Bootstrap invalide pour type "other" → conditionnel avec fallback
- Clipboard API sans .catch() → ajout fallback execCommand
- Chemin BDD fragile dans backup_service → parsing SQLALCHEMY_DATABASE_URI
- Guard URL undefined dans modal calendrier
- Flask-Migrate 4.0.5 ajoute et initialise (systeme de migrations Alembic)

*Round 3 - Qualite et accessibilite :*
- .catch() manquant sur refresh compteur notifications
- Context processor notifications duplique supprime
- Accessibilite clavier : div onclick → balises <a> dans familles
- Validation type fichier avatar en JS (JPG/PNG/GIF)
- aria-label ajoute sur input chat

*Fichiers crees :*
- `app/templates/admin/create_user.html`
- `app/templates/admin/edit_user.html`
- `.gitignore`

*Fichiers modifies :*
- `app/__init__.py` - CSRFProtect + Flask-Migrate
- `app/routes/notification_routes.py` - Fix context_processor + suppression doublon
- `app/services/document_service.py` - Validation content-type MIME
- `app/services/backup_service.py` - Fix chemin BDD
- `app/templates/base.html` - Meta CSRF + auto-inject JS + .catch() notifs
- `app/templates/view_document.html` - Fix endpoint version + icone type
- `app/templates/share_document.html` - .catch() clipboard + fallback
- `app/templates/chat.html` - url_for() + CSRF modal + aria-label
- `app/templates/calendar.html` - Guard URL event
- `app/templates/families.html` - Accessibilite clavier <a>
- `app/templates/profile.html` - Validation type avatar
- `requirements.txt` - Flask-Migrate 4.0.5
- `README.md` - Reecrit complet

---

## TACHES A EFFECTUER - PROCHAINE SESSION

> Audit complet realise le 20/02/2026. Liste exhaustive pour rendre le logiciel fonctionnel a 200%.

---

### PHASE 8 : FONCTIONNALITES MANQUANTES (CRITIQUE)

| # | Tache | Description | Fichiers concernes | Effort |
|---|-------|-------------|-------------------|--------|
| T1 | Scheduler de taches planifiees | APScheduler pour declencher automatiquement : notifications echeances, nettoyage notifications expirees, nettoyage vieilles sauvegardes. Actuellement tout est manuel (`/notifications/check-due` doit etre appele a la main). | `requirements.txt`, `__init__.py`, `main.py` | ELEVE |
| T2 | Pagination documents | La liste documents n'a PAS de pagination → crash si +100 docs. Ajouter `.paginate()` cote route + UI pagination Bootstrap dans le template. | `document_routes.py`, `documents.html` | MOYEN |
| T3 | Pagination taches | Idem pour la liste des taches. | `task_routes.py`, `tasks.html` | MOYEN |
| T4 | Pagination resultats recherche | Les resultats de recherche avancee ne sont pas pagines. | `search_routes.py`, `search.html` | MOYEN |
| T5 | Pagination tags | La liste des tags n'est pas paginee. | `search_routes.py`, `tags.html` | FAIBLE |
| T6 | Pagination dossiers | La liste des dossiers n'est pas paginee. | `user_routes.py`, `folders.html` | FAIBLE |
| T7 | Route export RGPD | `BackupService.export_user_data()` existe mais AUCUNE route pour y acceder. Ajouter `/profile/export-data` qui retourne un JSON/ZIP des donnees personnelles. Obligatoire conformite RGPD. | `user_routes.py`, `profile.html` | MOYEN |
| T8 | Integration chiffrement AES | `EncryptionService` existe (`encryption_service.py`) avec encrypt/decrypt mais n'est JAMAIS appele. Integrer : chiffrer a l'upload si `confidentiality='restricted'`, dechiffrer au download. Ajouter indicateur visuel (cadenas) dans le template. | `document_service.py`, `document_routes.py`, `view_document.html` | ELEVE |
| T9 | Notifications partage document | Quand on partage un document, le destinataire ne recoit AUCUNE notification. Appeler `NotificationService.notify_permission_granted()` apres `grant_multiple_permissions()`. | `document_routes.py:337`, `notification_service.py` | FAIBLE |
| T10 | Notifications assignation tache | Quand on assigne une tache a un membre famille, pas de notification envoyee. | `task_routes.py`, `notification_service.py` | FAIBLE |

---

### PHASE 9 : UX ET QUALITE PROFESSIONNELLE

| # | Tache | Description | Fichiers concernes | Effort |
|---|-------|-------------|-------------------|--------|
| T11 | Preservation saisie formulaires | Quand un formulaire echoue (validation), les champs sont vides → l'utilisateur doit tout retaper. Passer les valeurs saisies au template et ajouter `value="{{ request.form.get('field', '') }}"` sur tous les inputs. | `register.html`, `login.html`, `create_task.html`, `create_folder.html`, `create_family.html`, `upload_document.html`, `edit_task.html`, `edit_document.html` + routes correspondantes | ELEVE |
| T12 | Validation inline champs | Afficher les erreurs sous chaque champ avec les classes Bootstrap `is-invalid` / `invalid-feedback` au lieu d'un seul flash message generique en haut de page. | Memes templates que T11 | ELEVE |
| T13 | Message de bienvenue | Apres inscription, afficher un message d'accueil avec les prochaines etapes : "Bienvenue ! Commencez par uploader un document ou creer un groupe familial." | `auth_routes.py` (register), `dashboard.html` | FAIBLE |
| T14 | Confirmation suppression tache | La suppression de tache n'a PAS de dialog de confirmation `confirm()`. Ajouter `onsubmit="return confirm('...')"` sur le formulaire de suppression. | `view_task.html`, `tasks.html` | FAIBLE |
| T15 | Barre de recherche navbar | Ajouter un champ de recherche rapide directement dans la navbar (actuellement c'est juste un lien vers la page recherche). Recherche AJAX avec suggestions. | `base.html`, `search_routes.py` (ajouter endpoint API) | MOYEN |
| T16 | Tri colonnes listes | Permettre de trier les documents et taches par nom, date, taille, priorite en cliquant sur les en-tetes de colonnes. | `documents.html`, `tasks.html`, `document_routes.py`, `task_routes.py` | MOYEN |
| T17 | Operations en masse | Ajouter des checkboxes sur les listes documents/taches + barre d'actions : supprimer en masse, deplacer dans un dossier, partager en masse. | `documents.html`, `tasks.html`, `document_routes.py`, `task_routes.py` | ELEVE |
| T18 | Barre de progression upload | Afficher une barre de progression pendant l'upload de fichiers (via XMLHttpRequest ou fetch avec progress event). | `upload_document.html`, `document_versions.html` | MOYEN |
| T19 | CSS impression | Ajouter `@media print` dans style.css pour cacher la navbar, sidebar, footer. Ajouter un bouton "Imprimer" sur la vue document et la vue tache. | `style.css`, `view_document.html`, `view_task.html` | FAIBLE |
| T20 | Avertissement expiration session | Afficher un modal 2 minutes avant l'expiration de la session (2h) : "Votre session expire bientot. Cliquez pour rester connecte." avec un bouton qui fait un ping au serveur. | `base.html` (JS), config session lifetime | MOYEN |

---

### PHASE 10 : TESTS SUPPLEMENTAIRES

| # | Tache | Description | Fichiers concernes | Effort |
|---|-------|-------------|-------------------|--------|
| T21 | Tests famille complets | Tests dedies pour : creation famille, invitation, gestion roles, exclusion membre, suppression famille. Actuellement melange dans test_models et test_integration. | `tests/test_family.py` (nouveau) | MOYEN |
| T22 | Tests chat/messagerie | Tests pour : envoi message, edition, suppression, annonces, droits par role. | `tests/test_messages.py` (nouveau) | MOYEN |
| T23 | Tests liens de partage | Tests pour : creation lien, expiration, nombre d'utilisations, revocation, acceptation. | `tests/test_share_links.py` (nouveau) | MOYEN |
| T24 | Tests admin complets | Tests pour : creation/edition/suppression user, reset password, backup create/restore/delete, logs. | `tests/test_admin.py` (nouveau) | MOYEN |
| T25 | Tests encryption | Tests pour : chiffrement/dechiffrement fichier, gestion cle manquante, round-trip. | `tests/test_encryption.py` (nouveau) | FAIBLE |
| T26 | Tests RGPD export | Tests pour : export donnees user, format JSON correct, completude des donnees. | `tests/test_rgpd.py` (nouveau) | FAIBLE |

---

### PHASE 11 : POLISH ET FINITIONS

| # | Tache | Description | Fichiers concernes | Effort |
|---|-------|-------------|-------------------|--------|
| T27 | Tooltips features complexes | Ajouter des tooltips explicatifs sur : niveaux confidentialite, roles famille, jours de rappel tache, dates revision document. | `share_document.html`, `view_family.html`, `create_task.html`, `edit_document.html` | FAIBLE |
| T28 | Widget famille dashboard | Ajouter sur le dashboard un encart "Mes familles" avec acces rapide aux groupes et nombre de messages non lus. | `dashboard.html`, `user_routes.py` | FAIBLE |
| T29 | Widget notifications dashboard | Ajouter sur le dashboard un resume des dernieres notifications avec lien "Voir tout". | `dashboard.html`, `user_routes.py` | FAIBLE |
| T30 | Tables responsive mobile | Verifier que toutes les tables (documents, taches, versions, partages) ont `table-responsive` et testent correctement sur mobile. Ajouter colonnes cachees sur petits ecrans si besoin. | `documents.html`, `tasks.html`, `shared_documents.html`, `document_versions.html`, `search.html` | MOYEN |
| T31 | Breadcrumbs manquants | Ajouter le fil d'Ariane sur : dashboard, notifications, activite, profil, liste dossiers. | `dashboard.html`, `notifications.html`, `activity.html`, `profile.html`, `folders.html` | FAIBLE |
| T32 | Mode sombre | Ajouter un toggle dark mode dans la navbar. Utiliser les CSS variables Bootstrap et `data-bs-theme="dark"`. | `base.html`, `style.css`, `app.js` | MOYEN |
| T33 | Favicon et branding | Ajouter un favicon, un logo dans la navbar, et un logo sur la page login/register. | `base.html`, `login.html`, `register.html`, `static/img/` | FAIBLE |
| T34 | Raccourcis clavier | Ajouter : Ctrl+K pour recherche rapide, Escape pour fermer modals, Ctrl+S dans formulaires d'edition. | `base.html` (JS), `app.js` | FAIBLE |

---

### PHASE 12 : VERSION EXECUTABLE

| # | Tache | Description | Fichiers concernes | Effort |
|---|-------|-------------|-------------------|--------|
| E1 | Creer executable .exe | Application desktop standalone avec PyInstaller | `familidocs.spec`, `build_exe.bat`, `desktop_launcher.py` | ELEVE |
| E2 | Test executable | Tester sur machine sans Python : lancement, base auto-creee, navigateur auto-ouvert | Machine de test | MOYEN |

---

### RESUME DES TACHES PAR PRIORITE

| Priorite | Taches | Description |
|----------|--------|-------------|
| **CRITIQUE** | T1, T2, T3, T7, T8 | Scheduler, pagination, RGPD, chiffrement |
| **HAUTE** | T4, T9, T10, T11, T12, T14, T17 | Pagination recherche, notifications, validation formulaires, operations masse |
| **MOYENNE** | T5, T6, T13, T15, T16, T18, T20, T21-T26, T30, T32 | Pagination restante, UX, tests, responsive, dark mode |
| **BASSE** | T19, T27, T28, T29, T31, T33, T34 | Impression, tooltips, dashboard widgets, breadcrumbs, branding, raccourcis |
| **EXECUTABLE** | E1, E2 | Build et test .exe |

**Total : 36 taches (T1-T34 + E1-E2)**

---

### ESTIMATION EFFORT GLOBAL

| Phase | Nb taches | Effort estime |
|-------|-----------|---------------|
| Phase 8 - Fonctionnalites manquantes | 10 | ~4-6h |
| Phase 9 - UX et qualite pro | 10 | ~4-6h |
| Phase 10 - Tests supplementaires | 6 | ~2-3h |
| Phase 11 - Polish et finitions | 8 | ~2-3h |
| Phase 12 - Version executable | 2 | ~1-2h |
| **TOTAL** | **36** | **~13-20h** |

---

*Derniere mise a jour : 20/02/2026 - Session 6 terminee - 71/72 taches completes (hors TODO) - Audit complet realise*
