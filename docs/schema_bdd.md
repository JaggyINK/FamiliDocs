# Schema de Base de Donnees - FamiliDocs

## Modele Conceptuel de Donnees (MCD)

```
┌─────────────────┐       ┌─────────────────┐
│     USERS       │       │    FOLDERS      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ email           │   │   │ name            │
│ username        │   │   │ description     │
│ password_hash   │   │   │ category        │
│ first_name      │   └──>│ owner_id (FK)   │
│ last_name       │       │ parent_id (FK)  │──┐
│ role            │       │ created_at      │  │
│ is_active       │       │ updated_at      │<─┘
│ created_at      │       └─────────────────┘
│ updated_at      │              │
│ last_login      │              │
└─────────────────┘              │
        │                        │
        │     ┌─────────────────┐│
        │     │   DOCUMENTS     ││
        │     ├─────────────────┤│
        │     │ id (PK)         ││
        └────>│ owner_id (FK)   ││
              │ folder_id (FK)  │<┘
              │ name            │
              │ original_filename│
              │ stored_filename │
              │ file_type       │
              │ file_size       │
              │ description     │
              │ confidentiality │
              │ is_encrypted    │
              │ expiry_date     │
              │ created_at      │
              │ updated_at      │
              └─────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐
│ PERMISSIONS │ │  TASKS  │ │  LOGS   │
├─────────────┤ ├─────────┤ ├─────────┤
│ id (PK)     │ │ id (PK) │ │ id (PK) │
│ document_id │ │ owner_id│ │ user_id │
│ user_id     │ │ doc_id  │ │ doc_id  │
│ granted_by  │ │ title   │ │ action  │
│ can_view    │ │ desc    │ │ details │
│ can_edit    │ │ due_date│ │ ip_addr │
│ can_download│ │ priority│ │ user_ag │
│ can_share   │ │ status  │ │created_at│
│ start_date  │ │reminder │ └─────────┘
│ end_date    │ │created_at│
│ created_at  │ │updated_at│
│ updated_at  │ │completed │
│ notes       │ └─────────┘
└─────────────┘
```

## Description des Tables

### Table `users`
Stocke les informations des utilisateurs de l'application.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| email | VARCHAR(120) | Email unique |
| username | VARCHAR(80) | Nom d'utilisateur unique |
| password_hash | VARCHAR(256) | Mot de passe hashe |
| first_name | VARCHAR(80) | Prenom |
| last_name | VARCHAR(80) | Nom |
| role | VARCHAR(20) | Role (admin/user/trusted) |
| is_active | BOOLEAN | Compte actif |
| created_at | DATETIME | Date de creation |
| updated_at | DATETIME | Date de modification |
| last_login | DATETIME | Derniere connexion |

### Table `folders`
Organise les documents en dossiers hierarchiques.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| name | VARCHAR(100) | Nom du dossier |
| description | TEXT | Description |
| category | VARCHAR(50) | Categorie |
| owner_id | INTEGER | FK vers users |
| parent_id | INTEGER | FK vers folders (sous-dossier) |
| created_at | DATETIME | Date de creation |
| updated_at | DATETIME | Date de modification |

### Table `documents`
Stocke les metadonnees des documents uploades.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| name | VARCHAR(200) | Nom affiche |
| original_filename | VARCHAR(255) | Nom original |
| stored_filename | VARCHAR(255) | Nom de stockage |
| file_type | VARCHAR(50) | Type de fichier |
| file_size | INTEGER | Taille en octets |
| description | TEXT | Description |
| confidentiality | VARCHAR(20) | Niveau de confidentialite |
| is_encrypted | BOOLEAN | Document chiffre |
| expiry_date | DATE | Date d'echeance |
| owner_id | INTEGER | FK vers users |
| folder_id | INTEGER | FK vers folders |
| created_at | DATETIME | Date de creation |
| updated_at | DATETIME | Date de modification |

### Table `permissions`
Gere les droits d'acces aux documents.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| document_id | INTEGER | FK vers documents |
| user_id | INTEGER | FK vers users (beneficiaire) |
| granted_by | INTEGER | FK vers users (accordeur) |
| can_view | BOOLEAN | Droit de lecture |
| can_edit | BOOLEAN | Droit de modification |
| can_download | BOOLEAN | Droit de telechargement |
| can_share | BOOLEAN | Droit de partage |
| start_date | DATE | Date de debut |
| end_date | DATE | Date de fin (null = permanent) |
| created_at | DATETIME | Date de creation |
| updated_at | DATETIME | Date de modification |
| notes | TEXT | Notes sur le partage |

### Table `tasks`
Gere les taches et echeances liees aux documents.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| title | VARCHAR(200) | Titre de la tache |
| description | TEXT | Description |
| due_date | DATE | Date d'echeance |
| priority | VARCHAR(20) | Priorite (low/normal/high/urgent) |
| status | VARCHAR(20) | Statut |
| reminder_days | INTEGER | Jours avant rappel |
| owner_id | INTEGER | FK vers users |
| document_id | INTEGER | FK vers documents |
| created_at | DATETIME | Date de creation |
| updated_at | DATETIME | Date de modification |
| completed_at | DATETIME | Date de completion |

### Table `logs`
Journalise toutes les actions importantes.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| action | VARCHAR(50) | Type d'action |
| details | TEXT | Details de l'action |
| ip_address | VARCHAR(45) | Adresse IP |
| user_agent | VARCHAR(255) | Navigateur |
| user_id | INTEGER | FK vers users |
| document_id | INTEGER | FK vers documents |
| created_at | DATETIME | Date de l'action |

## Relations

1. **Users -> Folders** : Un utilisateur possede plusieurs dossiers (1:N)
2. **Users -> Documents** : Un utilisateur possede plusieurs documents (1:N)
3. **Folders -> Documents** : Un dossier contient plusieurs documents (1:N)
4. **Folders -> Folders** : Un dossier peut contenir des sous-dossiers (1:N)
5. **Documents -> Permissions** : Un document a plusieurs permissions (1:N)
6. **Documents -> Tasks** : Un document peut avoir plusieurs taches (1:N)
7. **Users -> Logs** : Les actions d'un utilisateur sont journalisees (1:N)

## Index

- `users.email` : Index unique pour la recherche par email
- `users.username` : Index unique pour la recherche par username
- `documents.stored_filename` : Index unique pour la reference fichier
- `logs.created_at` : Index pour les requetes temporelles
- `permissions(document_id, user_id)` : Contrainte d'unicite
