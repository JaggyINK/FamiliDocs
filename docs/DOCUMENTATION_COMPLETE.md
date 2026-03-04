# FamiliDocs - Documentation Complete du Projet

## Table des matieres

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Configuration et BDD](#3-configuration-et-bdd)
4. [Modeles (app/models/)](#4-modeles-appmodels)
5. [Services (app/services/)](#5-services-appservices)
6. [Routes (app/routes/)](#6-routes-approutes)
7. [Templates (app/templates/)](#7-templates-apptemplates)
8. [Fichiers statiques (app/static/)](#8-fichiers-statiques-appstatic)
9. [Tests (tests/)](#9-tests-tests)
10. [Fichiers racine](#10-fichiers-racine)
11. [Securite et autorisation](#11-securite-et-autorisation)
12. [Recapitulatif des modifications](#12-recapitulatif-des-modifications)
13. [Comment verifier que tout fonctionne](#13-comment-verifier-que-tout-fonctionne)

---

## 1. Vue d'ensemble

FamiliDocs est une application web Flask de gestion documentaire familiale.
Elle permet a des familles de stocker, organiser, partager et proteger leurs documents administratifs.

**Technologies** : Flask 3.0, SQLAlchemy 2.0, **PostgreSQL 16** (principal), Bootstrap 5, Fernet (AES), bcrypt

**Chiffres cles** :
- 13 modeles de donnees
- 8 services metier
- 10 blueprints (modules de routes)
- 88 endpoints (routes API/pages)
- 44 templates HTML
- 302 tests automatises (100% passent)

---

## 2. Architecture du projet

```
FamiliDocs/
|-- app/                          # Application Flask principale
|   |-- __init__.py               # Factory create_app(), blueprints, scheduler
|   |-- config/
|   |   |-- config.py             # Configuration dev/testing/prod + secret key
|   |-- database/
|   |   |-- familidocs.db         # Fichier local (fallback .exe uniquement)
|   |   |-- .secret_key           # Cle secrete persistante (auto-generee)
|   |-- models/                   # 13 modeles SQLAlchemy
|   |   |-- __init__.py           # Import central de tous les modeles
|   |   |-- user.py               # Utilisateurs
|   |   |-- document.py           # Documents
|   |   |-- folder.py             # Dossiers
|   |   |-- task.py               # Taches/rappels
|   |   |-- family.py             # Familles + FamilyMember + ShareLink
|   |   |-- permission.py         # Permissions de partage
|   |   |-- notification.py       # Notifications
|   |   |-- log.py                # Journaux d'audit
|   |   |-- tag.py                # Tags + table d'association
|   |   |-- document_version.py   # Versions de documents
|   |   |-- message.py            # Messages de chat familial
|   |-- routes/                   # 10 blueprints
|   |   |-- auth_routes.py        # Authentification
|   |   |-- user_routes.py        # Dashboard, profil, dossiers
|   |   |-- document_routes.py    # CRUD documents
|   |   |-- task_routes.py        # CRUD taches
|   |   |-- family_routes.py      # Gestion des familles
|   |   |-- admin_routes.py       # Administration
|   |   |-- notification_routes.py# Notifications
|   |   |-- search_routes.py      # Recherche et tags
|   |   |-- version_routes.py     # Versions de documents
|   |   |-- message_routes.py     # Chat familial
|   |-- services/                 # 8 services metier
|   |   |-- auth_service.py       # Authentification + rate limiting
|   |   |-- document_service.py   # Logique documents + chiffrement
|   |   |-- backup_service.py     # Sauvegarde/restauration + export RGPD
|   |   |-- notification_service.py# Gestion des notifications
|   |   |-- permission_service.py # Controle d'acces aux documents
|   |   |-- search_service.py     # Recherche multicritere + stats
|   |   |-- scheduler_service.py  # Planificateur de taches de fond
|   |   |-- encryption_service.py # Chiffrement AES (Fernet)
|   |-- templates/                # 44 templates Jinja2
|   |-- static/
|       |-- css/style.css         # Styles + responsive + print + dark mode
|       |-- js/app.js             # JS: tooltips, upload, bulk, session, raccourcis
|       |-- img/favicon.svg       # Favicon SVG
|-- tests/                        # 15 fichiers de tests (302 tests)
|-- docs/                         # Documentation
|-- desktop_app.py                # Lanceur desktop (CustomTkinter + Flask)
|-- desktop_launcher.py           # Lanceur desktop alternatif (navigateur)
|-- build_exe.bat                 # Script de creation .exe (PyInstaller)
|-- familidocs.spec               # Config PyInstaller
|-- requirements.txt              # 36 dependances Python
|-- .env.example                  # Template de configuration
|-- .gitignore                    # Exclusions Git
```

---

## 3. Configuration et BDD

### Base de donnees : PostgreSQL (principal)

L'application utilise **PostgreSQL** comme base de donnees principale.

**Connexion PostgreSQL** (definie dans `.env`) :
```
DATABASE_URL=postgresql://jagadmin:pass@localhost:5432/familidocs
```

- **Host** : 127.0.0.1
- **Port** : 5432
- **Base** : familidocs
- **Utilisateur** : jagadmin
- **Authentification** : Database Native

### Fichier : `app/config/config.py`

Gere 3 environnements :

| Environnement | BDD | Usage |
|---|---|---|
| **development** | **PostgreSQL** `postgresql://jagadmin:pass@localhost:5432/familidocs` | Dev local (web + exe) |
| **testing** | SQLite `:memory:` (en memoire, ephemere) | Tests pytest uniquement |
| **production** | Variable `DATABASE_URL` (PostgreSQL obligatoire) | Production |

Options PostgreSQL configurees automatiquement :
- `pool_size: 10` - Connexions simultanees
- `max_overflow: 20` - Connexions supplementaires
- `pool_pre_ping: True` - Verification connexion avant utilisation
- `pool_recycle: 300` - Recyclage toutes les 5 minutes

### Partage BDD web / exe

La version web et le desktop **.exe** partagent la **meme base PostgreSQL** :

1. Le fichier `.env` definit `DATABASE_URL=postgresql://...`
2. Les deux lanceurs (`desktop_launcher.py`, `desktop_app.py`) chargent `.env`
3. La condition `is_shared_mode = db_url.startswith('postgresql')` detecte PostgreSQL
4. En mode PostgreSQL : les deux versions accedent a la meme BDD, les memes uploads, les memes backups

**Fallback SQLite** (uniquement si .exe compile SANS PostgreSQL disponible) :
- Si `DATABASE_URL` n'est PAS defini ET qu'on est en mode `.exe` (`getattr(sys, 'frozen', False)`)
- Alors : SQLite dans `~/.familidocs/familidocs.db`
- Ce cas ne se produit PAS en dev normal

### Sauvegarde selon le type de BDD

Le `BackupService` detecte automatiquement le type de BDD :
- **PostgreSQL** : export JSON via SQLAlchemy (toutes les tables serialisees en JSON)
- **SQLite** (fallback .exe) : copie directe du fichier `.db`

### Cle secrete

Generee automatiquement via `secrets.token_hex(32)` et stockee dans `app/database/.secret_key` pour persister entre les redemarrages (sinon les sessions sont invalidees).

---

## 4. Modeles (app/models/)

### `__init__.py`
Import central de tous les modeles. Initialise `db = SQLAlchemy()`. Tout import de modele passe par ce fichier.

### `user.py` - Modele User
- **Champs** : email, username, password_hash, first_name, last_name, role, is_active, avatar, last_login, created_at
- **Roles** : `user`, `trusted`, `admin`
- **Methodes cles** :
  - `is_admin()` : verifie si role == admin
  - `can_access_document(doc)` : proprietaire OU admin OU permission valide
  - `can_edit_document(doc)` : proprietaire OU admin OU permission can_edit
  - `full_name` : prenom + nom

### `document.py` - Modele Document
- **Champs** : name, original_filename, stored_filename, file_type, file_size, description, confidentiality, expiry_date, next_review_date, last_reviewed_at, is_encrypted, owner_id, folder_id
- **Relations** : owner (User), folder (Folder), permissions, tasks, versions, tags, share_links
- **Proprietes** : is_expired, is_expiring_soon, days_until_expiry, needs_review, review_soon

### `folder.py` - Modele Folder
- **Champs** : name, category, description, owner_id, parent_id
- **Self-join** : dossiers imbriques via parent_id
- **Categories** : Administratif, Sante, Finance, Education, etc.

### `task.py` - Modele Task
- **Champs** : title, description, due_date, priority, status, reminder_days, completed_at, owner_id, assigned_to_id, document_id
- **Statuts** : pending, in_progress, completed, cancelled
- **Priorites** : low, normal, high, urgent
- **Methodes** : is_overdue, is_due_soon, days_until_due, priority_color

### `family.py` - Modeles Family, FamilyMember, ShareLink
- **Family** : name, description, creator_id + relation vers membres
- **FamilyMember** : family_id, user_id, role, invited_by, joined_at
  - Roles : chef_famille, admin, parent, gestionnaire, membre, enfant, lecteur
- **ShareLink** : token, document_id, family_id, created_by, expires_at, max_uses, use_count, is_revoked, granted_role
  - `is_valid` : verifie expiration + revocation + limite d'utilisation
  - `create_share_link()` : methode statique pour creer un lien securise

### `permission.py` - Modele Permission
- **Champs** : document_id, user_id, can_view, can_edit, can_download, can_share, start_date, end_date, granted_by
- **Contrainte unique** : (document_id, user_id)
- **Methode** : `is_valid()` verifie la validite temporelle

### `notification.py` - Modele Notification
- **Champs** : user_id, type, title, message, priority, is_read, read_at, expires_at, document_id, task_id, extra_data
- **Types** : task_due, task_overdue, task_assigned, document_expiry, document_expired, document_shared, permission_granted, permission_revoked, permission_expiring, welcome, backup_complete, system
- **Methodes** : time_ago (affichage relatif), is_expired, get_unread_count, cleanup_expired

### `log.py` - Modele Log (audit)
- **Champs** : user_id, action, details, ip_address, user_agent, document_id, created_at
- **Actions tracees** : login, logout, login_failed, document_upload, document_view, document_download, document_edit, document_share, etc.
- **Retention RGPD** : 7 jours (dev), configurable pour production

### `tag.py` - Modele Tag + table d'association
- **Champs** : name, color, owner_id
- **Contrainte** : (name, owner_id) unique
- **Association M:N** : `document_tags` (document_id, tag_id)

### `document_version.py` - Modele DocumentVersion
- **Champs** : document_id, version_number, stored_filename, file_size, uploaded_by, comment, created_at
- **Cascade** : supprime quand le document parent est supprime

### `message.py` - Modele Message
- **Champs** : content, sender_id, family_id, is_announcement, is_edited, is_deleted, created_at
- **Methodes** : can_edit(user), can_delete(user) - 15 min pour editer, 1h pour supprimer
- **Cascade** : supprime quand la famille est supprimee

---

## 5. Services (app/services/)

### `auth_service.py` - Service d'authentification
- **hash_password()** : hachage bcrypt
- **check_password()** : verification bcrypt
- **login_user()** : authentification avec rate limiting (5 tentatives, 15 min de blocage)
- **validate_password()** : regles de force (8+ chars, majuscule, minuscule, chiffre, caractere special)
- **create_default_admin()** : cree l'admin par defaut au premier lancement
- **create_default_folders()** : cree les dossiers par defaut pour un nouvel utilisateur

### `document_service.py` - Service documents
- **upload_document()** : validation fichier + sauvegarde + chiffrement AES si confidentiel
- **get_user_documents()** / **get_user_documents_query()** : recuperation avec filtres
- **get_shared_documents()** : documents partages avec l'utilisateur
- **update_document()** : mise a jour metadonnees
- **delete_document()** : suppression fichier + BDD
- **get_expiring_documents()** : documents arrivant a echeance

### `backup_service.py` - Service sauvegarde
- **create_backup()** : archive ZIP (BDD + fichiers uploades + metadonnees)
- **restore_backup()** : restauration depuis ZIP
- **export_user_data()** : export RGPD (JSON avec donnees personnelles, dossiers, documents, taches)
- **list_backups()** / **delete_backup()** / **cleanup_old_backups()** : gestion des archives
- Support PostgreSQL (export JSON) et SQLite (copie fichier)

### `notification_service.py` - Service notifications
- **notify_task_due()** : tache a echeance
- **notify_task_assigned()** : tache assignee
- **notify_document_expiry()** : document expirant
- **notify_document_shared()** : document partage
- **notify_permission_granted()** / **revoked()** / **expiring()** : droits d'acces
- **notify_welcome()** : bienvenue nouvel utilisateur
- **check_and_create_due_notifications()** : verification automatique des echeances
- **get_notification_summary()** : resume pour le dashboard (non-lus, urgents, recents)
- **cleanup()** : nettoyage des notifications expirees/anciennes

### `permission_service.py` - Service permissions
- **grant_permission()** : accorde un acces (view, edit, download, share) avec date de fin
- **grant_multiple_permissions()** : accorde a plusieurs utilisateurs
- **revoke_permission()** : revoque un acces
- **check_permission()** : verifie si un utilisateur a un droit specifique
- **get_document_permissions()** : liste les permissions d'un document
- **share_folder()** : partage un dossier entier
- Logique : proprietaire > admin > permission explicite

### `search_service.py` - Service recherche
- **search_documents()** / **search_documents_query()** : recherche multicritere (nom, type, dossier, dates, confidentialite, tags)
- **search_tasks()** : recherche de taches
- **global_search()** : recherche globale (documents + taches) pour l'AJAX
- **get_statistics()** : statistiques detaillees (par type, par mois, taille totale, taches par statut)

### `scheduler_service.py` - Planificateur
- **start(app)** : demarre un thread daemon avec 3 jobs periodiques
- Job 1 : **check_deadlines** (toutes les heures) - verifie taches et documents a echeance
- Job 2 : **cleanup_notifications** (quotidien a 02h) - supprime notifications expirees
- Job 3 : **cleanup_expired_permissions** (quotidien a 03h) - nettoie permissions expirees
- Ne demarre PAS en mode TESTING

### `encryption_service.py` - Service chiffrement
- **generate_key()** : genere une cle Fernet (AES 128-bit)
- **encrypt_data()** / **decrypt_data()** : chiffrement/dechiffrement en memoire
- **encrypt_string()** / **decrypt_string()** : chiffrement de chaines
- **encrypt_file()** / **decrypt_file()** : chiffrement/dechiffrement de fichiers sur disque
- **decrypt_to_memory()** : dechiffrement d'un fichier directement en memoire
- **derive_key_from_password()** : derivation de cle depuis mot de passe (PBKDF2)

---

## 6. Routes (app/routes/)

### `auth_routes.py` - Blueprint auth (sans prefixe)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/` | index | Redirection login ou dashboard |
| GET, POST | `/login` | login | Page de connexion |
| GET | `/logout` | logout | Deconnexion |
| GET, POST | `/register` | register | Inscription + notification bienvenue |
| GET, POST | `/change-password` | change_password | Changement mot de passe |

### `user_routes.py` - Blueprint user (sans prefixe)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/dashboard` | dashboard | Tableau de bord (stats, recents, familles, notifs) |
| GET, POST | `/profile` | profile | Page de profil |
| GET | `/profile/export-data` | export_data | Export RGPD (JSON telechargeabl) |
| POST | `/profile/avatar` | upload_avatar | Upload avatar |
| POST | `/profile/avatar/delete` | delete_avatar | Suppression avatar |
| GET | `/avatars/<filename>` | avatar | Affichage avatar |
| GET | `/folders` | folders | Liste des dossiers (pagine) |
| GET, POST | `/folders/create` | create_folder | Creation dossier |
| GET | `/folders/<id>` | view_folder | Detail dossier |
| GET, POST | `/folders/<id>/edit` | edit_folder | Edition dossier |
| POST | `/folders/<id>/delete` | delete_folder | Suppression dossier |
| GET | `/activity` | activity | Historique utilisateur |
| GET | `/activity/detailed` | activity_detailed | Historique detaille |
| GET, POST | `/folders/<id>/share` | share_folder | Partage dossier |

### `document_routes.py` - Blueprint document (prefixe `/documents`)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/documents/` | list_documents | Liste paginee + tri + recherche |
| GET | `/documents/shared` | shared_documents | Documents partages avec moi |
| GET | `/documents/my-shares` | my_shared_documents | Mes partages sortants |
| GET, POST | `/documents/upload` | upload | Upload + chiffrement auto si prive |
| GET | `/documents/<id>` | view | Detail document + logs |
| GET | `/documents/<id>/download` | download | Telechargement (+ dechiffrement) |
| GET, POST | `/documents/<id>/edit` | edit | Edition metadonnees |
| POST | `/documents/<id>/delete` | delete | Suppression |
| GET, POST | `/documents/<id>/share` | share | Partage avec permissions granulaires |
| POST | `/documents/<id>/revoke-all` | revoke_all_access | Revoquer tous les acces |
| POST | `/documents/<id>/revoke/<uid>` | revoke_access | Revoquer un acces specifique |
| GET | `/documents/<id>/mark-reviewed` | mark_reviewed | Marquer comme revise |
| POST | `/documents/bulk-action` | bulk_action | Operations en masse |

### `task_routes.py` - Blueprint task (prefixe `/tasks`)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/tasks/` | list_tasks | Liste paginee + filtres statut/priorite |
| GET | `/tasks/calendar` | calendar | Vue calendrier |
| GET, POST | `/tasks/create` | create | Creation tache |
| GET | `/tasks/<id>` | view | Detail tache |
| GET, POST | `/tasks/<id>/edit` | edit | Edition tache |
| POST | `/tasks/<id>/status/<status>` | change_status | Changement statut |
| POST | `/tasks/<id>/delete` | delete | Suppression (modal confirmation) |
| GET | `/tasks/overdue` | overdue | Taches en retard |
| GET | `/tasks/upcoming` | upcoming | Taches a venir |

### `family_routes.py` - Blueprint family (sans prefixe)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/families` | list_families | Liste des familles |
| GET, POST | `/families/create` | create_family | Creation famille |
| GET | `/families/<id>` | view_family | Detail famille |
| POST | `/families/<id>/invite` | create_invite_link | Creer lien d'invitation |
| POST | `/families/<id>/members/<mid>/role` | change_member_role | Changer role membre |
| POST | `/families/<id>/members/<mid>/remove` | remove_member | Exclure un membre |
| POST | `/families/<id>/leave` | leave_family | Quitter la famille |
| POST | `/families/<id>/delete` | delete_family | Supprimer (createur seul) |
| GET | `/join/<token>` | join_family | Rejoindre via lien (public) |
| GET | `/invite/<token>` | accept_invite | Accepter invitation |
| GET | `/share/<token>` | accept_share_link | Accepter lien de partage |
| POST | `/documents/<id>/share-link` | create_share_link | Creer lien de partage doc |
| POST | `/share-links/<id>/revoke` | revoke_share_link | Revoquer un lien |

### `admin_routes.py` - Blueprint admin (prefixe `/admin`)
Toutes les routes sont protegees par `@admin_required`.

| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/admin/` | dashboard | Tableau de bord admin |
| GET | `/admin/users` | users | Liste utilisateurs |
| GET, POST | `/admin/users/create` | create_user | Creation utilisateur |
| GET | `/admin/users/<id>` | view_user | Detail utilisateur |
| GET, POST | `/admin/users/<id>/edit` | edit_user | Edition utilisateur |
| POST | `/admin/users/<id>/reset-password` | reset_user_password | Reset mot de passe |
| POST | `/admin/users/<id>/toggle-active` | toggle_user_active | Activer/desactiver |
| GET | `/admin/logs` | logs | Journaux systeme |
| GET | `/admin/backups` | backups | Page sauvegardes |
| POST | `/admin/backups/create` | create_backup | Creer sauvegarde |
| POST | `/admin/backups/restore` | restore_backup | Restaurer sauvegarde |
| POST | `/admin/backups/delete` | delete_backup | Supprimer sauvegarde |

### `notification_routes.py` - Blueprint notification (prefixe `/notifications`)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/notifications/` | list_notifications | Liste des notifications |
| GET | `/notifications/count` | get_count | API compteur (AJAX) |
| GET | `/notifications/summary` | get_summary | API resume |
| GET | `/notifications/recent` | get_recent | API recentes |
| POST | `/notifications/<id>/read` | mark_as_read | Marquer comme lue |
| POST | `/notifications/<id>/unread` | mark_as_unread | Marquer non lue |
| POST | `/notifications/read-all` | mark_all_as_read | Tout marquer comme lu |
| POST | `/notifications/<id>/delete` | delete_notification | Supprimer |
| POST | `/notifications/delete-read` | delete_read_notifications | Supprimer les lues |
| POST | `/notifications/check-due` | check_due_notifications | Verifier echeances (admin) |
| POST | `/notifications/cleanup` | cleanup_notifications | Nettoyage (admin) |

### `search_routes.py` - Blueprint search (sans prefixe)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/search` | advanced_search | Recherche multicritere (paginee) |
| GET | `/search/global` | global_search | API recherche rapide (AJAX) |
| GET | `/tags` | list_tags | Liste des tags (paginee) |
| POST | `/tags/create` | create_tag | Creation tag |
| POST | `/tags/<id>/delete` | delete_tag | Suppression tag |
| POST | `/documents/<id>/tags` | add_tag_to_document | Ajouter tag a document |
| POST | `/documents/<id>/tags/<tid>/remove` | remove_tag_from_document | Retirer tag |

### `version_routes.py` - Blueprint version (prefixe `/documents`)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/documents/<id>/versions` | list_versions | Historique versions |
| POST | `/documents/<id>/versions/upload` | upload_version | Ajouter version |
| GET | `/documents/<id>/versions/<vid>/download` | download_version | Telecharger version |
| POST | `/documents/<id>/versions/<vid>/restore` | restore_version | Restaurer version |

### `message_routes.py` - Blueprint message (sans prefixe)
| Methode | URL | Fonction | Description |
|---|---|---|---|
| GET | `/families/<id>/chat` | chat | Page de chat familial |
| POST | `/families/<id>/chat/send` | send_message | Envoyer message |
| POST | `/messages/<id>/edit` | edit_message | Editer (15 min max) |
| POST | `/messages/<id>/delete` | delete_message | Supprimer (1h max) |
| GET | `/families/<id>/chat/load-more` | load_more_messages | Charger anciens messages |

---

## 7. Templates (app/templates/)

### Layout principal
- **`base.html`** : Layout maitre. Contient : sidebar avec navigation, recherche rapide AJAX, compteur notifications, toggle mode sombre, CSRF auto-inject, validation Bootstrap, favicon

### Macros reutilisables (`macros/`)
- **`pagination.html`** : Macro `render_pagination()` - pagination Bootstrap avec numeros de pages, fleches, compteur total
- **`breadcrumbs.html`** : Macro `render_breadcrumbs()` - fil d'Ariane avec icone accueil

### Pages d'authentification
- **`login.html`** : Formulaire de connexion
- **`register.html`** : Formulaire d'inscription avec validation inline Bootstrap (pattern, minlength, invalid-feedback)
- **`change_password.html`** : Changement de mot de passe

### Dashboard et profil
- **`dashboard.html`** : Tableau de bord avec : stats rapides (4 cards), documents recents, taches a venir, widget familles, widget notifications, statistiques detaillees (accordion), activite 6 mois, documents expirants
- **`profile.html`** : Profil utilisateur + bouton export RGPD + avatar

### Documents
- **`documents.html`** : Liste paginee + tri colonnes + operations en masse (checkboxes) + breadcrumbs
- **`view_document.html`** : Detail avec breadcrumbs, historique pliable, versions, tags, permissions, tooltips
- **`edit_document.html`** : Edition metadonnees avec preservation formulaire sur erreur
- **`upload_document.html`** : Upload avec barre de progression AJAX
- **`share_document.html`** : Partage avec selection permissions granulaires
- **`document_versions.html`** : Historique complet des versions
- **`shared_documents.html`** : Documents partages avec moi
- **`my_shared_documents.html`** : Mes partages sortants

### Dossiers
- **`folders.html`** : Liste paginee + breadcrumbs
- **`view_folder.html`** : Detail dossier + documents contenus
- **`create_folder.html`** / **`edit_folder.html`** : CRUD dossiers
- **`share_folder.html`** : Partage de dossier

### Taches
- **`tasks.html`** : Liste paginee + filtres statut/priorite + breadcrumbs
- **`view_task.html`** : Detail avec modal de suppression + tooltips
- **`create_task.html`** / **`edit_task.html`** : CRUD taches
- **`calendar.html`** : Vue calendrier mensuel
- **`overdue_tasks.html`** / **`upcoming_tasks.html`** : Vues filtrees

### Familles
- **`families.html`** : Liste des familles + breadcrumbs
- **`view_family.html`** : Detail avec membres, roles, liens d'invitation
- **`create_family.html`** : Creation famille
- **`join_family.html`** : Rejoindre via lien
- **`chat.html`** : Chat familial en temps reel

### Recherche et tags
- **`search.html`** : Recherche avancee multicritere + pagination
- **`tags.html`** : Gestion des tags + pagination

### Notifications
- **`notifications.html`** : Centre de notifications (toutes, non lues, prioritaires)

### Historique
- **`activity.html`** / **`activity_detailed.html`** : Journal d'activite

### Administration (`admin/`)
- **`admin/dashboard.html`** : Vue d'ensemble admin
- **`admin/users.html`** / **`admin/view_user.html`** : Liste et detail utilisateurs
- **`admin/create_user.html`** / **`admin/edit_user.html`** : CRUD utilisateurs
- **`admin/logs.html`** : Journaux systeme
- **`admin/backups.html`** : Gestion sauvegardes

### Erreurs (`errors/`)
- **`errors/403.html`** : Acces interdit
- **`errors/404.html`** : Page non trouvee
- **`errors/500.html`** : Erreur serveur

---

## 8. Fichiers statiques (app/static/)

### `css/style.css`
- Design moderne avec sidebar fixe et variables CSS
- Classes utilitaires : stat-card, sidebar-*, auth-layout
- `@media print` : masque sidebar, boutons, formulaires pour impression
- `@media (max-width: 768px)` : tables responsives (cards sur mobile)
- `[data-theme="dark"]` : mode sombre complet (fond, cartes, tableaux, formulaires, dropdowns)

### `js/app.js`
- **initTooltips()** : Initialise les tooltips Bootstrap sur `[data-bs-toggle="tooltip"]`
- **toggleBulkSelect() / selectAllDocs() / submitBulk()** : Operations en masse (checkboxes documents)
- **initUploadProgress()** : Barre de progression upload via XMLHttpRequest
- **initSessionWarning()** : Alerte 5 minutes avant expiration session (2h)
- **initKeyboardShortcuts()** : `Ctrl+K` = recherche rapide, `Escape` = fermer modals

### `img/favicon.svg`
- Icone SVG "FD" sur fond bleu (#0d6efd) avec coins arrondis

---

## 9. Tests (tests/)

### `conftest.py` - Fixtures partagees
- **app** : Application Flask en mode testing (BDD en memoire)
- **client** : Client HTTP de test
- **test_user** : Utilisateur standard (test@familidocs.local / Test123!)
- **admin_user** : Administrateur (admin_test@familidocs.local / Admin123!)
- **second_user** : Deuxieme utilisateur pour tests de partage
- **test_folder** : Dossier de test
- **test_document** : Document de test
- **test_task** : Tache de test
- **test_family** : Famille de test avec le createur comme chef_famille
- **auth_client** : Client authentifie (utilisateur standard)
- **admin_client** : Client authentifie (admin)

### Fichiers de tests (15 fichiers, 302 tests)

| Fichier | Tests | Description |
|---|---|---|
| **test_models.py** | ~80 | Tests unitaires de tous les modeles (creation, proprietes, methodes, contraintes) |
| **test_routes.py** | ~40 | Tests des routes HTTP (status codes, redirections, acces) |
| **test_services.py** | ~50 | Tests des services (auth, document, notification, backup, permission, search) |
| **test_integration.py** | ~30 | Tests d'integration (workflows complets : upload + share + download) |
| **test_security.py** | ~25 | Tests de securite (CSRF, rate limiting, acces non autorise, injection) |
| **test_documents.py** | ~20 | Tests CRUD documents detailles |
| **test_versions.py** | ~10 | Tests versionnement documents |
| **test_tags.py** | ~10 | Tests tags et association documents-tags |
| **test_families.py** | ~8 | Tests familles (creation, membres, roles, invitation, exclusion) |
| **test_chat.py** | ~6 | Tests chat (envoi, edition, suppression messages, annonces) |
| **test_share_links.py** | ~7 | Tests liens de partage (creation, expiration, limites d'utilisation) |
| **test_admin.py** | ~5 | Tests admin (dashboard, CRUD users, logs, backup) |
| **test_encryption.py** | ~7 | Tests chiffrement (round-trip, fichiers, mauvaise cle, derivation) |
| **test_rgpd.py** | ~10 | Tests export RGPD (completude, champs, route JSON) |

---

## 10. Fichiers racine

### `desktop_app.py`
Lanceur desktop avec CustomTkinter. Cree une fenetre native avec un webview integre vers le serveur Flask local. Gere le chemin BDD selon le mode (dev vs .exe compile).

### `desktop_launcher.py`
Lanceur desktop alternatif qui ouvre le navigateur par defaut. Demarre Flask sur un port disponible et ouvre `http://localhost:PORT`. Meme logique de chemin BDD.

### `build_exe.bat`
Script batch Windows pour creer l'executable via PyInstaller. Installe les dependances manquantes, nettoie les anciennes builds, compile avec tous les hidden imports necessaires.

### `familidocs.spec`
Configuration PyInstaller. Liste les hidden imports (tous les modeles + services + cryptography.fernet), les donnees bundlees (templates + static), les options de compilation.

### `requirements.txt`
36 dependances Python :
- Flask + extensions (SQLAlchemy, Login, WTF, Migrate)
- Securite (bcrypt, cryptography)
- BDD (psycopg2-binary pour PostgreSQL)
- Tests (pytest, pytest-flask)
- Desktop (customtkinter, pillow, pyinstaller)
- Utilitaires (schedule, python-dotenv, python-dateutil, email-validator)

### `.env.example`
Template de configuration avec : FLASK_ENV, SECRET_KEY, DATABASE_URL, ENCRYPTION_KEY, LOG_LEVEL

### `.gitignore`
Exclut : venv/, __pycache__/, *.db, .env, dist/, build/, .idea/, .pytest_cache/

---

## 11. Securite et autorisation

### Authentification
- **Hachage bcrypt** pour les mots de passe
- **Rate limiting** : 5 tentatives echouees = 15 min de blocage
- **Force mot de passe** : 8+ chars, majuscule, minuscule, chiffre, caractere special
- **Session** : 2h timeout, cookies HttpOnly + SameSite=Lax + Secure (prod)
- **CSRF** : Flask-WTF CSRFProtect actif globalement

### Autorisation multi-niveaux
1. **`@login_required`** : sur toutes les routes protegees
2. **`@admin_required`** : sur toutes les routes `/admin/`
3. **Verification proprietaire** : document.owner_id == current_user.id
4. **Verification permission** : PermissionService.check_permission()
5. **Verification role famille** : FamilyMember.role pour les operations famille

### Headers HTTP de securite
```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-cache, no-store, must-revalidate
```

### Chiffrement
- Documents prives chiffres automatiquement a l'upload (AES via Fernet)
- Dechiffrement transparent au telechargement
- Cle de chiffrement dans la configuration (variable d'environnement en production)

### Audit
- Toutes les actions sensibles sont tracees dans les logs
- Chaque log contient : user_id, action, details, IP, user_agent, timestamp
- Retention RGPD configurable

---

## 12. Recapitulatif des modifications

### Phase 0 : Fix partage BDD web/exe
- `desktop_launcher.py` : ajout condition `getattr(sys, 'frozen', False)` pour ne forcer le chemin `~/.familidocs/` qu'en mode .exe
- `desktop_app.py` : meme modification

### Phase 1 : Notifications manquantes (T9, T10, T13)
- `app/routes/document_routes.py` : notification apres partage de document
- `app/services/notification_service.py` : ajout methode `notify_task_assigned()`
- `app/models/notification.py` : ajout type `task_assigned` + icone
- `app/routes/task_routes.py` : appel notification a l'assignation
- `app/routes/auth_routes.py` : appel `notify_welcome()` apres inscription

### Phase 2 : RGPD + Chiffrement (T7, T8)
- `app/routes/user_routes.py` : route `/profile/export-data` (export JSON RGPD)
- `app/templates/profile.html` : bouton "Exporter mes donnees"
- `app/services/document_service.py` : chiffrement automatique a l'upload si confidentiel
- `app/routes/document_routes.py` : dechiffrement au download si chiffre
- `app/templates/view_document.html` : icone cadenas si document chiffre

### Phase 3 : Pagination (T2-T6)
- `app/templates/macros/pagination.html` : macro reutilisable
- `app/routes/document_routes.py` : pagination + tri colonnes
- `app/routes/task_routes.py` : pagination
- `app/routes/search_routes.py` : pagination recherche + tags
- `app/routes/user_routes.py` : pagination dossiers
- `app/services/document_service.py` : ajout `get_user_documents_query()`
- `app/services/search_service.py` : ajout `search_documents_query()`
- Templates `documents.html`, `tasks.html`, `search.html`, `tags.html`, `folders.html` : appel macro pagination

### Phase 4 : Scheduler (T1)
- `app/services/scheduler_service.py` : nouveau service (thread daemon, 3 jobs periodiques)
- `app/__init__.py` : demarrage du scheduler (sauf en TESTING)

### Phase 5 : UX Batch 1 (T11-T15)
- Routes taches/documents : preservation formulaire sur erreur (render_template au lieu de redirect)
- `app/templates/register.html` : validation inline Bootstrap (needs-validation, invalid-feedback)
- `app/templates/base.html` : script validation Bootstrap + recherche rapide AJAX
- `app/templates/view_task.html` : modal confirmation suppression
- `app/static/js/app.js` : recherche AJAX avec debounce 300ms

### Phase 6 : UX Batch 2 (T16-T20)
- `app/routes/document_routes.py` : tri colonnes (sort, order)
- `app/templates/documents.html` : headers cliquables + checkboxes + barre actions masse
- `app/routes/document_routes.py` : route `bulk_action()` pour suppression masse
- `app/static/js/app.js` : fonctions bulk select, upload progress bar, session warning, raccourcis clavier
- `app/static/css/style.css` : CSS impression + responsive tables + mode sombre

### Phase 7 : Tests (T21-T26)
- `tests/test_families.py` : 8 tests familles
- `tests/test_chat.py` : 6 tests chat
- `tests/test_share_links.py` : 7 tests liens de partage
- `tests/test_admin.py` : 5 tests admin
- `tests/test_encryption.py` : 7 tests chiffrement
- `tests/test_rgpd.py` : 10 tests RGPD

### Phase 8 : Polish Batch 1 (T27-T31)
- `app/templates/view_document.html` + `view_task.html` : tooltips sur boutons d'action
- `app/templates/dashboard.html` : widget familles + widget notifications
- `app/routes/user_routes.py` : passage donnees familles et notifications au dashboard
- `app/templates/macros/breadcrumbs.html` : macro breadcrumbs
- Templates `documents.html`, `folders.html`, `tasks.html`, `families.html` : ajout breadcrumbs

### Phase 9 : Polish Batch 2 (T32-T34)
- `app/templates/base.html` : bouton toggle mode sombre + JS localStorage
- `app/static/img/favicon.svg` : nouveau favicon SVG
- `app/templates/base.html` : balise `<link rel="icon">`

### Phase 10 : Executable (E1, E2)
- `familidocs.spec` : ajout hidden imports services + cryptography.fernet
- `build_exe.bat` : ajout hidden imports services + cryptography.fernet

---

## 13. Comment verifier que tout fonctionne

### 1. Tests automatises
```bash
# Depuis la racine du projet, avec le venv active
venv/Scripts/python.exe -m pytest tests/ -v
# Resultat attendu : 302 passed, 0 failed
```

### 2. Lancer l'application web
```bash
venv/Scripts/python.exe app/main.py
# Ouvrir http://localhost:5000
# Login admin : admin@familidocs.local / Admin123!
```

### 3. Verifier le partage BDD web/exe
```bash
# Lancer la version web
venv/Scripts/python.exe app/main.py
# Dans un autre terminal, lancer le desktop launcher
venv/Scripts/python.exe desktop_launcher.py
# Les deux doivent afficher les memes donnees (meme BDD en dev)
```

### 4. Verification manuelle par fonctionnalite

| Fonctionnalite | Comment verifier |
|---|---|
| Inscription | Creer un compte > verifier notification de bienvenue |
| Connexion | Se connecter > verifier redirection dashboard |
| Dashboard | Verifier : stats, documents recents, taches, widget familles, widget notifications |
| Mode sombre | Cliquer l'icone lune dans la sidebar > verifier persistence au rechargement |
| Documents | Upload > verifier dans la liste > trier par colonne > pagination |
| Chiffrement | Upload un document "prive" > verifier icone cadenas > telecharger |
| Recherche | Taper dans la barre laterale > verifier dropdown AJAX |
| Recherche avancee | `/search` > filtrer par type, dossier, dates > verifier pagination |
| Taches | Creer > voir > changer statut > supprimer (modal) |
| Familles | Creer > inviter (lien) > rejoindre > chat |
| Partage | Document > Partager > selectionner droits > verifier notification destinataire |
| Operations masse | Documents > cocher > supprimer en masse |
| Tags | Creer tag > associer a document > rechercher par tag |
| Admin | `/admin/` > CRUD utilisateurs > logs > sauvegardes |
| Export RGPD | Profil > "Exporter mes donnees" > verifier JSON complet |
| Breadcrumbs | Naviguer Documents > Detail > verifier fil d'Ariane |
| Impression | `Ctrl+P` sur une page > verifier que sidebar/boutons sont masques |
| Raccourcis | `Ctrl+K` > verifier focus recherche > `Escape` > fermer |
| Tooltips | Survoler boutons Modifier/Telecharger > verifier info-bulle |

### 5. Construire l'executable
```bash
# Sur Windows
build_exe.bat
# Verifier que dist/FamiliDocs.exe existe
# Lancer sur une machine sans Python pour valider
```
