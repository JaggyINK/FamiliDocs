# Cahier des Charges - FamiliDocs

## 1. Presentation du projet

### 1.1 Nom du projet
**FamiliDocs** - Coffre Administratif Numerique Familial

### 1.2 Description
FamiliDocs est une application web permettant aux familles de centraliser, organiser et securiser leurs documents administratifs, tout en offrant un partage controle entre membres de confiance.

## 2. Objectifs

### Objectif principal
Creer un service informatique securise permettant :
- La gestion documentaire familiale
- Le suivi des echeances administratives
- Le partage maitrise de documents et d'informations

### Objectifs secondaires
- Simplifier la gestion administrative pour les personnes agees
- Permettre aux proches d'aider sans tout exposer
- Repondre aux exigences de l'epreuve E5 BTS SIO SLAM

## 3. Public cible

- Parents ages
- Familles
- Aidants
- Utilisateurs peu a l'aise avec le numerique

## 4. Fonctionnalites

### 4.1 Gestion des utilisateurs
- Creation de compte avec validation
- Authentification securisee
- Roles : Administrateur, Utilisateur, Personne de confiance
- Gestion du profil

### 4.2 Gestion des dossiers
- Dossier principal par utilisateur
- Sous-dossiers par categorie (Administratif, Sante, Banque, Logement, Autres)
- Creation/modification/suppression de dossiers

### 4.3 Gestion des documents
- Upload de fichiers (PDF, images, documents Office)
- Metadonnees : nom, type, description, date d'echeance
- Niveaux de confidentialite (prive, partage, restreint)
- Recherche et filtrage

### 4.4 Partage et permissions
- Partage avec utilisateurs specifiques
- Droits granulaires (lecture, modification, telechargement)
- Acces temporaire avec date de fin

### 4.5 Taches et echeances
- Association tache/document
- Rappels automatiques
- Vue liste et calendrier
- Assignation entre membres de la famille
- Dashboard taches famille avec progression et recommandations

### 4.8 Application desktop native
- Interface CustomTkinter (meme BDD PostgreSQL que la version web)
- Documents, dossiers en grille, partages avec droits et duree
- Taches avec assignation, chat familial, gestion utilisateurs
- Executable autonome via PyInstaller

### 4.6 Journalisation
- Historique complet des actions
- Tracabilite des acces

### 4.7 Sauvegarde
- Export de la base de donnees
- Sauvegarde des fichiers
- Restauration complete

## 5. Architecture technique

### 5.1 Technologies
- **Backend** : Python 3.x, Flask
- **Base de donnees** : PostgreSQL 16
- **Frontend** : HTML5, CSS3, Bootstrap 5, JavaScript
- **Securite** : bcrypt, cryptography, pyotp (2FA), Content-Security-Policy

### 5.2 Structure du projet
```
familidocs/
├── app/
│   ├── config/         # Configuration
│   ├── models/         # Modeles de donnees
│   ├── routes/         # Routes/Controleurs
│   ├── services/       # Logique metier
│   ├── templates/      # Vues HTML
│   ├── static/         # CSS, JS, images
│   └── database/       # Base de donnees
├── backups/            # Sauvegardes
├── docs/               # Documentation
├── tests/              # Tests unitaires
└── requirements.txt    # Dependances
```

## 6. Securite

- Hashage des mots de passe (bcrypt) avec validation de complexite
- Authentification a deux facteurs (2FA/TOTP)
- Chiffrement des documents sensibles (AES)
- Gestion des sessions securisee (HttpOnly, SameSite, Secure)
- Controle d'acces strict avec roles hierarchiques
- Protection CSRF (Flask-WTF)
- En-tetes HTTP de securite (CSP, HSTS, X-Frame-Options, etc.)
- Validation des entrees et du content-type des fichiers
- Protection path traversal
- Conformite RGPD (retention logs 180j, export donnees, suppression compte)

## 7. Base de donnees

### Tables principales
- `users` : Utilisateurs
- `folders` : Dossiers
- `documents` : Documents
- `permissions` : Droits d'acces
- `tasks` : Taches/Echeances
- `logs` : Journalisation

## 8. Livrables BTS

- Code source commente
- Base de donnees PostgreSQL
- Cahier des charges
- Documentation technique
- Documentation utilisateur
- Tests unitaires
- Demonstration fonctionnelle

## 9. Planning previsionnel

| Phase | Description |
|-------|-------------|
| 1 | Analyse et conception |
| 2 | Developpement backend |
| 3 | Developpement frontend |
| 4 | Tests et corrections |
| 5 | Documentation |
| 6 | Deploiement |

## 10. Criteres de reussite

- Application fonctionnelle et stable
- Interface utilisateur intuitive
- Securite des donnees garantie
- Documentation complete
- Tests couvrant les fonctionnalites principales
