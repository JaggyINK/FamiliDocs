# Schema de Base de Donnees - FamiliDocs v2.1

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
│ profile_photo   │       └─────────────────┘
│ family_title    │              │
│ created_at      │              │
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
              │ next_review_date│
              │ last_reviewed_at│
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
│ granted_by  │ │ assigned│ │ action  │
│ can_view    │ │ title   │ │ details │
│ can_edit    │ │ desc    │ │ ip_addr │
│ can_download│ │ due_date│ │ user_ag │
│ can_share   │ │ priority│ │created_at│
│ start_date  │ │ status  │ └─────────┘
│ end_date    │ │reminder │
│ created_at  │ │created_at│
│ updated_at  │ │updated_at│
│ notes       │ │completed │
└─────────────┘ └─────────┘


┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    FAMILIES     │    │ FAMILY_MEMBERS  │    │  SHARE_LINKS    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │<───│ family_id (FK)  │    │ id (PK)         │
│ name            │    │ user_id (FK)    │    │ token (UNIQUE)  │
│ description     │    │ role            │    │ document_id (FK)│
│ creator_id (FK) │    │ joined_at       │    │ family_id (FK)  │
│ created_at      │    │ invited_by (FK) │    │ created_by (FK) │
└─────────────────┘    └─────────────────┘    │ expires_at      │
        │                                      │ max_uses        │
        │              ┌─────────────────┐    │ use_count       │
        └─────────────>│   MESSAGES      │    │ is_revoked      │
                       ├─────────────────┤    │ granted_role    │
                       │ id (PK)         │    │ created_at      │
                       │ family_id (FK)  │    └─────────────────┘
                       │ sender_id (FK)  │
                       │ content         │
                       │ is_announcement │
                       │ is_deleted      │
                       │ created_at      │
                       │ updated_at      │
                       └─────────────────┘
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
| profile_photo | VARCHAR(255) | Chemin vers photo de profil |
| family_title | VARCHAR(50) | Titre familial (Papa, Maman, etc.) |
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
| next_review_date | DATE | Date prochaine revision |
| last_reviewed_at | DATETIME | Derniere revision |
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
| assigned_to_id | INTEGER | FK vers users (membre famille assigne) |
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

### Table `notifications`
Gere les notifications temps reel des utilisateurs.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| user_id | INTEGER | FK vers users |
| type | VARCHAR(50) | Type (11 types disponibles) |
| title | VARCHAR(200) | Titre |
| message | TEXT | Contenu |
| priority | VARCHAR(20) | low/normal/high/urgent |
| is_read | BOOLEAN | Lu ou non |
| document_id | INTEGER | FK vers documents (optionnel) |
| task_id | INTEGER | FK vers tasks (optionnel) |
| created_at | DATETIME | Date de creation |
| read_at | DATETIME | Date de lecture |
| expires_at | DATETIME | Expiration auto |

### Table `document_versions`
Historique des versions d'un document.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| document_id | INTEGER | FK vers documents |
| version_number | INTEGER | Numero de version |
| stored_filename | VARCHAR(255) | Fichier de la version |
| original_filename | VARCHAR(255) | Nom original |
| file_size | INTEGER | Taille en octets |
| file_type | VARCHAR(50) | Type de fichier |
| comment | TEXT | Commentaire de modification |
| uploaded_by | INTEGER | FK vers users |
| created_at | DATETIME | Date de creation |

### Table `tags`
Etiquettes pour organiser les documents.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| name | VARCHAR(50) | Nom du tag |
| color | VARCHAR(7) | Couleur hexadecimale |
| owner_id | INTEGER | FK vers users |
| created_at | DATETIME | Date de creation |

**Contrainte** : UNIQUE(name, owner_id)

### Table `document_tags`
Table d'association documents-tags (N:N).

| Colonne | Type | Description |
|---------|------|-------------|
| document_id | INTEGER | FK vers documents (PK) |
| tag_id | INTEGER | FK vers tags (PK) |
| created_at | DATETIME | Date d'association |

### Table `families`
Groupes familiaux pour le partage collaboratif.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| name | VARCHAR(100) | Nom de la famille |
| description | TEXT | Description |
| creator_id | INTEGER | FK vers users (createur) |
| created_at | DATETIME | Date de creation |

### Table `family_members`
Association utilisateur-famille avec role hierarchique.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| family_id | INTEGER | FK vers families |
| user_id | INTEGER | FK vers users |
| role | VARCHAR(30) | Role dans la famille (8 roles) |
| joined_at | DATETIME | Date d'adhesion |
| invited_by | INTEGER | FK vers users (qui a invite) |

**Contrainte** : UNIQUE(family_id, user_id)

**Roles disponibles** :
| Role | Description |
|------|-------------|
| chef_famille | Administration complete (max 2 par famille) |
| admin | Gestion complete |
| parent | Gestion documents et taches |
| gestionnaire | Ajout/suppression de documents |
| enfant | Acces limite supervise |
| editeur | Modification des documents partages |
| lecteur | Consultation uniquement |
| invite | Acces temporaire limite |

### Table `share_links`
Liens de partage securises a usage limite.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| token | VARCHAR(64) | Token unique securise |
| document_id | INTEGER | FK vers documents (optionnel) |
| family_id | INTEGER | FK vers families (optionnel) |
| created_by | INTEGER | FK vers users |
| expires_at | DATETIME | Date d'expiration |
| max_uses | INTEGER | Nombre max d'utilisations |
| use_count | INTEGER | Compteur d'utilisation |
| is_revoked | BOOLEAN | Lien revoque |
| granted_role | VARCHAR(30) | Role attribue au destinataire |
| created_at | DATETIME | Date de creation |

### Table `messages`
Chat familial avec systeme d'annonces.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Cle primaire |
| family_id | INTEGER | FK vers families |
| sender_id | INTEGER | FK vers users |
| content | TEXT | Contenu du message |
| is_announcement | BOOLEAN | Message important/annonce |
| is_deleted | BOOLEAN | Suppression douce |
| created_at | DATETIME | Date d'envoi |
| updated_at | DATETIME | Date de modification |

## Relations

1. **Users -> Folders** : Un utilisateur possede plusieurs dossiers (1:N)
2. **Users -> Documents** : Un utilisateur possede plusieurs documents (1:N)
3. **Folders -> Documents** : Un dossier contient plusieurs documents (1:N)
4. **Folders -> Folders** : Un dossier peut contenir des sous-dossiers (1:N)
5. **Documents -> Permissions** : Un document a plusieurs permissions (1:N)
6. **Documents -> Tasks** : Un document peut avoir plusieurs taches (1:N)
7. **Users -> Logs** : Les actions d'un utilisateur sont journalisees (1:N)
8. **Users -> Notifications** : Un utilisateur recoit plusieurs notifications (1:N)
9. **Documents -> Versions** : Un document a plusieurs versions (1:N)
10. **Documents <-> Tags** : Relation N:N via document_tags
11. **Users -> Tags** : Un utilisateur possede plusieurs tags (1:N)
12. **Users -> Families** : Un utilisateur cree des familles (1:N)
13. **Users <-> Families** : Relation N:N via family_members
14. **Families -> Messages** : Une famille contient des messages (1:N)
15. **Users -> Messages** : Un utilisateur envoie des messages (1:N)
16. **Share_links -> Documents/Families** : Liens de partage (1:N)
17. **Users -> Tasks (assigned)** : Assignation de taches a des membres (1:N)

## Index

- `users.email` : Index unique pour la recherche par email
- `users.username` : Index unique pour la recherche par username
- `documents.stored_filename` : Index unique pour la reference fichier
- `logs.created_at` : Index pour les requetes temporelles
- `notifications.created_at` : Index pour le tri chronologique
- `document_versions.created_at` : Index pour le tri des versions
- `tags.name` : Index pour la recherche par nom
- `share_links.token` : Index unique pour la recherche par token
- `permissions(document_id, user_id)` : Contrainte d'unicite
- `tags(name, owner_id)` : Contrainte d'unicite
- `family_members(family_id, user_id)` : Contrainte d'unicite
