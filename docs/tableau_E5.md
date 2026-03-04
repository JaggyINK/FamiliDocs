# Tableau de Synthese - Epreuve E5 BTS SIO SLAM

## Informations Projet

| Element | Description |
|---------|-------------|
| **Nom du projet** | FamiliDocs |
| **Type** | Application Web |
| **Langage principal** | Python (Flask) |
| **Base de donnees** | PostgreSQL (dev/prod), SQLite (tests/desktop) |
| **Contexte** | Gestion documentaire familiale |
| **Version** | 2.1 |

## Competences Couvertes

### Bloc 1 - Support et mise a disposition de services informatiques

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Gerer le patrimoine informatique | Documentation technique et utilisateur | Schema BDD, documentation technique, tableau E5, `.env.example` |
| Repondre aux incidents | Journalisation des erreurs | Module de logs (21 actions), pages erreur 403/404/500, logging Python |
| Developper la presence en ligne | Interface web responsive | Templates Bootstrap 5.3, design adaptatif |
| Travailler en mode projet | Organisation du code | Structure MVC, Git, 257 tests, suivi ameliorations |

### Bloc 2 - Conception et developpement d'applications

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Concevoir une solution applicative | Architecture logicielle | Pattern MVC, 7 services, 13 modeles, 10 blueprints |
| Developper une solution applicative | Code Python/Flask | Routes, services, modeles SQLAlchemy, chat familial |
| Gerer les donnees | Base de donnees relationnelle | Schema 15 tables, ORM SQLAlchemy, relations 1:N/N:N |
| Proteger les donnees | Securite applicative | Hashage bcrypt, chiffrement AES, CSRF, sessions securisees |

### Bloc 3 - Cybersecurite des services informatiques

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Proteger les donnees a caractere personnel | Conformite RGPD | Export donnees, suppression compte, chiffrement |
| Securiser les equipements et usages | Authentification | bcrypt, rate limiting, sessions securisees, headers HTTP |
| Preserver l'identite numerique | Gestion des acces | 3 roles app + 8 roles famille, permissions granulaires |

## Fonctionnalites Implementees

### Gestion des utilisateurs
- [x] Inscription avec validation stricte
- [x] Connexion securisee (bcrypt + rate limiting)
- [x] Gestion des roles (admin/user/trusted)
- [x] Profil utilisateur modifiable
- [x] Photo de profil (upload/suppression)
- [x] Titre familial personnalise (Papa, Maman, etc.)
- [x] Changement de mot de passe

### Gestion documentaire
- [x] Upload de fichiers multiformats (PDF, images, Word, Excel, texte)
- [x] Organisation en dossiers hierarchiques (5 dossiers par defaut)
- [x] Metadonnees (nom, description, type, confidentialite)
- [x] Date de revision obligatoire avec alertes
- [x] Recherche et filtrage
- [x] Telechargement securise
- [x] Validation des extensions et niveaux de confidentialite

### Partage et permissions
- [x] Partage avec utilisateurs specifiques
- [x] Droits granulaires (lecture/ecriture/telechargement/partage)
- [x] Acces temporaire avec expiration (max 90 jours)
- [x] Partage multiple (plusieurs utilisateurs a la fois)
- [x] Partage de dossiers complets
- [x] Revocation des droits
- [x] Liens de partage securises (token, expiration, usage limite)

### Taches et echeances
- [x] Creation de taches liees aux documents
- [x] Gestion des priorites (4 niveaux)
- [x] Suivi des statuts (4 statuts)
- [x] Assignation a des membres de la famille
- [x] Rappels d'echeances parametrables
- [x] Vue calendrier
- [x] Validation des entrees serveur

### Gestion familiale (v2.1)
- [x] Creation de groupes familiaux
- [x] 8 roles hierarchiques (chef_famille -> invite)
- [x] Limite 2 chefs de famille par foyer
- [x] Invitations intelligentes (lien sans connexion)
- [x] Rejoindre famille a l'inscription
- [x] Revocation automatique a la sortie
- [x] Gestion des roles et promotions

### Chat familial (v2.1)
- [x] Messagerie au sein de la famille
- [x] Annonces reservees aux roles privilegies
- [x] Edition et suppression (soft delete)
- [x] Notifications pour les annonces

### Notifications (v2.0)
- [x] Notifications temps reel (AJAX)
- [x] 11 types de notifications
- [x] Priorites avec code couleur
- [x] Rafraichissement automatique (60s)
- [x] Support email (simule en dev, logging en prod)

### Versioning documents (v2.0)
- [x] Historique complet des versions
- [x] Upload de nouvelles versions
- [x] Restauration d'anciennes versions
- [x] Telechargement par version
- [x] Accordeon pliable dans l'interface

### Tags et recherche avancee (v2.0)
- [x] Tags personnalises avec couleur
- [x] Association N:N documents-tags
- [x] Recherche multi-criteres
- [x] Recherche globale AJAX

### Dashboard ameliore (v2.0)
- [x] Statistiques par type de fichier
- [x] Indicateurs cles (espace, retards)
- [x] Graphique d'activite mensuel (cliquable)
- [x] Alertes visuelles
- [x] Activite detaillee avec filtres

### Administration
- [x] Tableau de bord statistiques
- [x] Gestion des utilisateurs
- [x] Consultation des logs
- [x] Sauvegardes et restauration

### Securite
- [x] Hashage bcrypt des mots de passe
- [x] Protection CSRF
- [x] Sessions securisees (HttpOnly, SameSite)
- [x] Validation des entrees (serveur)
- [x] Journalisation des actions (21 types)
- [x] Limitation de tentatives de connexion (v2.0)
- [x] En-tetes HTTP de securite (5 headers) (v2.0)
- [x] Politique de mot de passe stricte (v2.0)
- [x] Pages d'erreur personnalisees (403/404/500) (v2.1)
- [x] Logging applicatif structure (v2.1)
- [x] Cle secrete auto-generee (v2.1)

### Tests (v2.1)
- [x] 302 tests automatises
- [x] Tests modeles (102 tests)
- [x] Tests services (28 tests)
- [x] Tests routes (30 tests)
- [x] Tests integration (17 tests)
- [x] Tests securite (14 tests)
- [x] Tests versioning et tags (11 tests)
- [x] Tests RGPD, chat, familles, partage, admin, chiffrement

## Technologies Utilisees

| Categorie | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.x |
| Framework web | Flask | 3.0 |
| ORM | SQLAlchemy | 2.0 |
| Authentification | Flask-Login | 0.6 |
| Hashage | bcrypt | 4.1 |
| Chiffrement | cryptography | 41.0 |
| Frontend | Bootstrap | 5.3 |
| Base de donnees | PostgreSQL (dev/prod) | 16+ |
| Base de donnees (tests) | SQLite en memoire | 3 |
| Tests | pytest | 7.4 |

## Livrables

| Livrable | Format | Description |
|----------|--------|-------------|
| Code source | Python | Application complete (13 modeles, 7 services, 10 blueprints) |
| Base de donnees | SQLite | Schema 15 tables avec relations |
| Schema BDD | Markdown | MCD et description detaillee des tables |
| Documentation technique | Markdown | Architecture, API, securite, deploiement |
| Tableau E5 | Markdown | Ce document |
| Tests | Python | 302 tests automatises (11 fichiers) |
| Suivi ameliorations | Markdown | Historique detaille des phases |
| `.env.example` | Dotenv | Configuration des variables d'environnement |

## Points Forts du Projet

1. **Architecture solide** : 13 modeles, 7 services, 10 blueprints (MVC strict)
2. **Securite multi-couches** : bcrypt, CSRF, rate limiting, headers HTTP, validation serveur
3. **Gestion familiale complete** : 8 roles, invitations smart, chat, assignation taches
4. **Versioning documents** : Tracabilite complete des modifications
5. **Tags et recherche avancee** : Organisation flexible multi-criteres
6. **Notifications temps reel** : AJAX, 11 types, rafraichissement auto
7. **Dashboard statistiques** : Graphiques, indicateurs, alertes
8. **302 tests automatises** : Modeles, services, routes, integration, securite, RGPD
9. **Documentation technique** : Complete et detaillee (3 documents)
10. **Pages d'erreur personnalisees** et logging structure

## Axes d'Amelioration

1. Application mobile native
2. Integration cloud (AWS/GCP)
3. Signature electronique
4. Reconnaissance optique de caracteres (OCR)
5. Notifications par email reel (SMTP)

## Contexte BTS SIO SLAM

Ce projet repond aux exigences de l'epreuve E5 :
- Developpement d'une solution applicative complete
- Utilisation de technologies actuelles
- Respect des bonnes pratiques de developpement
- Documentation technique exhaustive
- Tests et validation (302 tests automatises)
- Securite applicative multi-couches
