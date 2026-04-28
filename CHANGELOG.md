# Changelog FamiliDocs

Ce document liste les evolutions majeures du projet, version par version.

Format inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

---

## [2.3] - 2026-03

### Securite
- Authentification a deux facteurs (2FA / TOTP) via `pyotp` + QR code
- Validation de force du mot de passe avec indicateur visuel temps reel cote client
- En-tetes de securite HTTP : Content-Security-Policy, Strict-Transport-Security
- Protection path traversal sur le telechargement (resolution `os.path.realpath`)
- Validation MIME a l'upload des nouvelles versions de documents
- SECRET_KEY et DATABASE_URL obligatoires en production (`raise ValueError` sinon)
- Retention RGPD des logs : 180 jours par defaut, configurable via `LOG_RETENTION_DAYS`

### Donnees de demonstration
- Script `seed_demo_data.py` : famille Dupont realiste (5 utilisateurs, 20 documents, 19 partages, 9 taches, 14 messages, 10 notifications)
- Fichier `DEMO_IDENTIFIANTS.txt` avec tous les comptes
- Suppression du compte `admin@familidocs.local` au profit du modele "parents = administrateurs"
- Renommage du role `chef_famille` en `responsable` (cohérence vocabulaire)

### Application desktop
- Refonte complete de l'interface (CustomTkinter) avec design "Liquid Glass"
- Chat familial integre dans l'application desktop
- Partages avec droits granulaires, duree, revocation
- Dossiers en grille
- Assignation de taches entre membres avec dashboard taches famille (statistiques, progression, recommandations)
- Gestion des utilisateurs avec changement de roles (responsables uniquement)
- Correction des couleurs hex 8 caracteres
- Correction du champ `username` manquant a l'inscription desktop

### Interface web
- Effets Liquid Glass sur cartes, sidebar, pages d'authentification, mode sombre
- Cartes statistiques du dashboard cliquables vers les sections concernees
- Chat accessible depuis la sidebar et la page famille

### Documentation
- `ORAL_E5_PREPARATION.md` : pitch + 25 questions/reponses pour l'oral E5
- Mise a jour de tous les fichiers `.md`
- Humanisation des commentaires de code (style etudiant)
- Nettoyage des fichiers obsoletes (anciens briefings iOS, instructions API Windows)

---

## [2.2] - 2026-02

### Documentation BTS
- `docs/cahier_des_charges.md` : besoins fonctionnels et non-fonctionnels
- `docs/schema_bdd.md` : MCD, tables, relations, index
- `docs/tableau_E5.md` : tableau de synthese des competences couvertes
- `docs/DOCUMENTATION_COMPLETE.md` : architecture detaillee

### Application desktop
- Premiere version CustomTkinter operationnelle
- Compilation .exe avec PyInstaller (`build_exe.bat`, `familidocs.spec`)
- Partage de la meme base PostgreSQL avec la version web

---

## [2.1] - 2026-01

### Familles et collaboration
- Modeles `Family`, `FamilyMember`, `Message` (chat)
- 8 roles familiaux hierarchiques (responsable, admin, parent, gestionnaire, enfant, editeur, lecteur, invite)
- Maximum 2 responsables par famille
- Invitations intelligentes via lien (sans connexion prealable)
- Liens de partage securises avec token, expiration et nombre d'utilisations
- Chat familial avec systeme d'annonces (reservees aux roles privilegies)

### Robustesse et logs
- Pages d'erreur personnalisees 403, 404, 500
- Logging applicatif structure
- Cle secrete auto-generee et persistante (`app/database/.secret_key`)

### Tests
- 6 nouveaux fichiers de tests : familles, chat, liens de partage, admin, chiffrement, RGPD

---

## [2.0] - 2025-12

### Fonctionnalites majeures
- Versionnement complet des documents (modele `DocumentVersion` + routes dediees)
- Tags personnalises avec couleur, en relation N:N avec les documents (`document_tags`)
- Recherche multi-criteres avancee + recherche globale AJAX dans la sidebar
- Notifications temps reel : 12 types, badge AJAX, rafraichissement auto 60s
- Dashboard ameliore : graphiques d'activite mensuelle, indicateurs cles, alertes
- Operations en masse sur les documents (selection multiple + suppression)

### Securite
- Rate limiting des tentatives de connexion (5 tentatives, 15 min de blocage)
- Politique de mot de passe stricte (8+ caracteres, majuscule, minuscule, chiffre, caractere special)
- Sessions securisees : HttpOnly, SameSite=Lax, Secure en production
- Chiffrement AES (Fernet) automatique des documents marques "private"

### Interface
- Mode sombre persistant (localStorage)
- Tables responsive (cartes sur mobile)
- CSS d'impression masquant sidebar et boutons
- Raccourcis clavier (Ctrl+K = recherche rapide)
- Tooltips sur les boutons d'action

### Architecture
- 8 services metier (auth, document, permission, notification, search, scheduler, backup, encryption)
- 10 blueprints Flask
- Service `SchedulerService` (thread daemon : verification echeances, nettoyage logs et notifications)

---

## [1.0] - 2025-09

### Premiere version
- Architecture MVC (Flask + SQLAlchemy + Bootstrap)
- 13 modeles : User, Document, Folder, Permission, Task, Log, Notification, DocumentVersion, Tag, Family, FamilyMember, ShareLink, Message
- Authentification (bcrypt) + roles applicatifs (admin, user, trusted)
- Upload de documents multiformat avec organisation en dossiers
- Partage avec permissions granulaires (lecture, edition, telechargement, partage)
- Taches et echeances avec 4 priorites et 4 statuts
- Administration : gestion utilisateurs, logs, sauvegardes (ZIP)
- Conformite RGPD : export des donnees personnelles, suppression de compte
- Suite de tests pytest (modeles, services, routes, integration, securite)
