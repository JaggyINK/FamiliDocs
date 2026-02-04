# Tableau de Synthese - Epreuve E5 BTS SIO SLAM

## Informations Projet

| Element | Description |
|---------|-------------|
| **Nom du projet** | FamiliDocs |
| **Type** | Application Web |
| **Langage principal** | Python (Flask) |
| **Base de donnees** | SQLite |
| **Contexte** | Gestion documentaire familiale |

## Competences Couvertes

### Bloc 1 - Support et mise a disposition de services informatiques

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Gerer le patrimoine informatique | Documentation technique et utilisateur | Cahier des charges, README, documentation BDD |
| Repondre aux incidents | Journalisation des erreurs | Module de logs, gestion des exceptions |
| Developper la presence en ligne | Interface web responsive | Templates Bootstrap, design adaptatif |
| Travailler en mode projet | Organisation du code | Structure MVC, Git, tests unitaires |

### Bloc 2 - Conception et developpement d'applications

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Concevoir une solution applicative | Architecture logicielle | Pattern MVC, services, modeles |
| Developper une solution applicative | Code Python/Flask | Routes, services, modeles SQLAlchemy |
| Gerer les donnees | Base de donnees relationnelle | Schema BDD, ORM SQLAlchemy |
| Proteger les donnees | Securite applicative | Hashage, chiffrement, CSRF, sessions |

### Bloc 3 - Cybersecurite des services informatiques

| Competence | Description | Realisation |
|------------|-------------|-------------|
| Proteger les donnees a caractere personnel | Conformite RGPD | Export donnees, suppression compte |
| Securiser les equipements et usages | Authentification | bcrypt, sessions securisees |
| Preserver l'identite numerique | Gestion des acces | Roles, permissions granulaires |

## Fonctionnalites Implementees

### Gestion des utilisateurs
- [x] Inscription avec validation
- [x] Connexion securisee
- [x] Gestion des roles (admin/user/trusted)
- [x] Profil utilisateur modifiable
- [x] Changement de mot de passe

### Gestion documentaire
- [x] Upload de fichiers multiformats
- [x] Organisation en dossiers
- [x] Metadonnees (nom, description, type)
- [x] Recherche et filtrage
- [x] Telechargement securise

### Partage et permissions
- [x] Partage avec utilisateurs specifiques
- [x] Droits granulaires (lecture/ecriture/partage)
- [x] Acces temporaire avec expiration
- [x] Revocation des droits

### Taches et echeances
- [x] Creation de taches liees aux documents
- [x] Gestion des priorites
- [x] Suivi des statuts
- [x] Rappels d'echeances

### Notifications (v2.0)
- [x] Notifications temps reel (AJAX)
- [x] 11 types de notifications
- [x] Priorites avec code couleur
- [x] Rafraichissement automatique
- [x] Support email (simule)

### Versioning documents (v2.0)
- [x] Historique complet des versions
- [x] Upload de nouvelles versions
- [x] Restauration d'anciennes versions
- [x] Telechargement par version

### Tags et recherche avancee (v2.0)
- [x] Tags personnalises avec couleur
- [x] Association N:N documents-tags
- [x] Recherche multi-criteres
- [x] Recherche globale AJAX

### Dashboard ameliore (v2.0)
- [x] Statistiques par type de fichier
- [x] Indicateurs cles (espace, retards)
- [x] Graphique d'activite mensuel
- [x] Alertes visuelles

### Administration
- [x] Tableau de bord statistiques
- [x] Gestion des utilisateurs
- [x] Consultation des logs
- [x] Sauvegardes et restauration

### Securite
- [x] Hashage bcrypt des mots de passe
- [x] Protection CSRF
- [x] Sessions securisees
- [x] Validation des entrees
- [x] Journalisation des actions
- [x] Limitation de tentatives de connexion (v2.0)
- [x] En-tetes HTTP de securite (v2.0)
- [x] Politique de mot de passe stricte (v2.0)

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
| Base de donnees | SQLite | 3 |
| Tests | pytest | 7.4 |

## Livrables

| Livrable | Format | Description |
|----------|--------|-------------|
| Code source | Python | Application complete |
| Base de donnees | SQLite | Schema et donnees initiales |
| Cahier des charges | Markdown | Specifications fonctionnelles |
| Schema BDD | Markdown | MCD et description des tables |
| Documentation technique | Markdown | Architecture et API |
| Tests | Python | Tests unitaires pytest |
| README | Markdown | Guide d'installation |

## Points Forts du Projet

1. **Architecture solide** : 9 modeles, 7 services, 8 blueprints (MVC)
2. **Securite multi-couches** : bcrypt, CSRF, rate limiting, headers HTTP
3. **Versioning documents** : Tracabilite complete des modifications
4. **Tags et recherche avancee** : Organisation flexible multi-criteres
5. **Notifications temps reel** : AJAX, 11 types, rafraichissement auto
6. **Dashboard statistiques** : Graphiques, indicateurs, alertes
7. **41+ tests unitaires** : Modeles, services, securite
8. **Documentation technique** : Complete et detaillee

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
- Tests et validation
