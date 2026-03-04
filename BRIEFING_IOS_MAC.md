# BRIEFING iOS - FamiliDocs (Mac / Xcode)

> Ce fichier contient TOUT ce dont Claude a besoin pour creer l'app iOS native.
> A donner tel quel a Claude sur le MacBook avec Xcode.

---

## Table des matieres

1. [Contexte du projet](#1-contexte-du-projet)
2. [Pre-requis](#2-pre-requis)
3. [Specification API REST complete](#3-specification-api-rest-complete)
4. [Structure du projet Xcode](#4-structure-du-projet-xcode)
5. [Code Swift complet](#5-code-swift-complet)
6. [Configuration Info.plist](#6-configuration-infoplist)
7. [Deploiement sur iPhone](#7-deploiement-sur-iphone)

---

## 1. Contexte du projet

**FamiliDocs** est un coffre-fort numerique familial. Le backend Flask tourne sur un PC Windows et expose une API REST JSON. L'app iOS se connecte a cette API via le reseau local Wi-Fi.

Fonctionnalites principales :
- Authentification (login/register) avec JWT
- Gestion de documents (upload, download, partage, tags)
- Dossiers hierarchiques (categories)
- Taches avec echeances et priorites
- Familles (groupes) avec roles et chat integre
- Notifications

---

## 2. Pre-requis

- **Xcode 15+** (gratuit sur le Mac App Store)
- **Compte Apple gratuit** (pour deployer sur son propre iPhone)
- **iOS 17+** comme cible de deploiement
- Le PC Windows avec le serveur Flask doit etre sur le **meme reseau Wi-Fi**
- Connaitre l'**adresse IP du PC** (ex: `192.168.1.42`)

---

## 3. Specification API REST complete

### 3.1 Base URL

```
http://<IP_DU_PC>:5000/api
```

Exemple : `http://192.168.1.42:5000/api`

### 3.2 Authentification

Toutes les requetes (sauf login/register) doivent inclure le header :
```
Authorization: Bearer <token_jwt>
```

Le token est obtenu via `/api/auth/login` et expire apres 72h.

### 3.3 Format des erreurs

Toutes les erreurs retournent :
```json
{"error": "Message d'erreur en francais"}
```

Codes HTTP utilises : `400` (bad request), `401` (non authentifie), `403` (interdit), `404` (introuvable), `409` (conflit).

### 3.4 Format de pagination

Les endpoints pagines retournent :
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### 3.5 Endpoints detailles

---

#### AUTH - Authentification

**POST `/api/auth/login`**
```
Request:  {"email": "string", "password": "string"}
Response: {"token": "jwt_string", "user": User}
Errors:   401 (identifiants incorrects), 403 (compte desactive)
```

**POST `/api/auth/register`**
```
Request:  {"email": "string", "username": "string", "password": "string (min 8 chars)",
           "first_name": "string", "last_name": "string"}
Response: 201 {"token": "jwt_string", "user": User}
Errors:   400 (champs manquants), 409 (email/username deja pris)
```

**GET `/api/auth/me`** (Auth requise)
```
Response: {"user": User}
```

**PUT `/api/auth/me`** (Auth requise)
```
Request:  {"first_name"?: "string", "last_name"?: "string", "email"?: "string", "family_title"?: "string"}
Response: {"user": User}
```

**POST `/api/auth/change-password`** (Auth requise)
```
Request:  {"old_password": "string", "new_password": "string (min 8 chars)"}
Response: {"message": "Mot de passe modifie avec succes"}
```

**Objet User :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "family_title": "Pere",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00",
  "last_login": "2026-03-04T08:00:00",
  "profile_photo": "photo.jpg"
}
```

---

#### DOCUMENTS

**GET `/api/documents`** (Auth requise)
```
Query: folder_id (int), search (string), sort (name|created_at|file_size),
       order (asc|desc), page (int), per_page (int, defaut 20)
Response: {
  "documents": [Document],
  "total": 42, "page": 1, "pages": 3, "has_next": true, "has_prev": false
}
```

**GET `/api/documents/shared`** (Auth requise)
```
Response: {"documents": [Document + permissions]}
Chaque document a un champ "permissions": {"can_view":true, "can_edit":false, "can_download":true, "can_share":false}
```

**GET `/api/documents/:id`** (Auth requise)
```
Response: {"document": Document + tags[] + permissions[] (si proprietaire)}
```

**POST `/api/documents`** (Auth requise, **multipart/form-data**)
```
Form fields:
  file (fichier obligatoire)
  name (string, defaut: nom du fichier)
  description (string, optionnel)
  folder_id (int, optionnel)
  confidentiality (public|private|restricted, defaut: private)
  expiry_date (YYYY-MM-DD, optionnel)
Response: 201 {"document": Document}
Extensions autorisees: pdf, png, jpg, jpeg, doc, docx, txt, xls, xlsx, gif
Taille max: 16 MB
```

**PUT `/api/documents/:id`** (Auth requise)
```
Request: {"name"?: "string", "description"?: "string", "folder_id"?: int|null,
          "confidentiality"?: "string", "expiry_date"?: "YYYY-MM-DD"|null,
          "next_review_date"?: "YYYY-MM-DD"|null}
Response: {"document": Document}
```

**DELETE `/api/documents/:id`** (Auth requise, proprietaire/admin)
```
Response: {"message": "Document supprime"}
```

**GET `/api/documents/:id/download`** (Auth requise)
```
Response: fichier binaire (Content-Disposition: attachment)
```

**POST `/api/documents/:id/share`** (Auth requise, proprietaire)
```
Request: {"user_ids": [1, 2], "can_edit"?: false, "can_download"?: true,
          "can_share"?: false, "end_date"?: "YYYY-MM-DD"}
Response: {"message": "Document partage avec N utilisateur(s)"}
```

**DELETE `/api/documents/:id/revoke/:user_id`** (Auth requise, proprietaire)
```
Response: {"message": "Permission revoquee"}
```

**POST `/api/documents/:id/tags`** (Auth requise)
```
Request: {"tag_id": int}  OU  {"name": "string", "color"?: "#hex"}
Response: {"tag": {"id": 1, "name": "urgent", "color": "#ff0000"}}
```

**DELETE `/api/documents/:id/tags/:tag_id`** (Auth requise)
```
Response: {"message": "Tag retire"}
```

**Objet Document :**
```json
{
  "id": 1,
  "name": "Facture EDF",
  "original_filename": "facture_edf_2026.pdf",
  "file_type": "pdf",
  "file_size": 245000,
  "description": "Facture electricite mars 2026",
  "confidentiality": "private",
  "is_encrypted": false,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00",
  "expiry_date": "2027-01-15",
  "next_review_date": null,
  "is_expired": false,
  "is_expiring_soon": false,
  "owner_id": 1,
  "folder_id": 2,
  "folder_name": "Administratif",
  "tags": [{"id": 1, "name": "facture", "color": "#28a745"}]
}
```

---

#### DOSSIERS

**GET `/api/folders`** (Auth requise)
```
Query: parent_id (int, optionnel - pour sous-dossiers)
Response: {"folders": [Folder]}
```

**GET `/api/folders/:id`** (Auth requise)
```
Response: {"folder": Folder + documents: [Document] + subfolders: [Folder] + path: "string"}
Le champ path est une string du type "Parent / Enfant / Dossier".
Les documents sont des objets Document complets (meme schema que GET /api/documents).
```

**POST `/api/folders`** (Auth requise)
```
Request: {"name": "string", "description"?: "string",
          "category"?: "Administratif|Sante|Banque|Logement|Autres",
          "parent_id"?: int}
Response: 201 {"folder": Folder}
```

**PUT `/api/folders/:id`** (Auth requise)
```
Request: {"name"?: "string", "description"?: "string", "category"?: "string"}
Response: {"folder": Folder}
```

**DELETE `/api/folders/:id`** (Auth requise, doit etre vide)
```
Response: {"message": "Dossier supprime"}
Errors: 400 si le dossier contient des documents ou sous-dossiers
```

**Objet Folder :**
```json
{
  "id": 1,
  "name": "Administratif",
  "description": "Documents administratifs",
  "category": "Administratif",
  "parent_id": null,
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00",
  "document_count": 5,
  "subfolder_count": 2
}
```

---

#### TACHES

**GET `/api/tasks`** (Auth requise)
```
Query: status (pending|in_progress|completed|cancelled),
       priority (low|normal|high|urgent), page (int), per_page (int)
Response: {"tasks": [Task], "total":..., "page":..., "pages":..., "has_next":..., "has_prev":...}
```

**GET `/api/tasks/overdue`** (Auth requise)
```
Response: {"tasks": [Task]}
```

**GET `/api/tasks/upcoming`** (Auth requise)
```
Query: days (int, defaut 30)
Response: {"tasks": [Task]}
```

**GET `/api/tasks/:id`** (Auth requise)
```
Response: {"task": Task}
```

**POST `/api/tasks`** (Auth requise)
```
Request: {"title": "string", "due_date": "YYYY-MM-DD",
          "description"?: "string", "priority"?: "low|normal|high|urgent",
          "document_id"?: int, "reminder_days"?: int, "assigned_to_id"?: int}
Response: 201 {"task": Task}
```

**PUT `/api/tasks/:id`** (Auth requise)
```
Request: {"title"?: "string", "description"?: "string", "due_date"?: "YYYY-MM-DD",
          "priority"?: "string", "reminder_days"?: int, "document_id"?: int|null,
          "assigned_to_id"?: int|null}
Response: {"task": Task}
```

**PUT `/api/tasks/:id/status`** (Auth requise)
```
Request: {"status": "pending|in_progress|completed|cancelled"}
Response: {"task": Task}
```

**DELETE `/api/tasks/:id`** (Auth requise, proprietaire/admin)
```
Response: {"message": "Tache supprimee"}
```

**Objet Task :**
```json
{
  "id": 1,
  "title": "Renouveler passeport",
  "description": "Prendre RDV en mairie",
  "due_date": "2026-06-01",
  "priority": "high",
  "status": "pending",
  "reminder_days": 7,
  "owner_id": 1,
  "owner_name": "John Doe",
  "document_id": null,
  "assigned_to_id": 2,
  "assigned_to_name": "Jane Doe",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00",
  "completed_at": null,
  "is_overdue": false
}
```

---

#### FAMILLES

**GET `/api/families`** (Auth requise)
```
Response: {"families": [Family]}
```

**GET `/api/families/:id`** (Auth requise, membre uniquement)
```
Response: {"family": Family + members[]}
Chaque member: {"id":1, "user_id":1, "user_name":"John Doe",
                "user_email":"john@example.com", "role":"chef_famille",
                "joined_at":"2026-01-15T10:30:00"}
```

**POST `/api/families`** (Auth requise)
```
Request: {"name": "string", "description"?: "string"}
Response: 201 {"family": Family}
Le createur est automatiquement ajoute comme "chef_famille".
```

**PUT `/api/families/:id`** (Auth requise, chef_famille/admin)
```
Request: {"name"?: "string", "description"?: "string"}
Response: {"family": Family}
```

**DELETE `/api/families/:id`** (Auth requise, createur uniquement)
```
Response: {"message": "Famille supprimee"}
```

**POST `/api/families/:id/invite`** (Auth requise, gestionnaire+)
```
Request: {"expires_hours"?: 24, "max_uses"?: 1,
          "role"?: "lecteur|invite|enfant|editeur|gestionnaire|parent|admin|chef_famille"}
Response: 201 {"invite": {"token": "abc...", "expires_at": "...", "max_uses": 1, "role": "lecteur"}}
```

**POST `/api/families/join/:token`** (Auth requise)
```
Response: {"message": "Vous avez rejoint la famille ...", "family": Family}
Errors: 400 (lien invalide/expire), 409 (deja membre)
```

**PUT `/api/families/:id/members/:member_id/role`** (Auth requise, gestionnaire+)
```
Request: {"role": "string"}
Response: {"message": "Role modifie en ..."}
Roles valides: chef_famille (max 2), admin, parent, gestionnaire, enfant, editeur, lecteur, invite
```

**DELETE `/api/families/:id/members/:member_id`** (Auth requise, gestionnaire+)
```
Response: {"message": "Membre retire"}
```

**POST `/api/families/:id/leave`** (Auth requise)
```
Response: {"message": "Vous avez quitte la famille"}
Errors: 400 si createur
```

**Objet Family :**
```json
{
  "id": 1,
  "name": "Famille Dupont",
  "description": "Notre famille",
  "creator_id": 1,
  "created_at": "2026-01-15T10:30:00",
  "member_count": 4,
  "my_role": "chef_famille"
}
```

---

#### CHAT FAMILIAL

**GET `/api/families/:id/messages`** (Auth requise, membre)
```
Query: offset (int, defaut 0), limit (int, defaut 50, max 100)
Response: {"messages": [Message], "total": 42, "has_more": true}
Les messages sont en ordre chronologique (plus ancien en premier).
```

**POST `/api/families/:id/messages`** (Auth requise, membre)
```
Request: {"content": "string (max 2000 chars)", "is_announcement"?: false}
Response: 201 {"message": Message}
Note: is_announcement reserve aux roles admin, chef_famille, parent.
```

**PUT `/api/messages/:id`** (Auth requise, auteur uniquement)
```
Request: {"content": "string"}
Response: {"message": Message}
```

**DELETE `/api/messages/:id`** (Auth requise, auteur/admin)
```
Response: {"message": "Message supprime"}
Note: soft delete - le contenu est remplace par "[Message supprime]"
```

**Objet Message :**
```json
{
  "id": 1,
  "family_id": 1,
  "sender_id": 1,
  "sender_name": "John Doe",
  "content": "Bonjour tout le monde !",
  "is_announcement": false,
  "is_deleted": false,
  "created_at": "2026-03-04T10:30:00",
  "updated_at": "2026-03-04T10:30:00"
}
```

---

#### NOTIFICATIONS

**GET `/api/notifications`** (Auth requise)
```
Query: unread (1 pour non-lues seulement), type (string), page (int), per_page (int)
Response: {"notifications": [Notification], "total":..., "page":..., "pages":...,
           "has_next":..., "unread_count": 5}
```

**GET `/api/notifications/count`** (Auth requise)
```
Response: {"count": 5}
```

**POST `/api/notifications/:id/read`** (Auth requise)
```
Response: {"message": "Notification marquee comme lue"}
```

**POST `/api/notifications/read-all`** (Auth requise)
```
Response: {"message": "Toutes les notifications marquees comme lues"}
```

**DELETE `/api/notifications/:id`** (Auth requise)
```
Response: {"message": "Notification supprimee"}
```

**POST `/api/notifications/delete-read`** (Auth requise)
```
Response: {"message": "Notifications lues supprimees"}
```

**Objet Notification :**
```json
{
  "id": 1,
  "type": "task_due",
  "title": "Tache bientot due",
  "message": "La tache 'Renouveler passeport' arrive a echeance dans 3 jours",
  "priority": "normal",
  "is_read": false,
  "document_id": null,
  "task_id": 1,
  "created_at": "2026-03-04T08:00:00",
  "read_at": null
}
```

Types possibles : `task_due`, `task_overdue`, `document_expiry`, `document_expired`, `document_shared`, `permission_granted`, `permission_revoked`, `permission_expiring`, `task_assigned`, `system`, `backup_complete`, `welcome`.

---

## 4. Structure du projet Xcode

Creer un nouveau projet Xcode : **App** > **SwiftUI** > **FamiliDocs** > iOS 17+.

```
FamiliDocs/
  FamiliDocsApp.swift              # Point d'entree
  Info.plist                        # Config HTTP local
  Models/
    User.swift                      # Modele User
    Document.swift                  # Modele Document
    Folder.swift                    # Modele Folder
    Task.swift                      # Modele FDTask
    Family.swift                    # Modele Family, FamilyMember
    Message.swift                   # Modele ChatMessage
    Notification.swift              # Modele FDNotification
    APIResponse.swift               # Types generiques de reponse
  Services/
    APIService.swift                # Client HTTP central (URLSession)
    AuthService.swift               # Login, register, token storage
    KeychainService.swift           # Stockage securise du token
  ViewModels/
    AuthViewModel.swift             # State auth (login/register)
    DocumentsViewModel.swift        # State documents
    FoldersViewModel.swift          # State dossiers
    TasksViewModel.swift            # State taches
    FamiliesViewModel.swift         # State familles
    ChatViewModel.swift             # State chat
    NotificationsViewModel.swift    # State notifications
  Views/
    ContentView.swift               # Router principal (auth vs main)
    Auth/
      LoginView.swift
      RegisterView.swift
    Main/
      MainTabView.swift             # Tab bar principal
    Documents/
      DocumentsListView.swift
      DocumentDetailView.swift
      DocumentUploadView.swift
    Folders/
      FoldersListView.swift
      FolderDetailView.swift
    Tasks/
      TasksListView.swift
      TaskDetailView.swift
      TaskFormView.swift
    Families/
      FamiliesListView.swift
      FamilyDetailView.swift
      ChatView.swift
    Notifications/
      NotificationsListView.swift
    Components/
      DocumentRow.swift
      TaskRow.swift
      PriorityBadge.swift
      StatusBadge.swift
      LoadingView.swift
      ErrorView.swift
```

---

## 5. Code Swift complet

### 5.1 `FamiliDocsApp.swift`

```swift
import SwiftUI

@main
struct FamiliDocsApp: App {
    @StateObject private var authVM = AuthViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authVM)
        }
    }
}
```

### 5.2 Models

#### `Models/User.swift`

```swift
import Foundation

struct User: Codable, Identifiable {
    let id: Int
    let email: String
    let username: String
    let firstName: String
    let lastName: String
    let role: String
    let familyTitle: String?
    let isActive: Bool
    let createdAt: String?
    let lastLogin: String?
    let profilePhoto: String?

    enum CodingKeys: String, CodingKey {
        case id, email, username, role
        case firstName = "first_name"
        case lastName = "last_name"
        case familyTitle = "family_title"
        case isActive = "is_active"
        case createdAt = "created_at"
        case lastLogin = "last_login"
        case profilePhoto = "profile_photo"
    }

    var fullName: String { "\(firstName) \(lastName)" }
}
```

#### `Models/Document.swift`

```swift
import Foundation

struct FDDocument: Codable, Identifiable {
    let id: Int
    let name: String
    let originalFilename: String
    let fileType: String?
    let fileSize: Int?
    let description: String?
    let confidentiality: String
    let isEncrypted: Bool
    let createdAt: String?
    let updatedAt: String?
    let expiryDate: String?
    let nextReviewDate: String?
    let isExpired: Bool
    let isExpiringSoon: Bool
    let ownerId: Int
    let folderId: Int?
    let folderName: String?
    let tags: [Tag]

    enum CodingKeys: String, CodingKey {
        case id, name, description, confidentiality, tags
        case originalFilename = "original_filename"
        case fileType = "file_type"
        case fileSize = "file_size"
        case isEncrypted = "is_encrypted"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case expiryDate = "expiry_date"
        case nextReviewDate = "next_review_date"
        case isExpired = "is_expired"
        case isExpiringSoon = "is_expiring_soon"
        case ownerId = "owner_id"
        case folderId = "folder_id"
        case folderName = "folder_name"
    }

    var fileSizeFormatted: String {
        guard let size = fileSize else { return "—" }
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(size))
    }

    var fileIcon: String {
        switch fileType?.lowercased() {
        case "pdf": return "doc.fill"
        case "png", "jpg", "jpeg", "gif": return "photo.fill"
        case "doc", "docx": return "doc.text.fill"
        case "xls", "xlsx": return "tablecells.fill"
        case "txt": return "doc.plaintext.fill"
        default: return "doc.fill"
        }
    }
}

struct Tag: Codable, Identifiable {
    let id: Int
    let name: String
    let color: String
}

struct DocumentPermission: Codable {
    let canView: Bool
    let canEdit: Bool
    let canDownload: Bool
    let canShare: Bool

    enum CodingKeys: String, CodingKey {
        case canView = "can_view"
        case canEdit = "can_edit"
        case canDownload = "can_download"
        case canShare = "can_share"
    }
}
```

#### `Models/Folder.swift`

```swift
import Foundation

struct Folder: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String?
    let category: String
    let parentId: Int?
    let createdAt: String?
    let updatedAt: String?
    let documentCount: Int
    let subfolderCount: Int

    enum CodingKeys: String, CodingKey {
        case id, name, description, category
        case parentId = "parent_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case documentCount = "document_count"
        case subfolderCount = "subfolder_count"
    }

    var categoryIcon: String {
        switch category {
        case "Administratif": return "building.columns.fill"
        case "Sante": return "heart.fill"
        case "Banque": return "banknote.fill"
        case "Logement": return "house.fill"
        default: return "folder.fill"
        }
    }
}
```

#### `Models/Task.swift`

```swift
import Foundation

struct FDTask: Codable, Identifiable {
    let id: Int
    let title: String
    let description: String?
    let dueDate: String?
    let priority: String
    let status: String
    let reminderDays: Int
    let ownerId: Int
    let ownerName: String?
    let documentId: Int?
    let assignedToId: Int?
    let assignedToName: String?
    let createdAt: String?
    let updatedAt: String?
    let completedAt: String?
    let isOverdue: Bool

    enum CodingKeys: String, CodingKey {
        case id, title, description, priority, status
        case dueDate = "due_date"
        case reminderDays = "reminder_days"
        case ownerId = "owner_id"
        case ownerName = "owner_name"
        case documentId = "document_id"
        case assignedToId = "assigned_to_id"
        case assignedToName = "assigned_to_name"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case completedAt = "completed_at"
        case isOverdue = "is_overdue"
    }

    var priorityColor: String {
        switch priority {
        case "urgent": return "red"
        case "high": return "orange"
        case "normal": return "blue"
        case "low": return "gray"
        default: return "blue"
        }
    }

    var statusLabel: String {
        switch status {
        case "pending": return "En attente"
        case "in_progress": return "En cours"
        case "completed": return "Termine"
        case "cancelled": return "Annule"
        default: return status
        }
    }

    var dueDateFormatted: String? {
        guard let dueDate else { return nil }
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withFullDate]
        guard let date = isoFormatter.date(from: dueDate) else { return dueDate }
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.locale = Locale(identifier: "fr_FR")
        return formatter.string(from: date)
    }
}
```

#### `Models/Family.swift`

```swift
import Foundation

struct Family: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String?
    let creatorId: Int
    let createdAt: String?
    let memberCount: Int
    let myRole: String?

    enum CodingKeys: String, CodingKey {
        case id, name, description
        case creatorId = "creator_id"
        case createdAt = "created_at"
        case memberCount = "member_count"
        case myRole = "my_role"
    }
}

struct FamilyMember: Codable, Identifiable {
    let id: Int
    let userId: Int
    let userName: String?
    let userEmail: String?
    let role: String
    let joinedAt: String?

    enum CodingKeys: String, CodingKey {
        case id, role
        case userId = "user_id"
        case userName = "user_name"
        case userEmail = "user_email"
        case joinedAt = "joined_at"
    }

    var roleLabel: String {
        switch role {
        case "chef_famille": return "Chef de famille"
        case "admin": return "Administrateur"
        case "parent": return "Parent"
        case "gestionnaire": return "Gestionnaire"
        case "enfant": return "Enfant"
        case "editeur": return "Editeur"
        case "lecteur": return "Lecteur"
        case "invite": return "Invite"
        default: return role
        }
    }
}

struct InviteLink: Codable {
    let token: String
    let expiresAt: String
    let maxUses: Int
    let role: String

    enum CodingKeys: String, CodingKey {
        case token, role
        case expiresAt = "expires_at"
        case maxUses = "max_uses"
    }
}
```

#### `Models/Message.swift`

```swift
import Foundation

struct ChatMessage: Codable, Identifiable {
    let id: Int
    let familyId: Int
    let senderId: Int
    let senderName: String?
    let content: String
    let isAnnouncement: Bool
    let isDeleted: Bool
    let createdAt: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id, content
        case familyId = "family_id"
        case senderId = "sender_id"
        case senderName = "sender_name"
        case isAnnouncement = "is_announcement"
        case isDeleted = "is_deleted"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}
```

#### `Models/Notification.swift`

```swift
import Foundation

struct FDNotification: Codable, Identifiable {
    let id: Int
    let type: String
    let title: String
    let message: String
    let priority: String
    let isRead: Bool
    let documentId: Int?
    let taskId: Int?
    let createdAt: String?
    let readAt: String?

    enum CodingKeys: String, CodingKey {
        case id, type, title, message, priority
        case isRead = "is_read"
        case documentId = "document_id"
        case taskId = "task_id"
        case createdAt = "created_at"
        case readAt = "read_at"
    }

    var typeIcon: String {
        switch type {
        case "task_due", "task_overdue": return "clock.badge.exclamationmark.fill"
        case "task_assigned": return "person.badge.clock.fill"
        case "document_expiry", "document_expired": return "doc.badge.clock.fill"
        case "document_shared": return "doc.badge.plus"
        case "permission_granted": return "lock.open.fill"
        case "permission_revoked": return "lock.fill"
        case "welcome": return "hand.wave.fill"
        case "system": return "gear"
        default: return "bell.fill"
        }
    }
}
```

#### `Models/APIResponse.swift`

```swift
import Foundation

struct AuthResponse: Codable {
    let token: String
    let user: User
}

struct UserResponse: Codable {
    let user: User
}

struct DocumentsResponse: Codable {
    let documents: [FDDocument]
    let total: Int?
    let page: Int?
    let pages: Int?
    let hasNext: Bool?
    let hasPrev: Bool?

    enum CodingKeys: String, CodingKey {
        case documents, total, page, pages
        case hasNext = "has_next"
        case hasPrev = "has_prev"
    }
}

struct SingleDocumentResponse: Codable {
    let document: FDDocument
}

struct FoldersResponse: Codable {
    let folders: [Folder]
}

struct SingleFolderResponse: Codable {
    let folder: FolderDetail
}

struct FolderDetail: Codable {
    let id: Int
    let name: String
    let description: String?
    let category: String
    let parentId: Int?
    let createdAt: String?
    let updatedAt: String?
    let documentCount: Int
    let subfolderCount: Int
    let documents: [FDDocument]?
    let subfolders: [Folder]?
    let path: String?

    enum CodingKeys: String, CodingKey {
        case id, name, description, category, documents, subfolders, path
        case parentId = "parent_id"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case documentCount = "document_count"
        case subfolderCount = "subfolder_count"
    }
}

struct TasksResponse: Codable {
    let tasks: [FDTask]
    let total: Int?
    let page: Int?
    let pages: Int?
    let hasNext: Bool?
    let hasPrev: Bool?

    enum CodingKeys: String, CodingKey {
        case tasks, total, page, pages
        case hasNext = "has_next"
        case hasPrev = "has_prev"
    }
}

struct SingleTaskResponse: Codable {
    let task: FDTask
}

struct FamiliesResponse: Codable {
    let families: [Family]
}

struct FamilyDetailResponse: Codable {
    let family: FamilyDetail
}

struct FamilyDetail: Codable {
    let id: Int
    let name: String
    let description: String?
    let creatorId: Int
    let createdAt: String?
    let memberCount: Int
    let myRole: String?
    let members: [FamilyMember]

    enum CodingKeys: String, CodingKey {
        case id, name, description, members
        case creatorId = "creator_id"
        case createdAt = "created_at"
        case memberCount = "member_count"
        case myRole = "my_role"
    }
}

struct MessagesResponse: Codable {
    let messages: [ChatMessage]
    let total: Int
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case messages, total
        case hasMore = "has_more"
    }
}

struct SingleMessageResponse: Codable {
    let message: ChatMessage
}

struct NotificationsResponse: Codable {
    let notifications: [FDNotification]
    let total: Int?
    let page: Int?
    let pages: Int?
    let hasNext: Bool?
    let unreadCount: Int?

    enum CodingKeys: String, CodingKey {
        case notifications, total, page, pages
        case hasNext = "has_next"
        case unreadCount = "unread_count"
    }
}

struct CountResponse: Codable {
    let count: Int
}

struct InviteResponse: Codable {
    let invite: InviteLink
}

struct MessageResponse: Codable {
    let message: String
}

struct SingleFamilyResponse: Codable {
    let family: Family
}

struct JoinFamilyResponse: Codable {
    let message: String
    let family: Family
}

struct ErrorResponse: Codable {
    let error: String
}
```

### 5.3 Services

#### `Services/KeychainService.swift`

```swift
import Foundation
import Security

enum KeychainService {
    private static let tokenKey = "com.familidocs.jwt_token"
    private static let serverKey = "com.familidocs.server_url"

    static func saveToken(_ token: String) {
        save(key: tokenKey, value: token)
    }

    static func getToken() -> String? {
        get(key: tokenKey)
    }

    static func deleteToken() {
        delete(key: tokenKey)
    }

    static func saveServerURL(_ url: String) {
        save(key: serverKey, value: url)
    }

    static func getServerURL() -> String? {
        get(key: serverKey)
    }

    // MARK: - Private

    private static func save(key: String, value: String) {
        let data = value.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)

        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        SecItemAdd(addQuery as CFDictionary, nil)
    }

    private static func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
```

#### `Services/APIService.swift`

```swift
import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case noToken
    case serverError(String)
    case decodingError
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "URL invalide"
        case .noToken: return "Non authentifie"
        case .serverError(let msg): return msg
        case .decodingError: return "Erreur de decodage"
        case .networkError(let err): return err.localizedDescription
        }
    }
}

class APIService {
    static let shared = APIService()

    var baseURL: String {
        KeychainService.getServerURL() ?? "http://192.168.1.42:5000/api"
    }

    private let session: URLSession
    private let decoder: JSONDecoder

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        session = URLSession(configuration: config)
        decoder = JSONDecoder()
    }

    // MARK: - Generic request

    func request<T: Decodable>(
        _ method: String,
        path: String,
        body: [String: Any]? = nil,
        query: [String: String]? = nil,
        authenticated: Bool = true
    ) async throws -> T {
        var urlString = "\(baseURL)\(path)"

        if let query, !query.isEmpty {
            let queryString = query.map { "\($0.key)=\($0.value)" }.joined(separator: "&")
            urlString += "?\(queryString)"
        }

        guard let url = URL(string: urlString) else { throw APIError.invalidURL }

        var request = URLRequest(url: url)
        request.httpMethod = method

        if authenticated {
            guard let token = KeychainService.getToken() else { throw APIError.noToken }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }

        if httpResponse.statusCode >= 400 {
            if let errorResponse = try? decoder.decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.error)
            }
            throw APIError.serverError("Erreur serveur (\(httpResponse.statusCode))")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError
        }
    }

    // MARK: - Multipart upload

    func uploadFile<T: Decodable>(
        path: String,
        fileData: Data,
        fileName: String,
        mimeType: String,
        fields: [String: String] = [:]
    ) async throws -> T {
        let urlString = "\(baseURL)\(path)"
        guard let url = URL(string: urlString) else { throw APIError.invalidURL }
        guard let token = KeychainService.getToken() else { throw APIError.noToken }

        let boundary = UUID().uuidString
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        // Champs texte
        for (key, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        // Fichier
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.networkError(URLError(.badServerResponse))
        }

        if httpResponse.statusCode >= 400 {
            if let errorResponse = try? decoder.decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.error)
            }
            throw APIError.serverError("Erreur upload (\(httpResponse.statusCode))")
        }

        return try decoder.decode(T.self, from: data)
    }

    // MARK: - Download

    func downloadFile(path: String) async throws -> (Data, String) {
        let urlString = "\(baseURL)\(path)"
        guard let url = URL(string: urlString) else { throw APIError.invalidURL }
        guard let token = KeychainService.getToken() else { throw APIError.noToken }

        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIError.serverError("Erreur de telechargement")
        }

        let filename = httpResponse.suggestedFilename ?? "document"
        return (data, filename)
    }
}
```

#### `Services/AuthService.swift`

```swift
import Foundation

class AuthService {
    static let shared = AuthService()
    private let api = APIService.shared

    func login(email: String, password: String) async throws -> User {
        let response: AuthResponse = try await api.request(
            "POST", path: "/auth/login",
            body: ["email": email, "password": password],
            authenticated: false
        )
        KeychainService.saveToken(response.token)
        return response.user
    }

    func register(email: String, username: String, password: String,
                  firstName: String, lastName: String) async throws -> User {
        let response: AuthResponse = try await api.request(
            "POST", path: "/auth/register",
            body: [
                "email": email, "username": username, "password": password,
                "first_name": firstName, "last_name": lastName
            ],
            authenticated: false
        )
        KeychainService.saveToken(response.token)
        return response.user
    }

    func fetchProfile() async throws -> User {
        let response: UserResponse = try await api.request("GET", path: "/auth/me")
        return response.user
    }

    func logout() {
        KeychainService.deleteToken()
    }

    var isLoggedIn: Bool {
        KeychainService.getToken() != nil
    }
}
```

### 5.4 ViewModels

#### `ViewModels/AuthViewModel.swift`

```swift
import SwiftUI

@MainActor
class AuthViewModel: ObservableObject {
    @Published var currentUser: User?
    @Published var isAuthenticated = false
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var serverURL: String = KeychainService.getServerURL() ?? "http://192.168.1.42:5000/api"

    init() {
        if AuthService.shared.isLoggedIn {
            isAuthenticated = true
            Task { await fetchProfile() }
        }
    }

    func updateServerURL() {
        KeychainService.saveServerURL(serverURL)
    }

    func login(email: String, password: String) async {
        isLoading = true
        errorMessage = nil
        do {
            currentUser = try await AuthService.shared.login(email: email, password: password)
            isAuthenticated = true
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func register(email: String, username: String, password: String,
                  firstName: String, lastName: String) async {
        isLoading = true
        errorMessage = nil
        do {
            currentUser = try await AuthService.shared.register(
                email: email, username: username, password: password,
                firstName: firstName, lastName: lastName
            )
            isAuthenticated = true
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func fetchProfile() async {
        do {
            currentUser = try await AuthService.shared.fetchProfile()
        } catch {
            logout()
        }
    }

    func logout() {
        AuthService.shared.logout()
        currentUser = nil
        isAuthenticated = false
    }
}
```

#### `ViewModels/DocumentsViewModel.swift`

```swift
import Foundation

@MainActor
class DocumentsViewModel: ObservableObject {
    @Published var documents: [FDDocument] = []
    @Published var sharedDocuments: [FDDocument] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var totalPages = 1
    @Published var currentPage = 1

    private let api = APIService.shared

    func loadDocuments(folderId: Int? = nil, search: String? = nil, page: Int = 1) async {
        isLoading = true
        errorMessage = nil
        var query: [String: String] = ["page": "\(page)"]
        if let folderId { query["folder_id"] = "\(folderId)" }
        if let search, !search.isEmpty { query["search"] = search }

        do {
            let response: DocumentsResponse = try await api.request(
                "GET", path: "/documents", query: query
            )
            documents = response.documents
            totalPages = response.pages ?? 1
            currentPage = response.page ?? 1
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadSharedDocuments() async {
        do {
            let response: DocumentsResponse = try await api.request(
                "GET", path: "/documents/shared"
            )
            sharedDocuments = response.documents
        } catch {}
    }

    func deleteDocument(id: Int) async -> Bool {
        do {
            let _: MessageResponse = try await api.request("DELETE", path: "/documents/\(id)")
            documents.removeAll { $0.id == id }
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }
}
```

#### `ViewModels/FoldersViewModel.swift`

```swift
import Foundation

@MainActor
class FoldersViewModel: ObservableObject {
    @Published var folders: [Folder] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIService.shared

    func loadFolders(parentId: Int? = nil) async {
        isLoading = true
        var query: [String: String] = [:]
        if let parentId { query["parent_id"] = "\(parentId)" }

        do {
            let response: FoldersResponse = try await api.request(
                "GET", path: "/folders", query: query
            )
            folders = response.folders
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func createFolder(name: String, description: String = "", category: String = "Autres",
                      parentId: Int? = nil) async -> Bool {
        var body: [String: Any] = ["name": name, "description": description, "category": category]
        if let parentId { body["parent_id"] = parentId }

        do {
            let response: SingleFolderResponse = try await api.request(
                "POST", path: "/folders", body: body
            )
            // Reload to get proper Folder type
            await loadFolders(parentId: parentId)
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }

    func deleteFolder(id: Int) async -> Bool {
        do {
            let _: MessageResponse = try await api.request("DELETE", path: "/folders/\(id)")
            folders.removeAll { $0.id == id }
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }
}
```

#### `ViewModels/TasksViewModel.swift`

```swift
import Foundation

@MainActor
class TasksViewModel: ObservableObject {
    @Published var tasks: [FDTask] = []
    @Published var overdueTasks: [FDTask] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIService.shared

    func loadTasks(status: String? = nil, priority: String? = nil) async {
        isLoading = true
        var query: [String: String] = [:]
        if let status { query["status"] = status }
        if let priority { query["priority"] = priority }

        do {
            let response: TasksResponse = try await api.request(
                "GET", path: "/tasks", query: query
            )
            tasks = response.tasks
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadOverdue() async {
        do {
            let response: TasksResponse = try await api.request("GET", path: "/tasks/overdue")
            overdueTasks = response.tasks
        } catch {}
    }

    func createTask(title: String, dueDate: String, description: String = "",
                    priority: String = "normal") async -> Bool {
        do {
            let _: SingleTaskResponse = try await api.request(
                "POST", path: "/tasks",
                body: ["title": title, "due_date": dueDate,
                       "description": description, "priority": priority]
            )
            await loadTasks()
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }

    func updateStatus(taskId: Int, status: String) async -> Bool {
        do {
            let _: SingleTaskResponse = try await api.request(
                "PUT", path: "/tasks/\(taskId)/status",
                body: ["status": status]
            )
            await loadTasks()
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }

    func deleteTask(id: Int) async -> Bool {
        do {
            let _: MessageResponse = try await api.request("DELETE", path: "/tasks/\(id)")
            tasks.removeAll { $0.id == id }
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }
}
```

#### `ViewModels/FamiliesViewModel.swift`

```swift
import Foundation

@MainActor
class FamiliesViewModel: ObservableObject {
    @Published var families: [Family] = []
    @Published var selectedFamily: FamilyDetail?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIService.shared

    func loadFamilies() async {
        isLoading = true
        do {
            let response: FamiliesResponse = try await api.request("GET", path: "/families")
            families = response.families
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadFamily(id: Int) async {
        do {
            let response: FamilyDetailResponse = try await api.request(
                "GET", path: "/families/\(id)"
            )
            selectedFamily = response.family
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func createFamily(name: String, description: String = "") async -> Bool {
        do {
            let _: SingleFamilyResponse = try await api.request(
                "POST", path: "/families",
                body: ["name": name, "description": description]
            )
            await loadFamilies()
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }

    func createInvite(familyId: Int, role: String = "lecteur",
                      expiresHours: Int = 24, maxUses: Int = 1) async -> InviteLink? {
        do {
            let response: InviteResponse = try await api.request(
                "POST", path: "/families/\(familyId)/invite",
                body: ["role": role, "expires_hours": expiresHours, "max_uses": maxUses]
            )
            return response.invite
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return nil
        }
    }

    func joinFamily(token: String) async -> Bool {
        do {
            let _: JoinFamilyResponse = try await api.request(
                "POST", path: "/families/join/\(token)"
            )
            await loadFamilies()
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }
}
```

#### `ViewModels/ChatViewModel.swift`

```swift
import Foundation

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isLoading = false
    @Published var hasMore = false
    @Published var errorMessage: String?

    private let api = APIService.shared
    let familyId: Int

    init(familyId: Int) {
        self.familyId = familyId
    }

    func loadMessages() async {
        isLoading = true
        do {
            let response: MessagesResponse = try await api.request(
                "GET", path: "/families/\(familyId)/messages",
                query: ["limit": "50"]
            )
            messages = response.messages
            hasMore = response.hasMore
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func loadMore() async {
        guard hasMore else { return }
        do {
            let response: MessagesResponse = try await api.request(
                "GET", path: "/families/\(familyId)/messages",
                query: ["offset": "\(messages.count)", "limit": "50"]
            )
            messages.insert(contentsOf: response.messages, at: 0)
            hasMore = response.hasMore
        } catch {}
    }

    func sendMessage(content: String, isAnnouncement: Bool = false) async -> Bool {
        do {
            let response: SingleMessageResponse = try await api.request(
                "POST", path: "/families/\(familyId)/messages",
                body: ["content": content, "is_announcement": isAnnouncement]
            )
            messages.append(response.message)
            return true
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
            return false
        }
    }
}
```

#### `ViewModels/NotificationsViewModel.swift`

```swift
import Foundation

@MainActor
class NotificationsViewModel: ObservableObject {
    @Published var notifications: [FDNotification] = []
    @Published var unreadCount = 0
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api = APIService.shared

    func loadNotifications(unreadOnly: Bool = false) async {
        isLoading = true
        var query: [String: String] = [:]
        if unreadOnly { query["unread"] = "1" }

        do {
            let response: NotificationsResponse = try await api.request(
                "GET", path: "/notifications", query: query
            )
            notifications = response.notifications
            unreadCount = response.unreadCount ?? 0
        } catch let error as APIError {
            errorMessage = error.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func fetchUnreadCount() async {
        do {
            let response: CountResponse = try await api.request(
                "GET", path: "/notifications/count"
            )
            unreadCount = response.count
        } catch {}
    }

    func markAsRead(id: Int) async {
        do {
            let _: MessageResponse = try await api.request(
                "POST", path: "/notifications/\(id)/read"
            )
            if let idx = notifications.firstIndex(where: { $0.id == id }) {
                await loadNotifications()
            }
            unreadCount = max(0, unreadCount - 1)
        } catch {}
    }

    func markAllAsRead() async {
        do {
            let _: MessageResponse = try await api.request(
                "POST", path: "/notifications/read-all"
            )
            await loadNotifications()
        } catch {}
    }
}
```

### 5.5 Views

#### `Views/ContentView.swift`

```swift
import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authVM: AuthViewModel

    var body: some View {
        Group {
            if authVM.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
    }
}
```

#### `Views/Auth/LoginView.swift`

```swift
import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                // Logo
                VStack(spacing: 8) {
                    Image(systemName: "lock.doc.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.blue)
                    Text("FamiliDocs")
                        .font(.largeTitle.bold())
                    Text("Coffre-fort familial")
                        .foregroundStyle(.secondary)
                }

                // Formulaire
                VStack(spacing: 16) {
                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                        .textFieldStyle(.roundedBorder)

                    SecureField("Mot de passe", text: $password)
                        .textContentType(.password)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                if let error = authVM.errorMessage {
                    Text(error)
                        .foregroundStyle(.red)
                        .font(.callout)
                }

                Button {
                    Task { await authVM.login(email: email, password: password) }
                } label: {
                    if authVM.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Se connecter")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal)
                .disabled(email.isEmpty || password.isEmpty || authVM.isLoading)

                Button("Creer un compte") { showRegister = true }

                Spacer()

                Button("Configurer le serveur") { showSettings = true }
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            .padding()
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
            .sheet(isPresented: $showSettings) {
                ServerSettingsView()
            }
        }
    }
}

struct ServerSettingsView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section("Adresse du serveur") {
                    TextField("URL de l'API", text: $authVM.serverURL)
                        .autocapitalization(.none)
                        .keyboardType(.URL)
                    Text("Exemple: http://192.168.1.42:5000/api")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Serveur")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("OK") {
                        authVM.updateServerURL()
                        dismiss()
                    }
                }
            }
        }
    }
}
```

#### `Views/Auth/RegisterView.swift`

```swift
import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @Environment(\.dismiss) var dismiss

    @State private var email = ""
    @State private var username = ""
    @State private var password = ""
    @State private var passwordConfirm = ""
    @State private var firstName = ""
    @State private var lastName = ""

    var isValid: Bool {
        !email.isEmpty && !username.isEmpty && !firstName.isEmpty &&
        !lastName.isEmpty && password.count >= 8 && password == passwordConfirm
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Identite") {
                    TextField("Prenom", text: $firstName)
                    TextField("Nom", text: $lastName)
                }
                Section("Compte") {
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    TextField("Nom d'utilisateur", text: $username)
                        .autocapitalization(.none)
                }
                Section("Mot de passe") {
                    SecureField("Mot de passe (min 8 car.)", text: $password)
                    SecureField("Confirmer", text: $passwordConfirm)
                    if !password.isEmpty && password != passwordConfirm {
                        Text("Les mots de passe ne correspondent pas")
                            .foregroundStyle(.red).font(.caption)
                    }
                }
                if let error = authVM.errorMessage {
                    Section { Text(error).foregroundStyle(.red) }
                }
            }
            .navigationTitle("Inscription")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Annuler") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Creer") {
                        Task {
                            await authVM.register(
                                email: email, username: username, password: password,
                                firstName: firstName, lastName: lastName
                            )
                            if authVM.isAuthenticated { dismiss() }
                        }
                    }
                    .disabled(!isValid || authVM.isLoading)
                }
            }
        }
    }
}
```

#### `Views/Main/MainTabView.swift`

```swift
import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var authVM: AuthViewModel
    @StateObject private var notifVM = NotificationsViewModel()

    var body: some View {
        TabView {
            DocumentsListView()
                .tabItem {
                    Label("Documents", systemImage: "doc.fill")
                }

            FoldersListView()
                .tabItem {
                    Label("Dossiers", systemImage: "folder.fill")
                }

            TasksListView()
                .tabItem {
                    Label("Taches", systemImage: "checklist")
                }

            FamiliesListView()
                .tabItem {
                    Label("Familles", systemImage: "person.3.fill")
                }

            NotificationsListView()
                .tabItem {
                    Label("Notifs", systemImage: "bell.fill")
                }
                .badge(notifVM.unreadCount)
        }
        .task {
            await notifVM.fetchUnreadCount()
        }
        .environmentObject(notifVM)
    }
}
```

#### `Views/Documents/DocumentsListView.swift`

```swift
import SwiftUI

struct DocumentsListView: View {
    @StateObject private var vm = DocumentsViewModel()
    @State private var searchText = ""
    @State private var showUpload = false

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.documents.isEmpty {
                    ProgressView("Chargement...")
                } else if vm.documents.isEmpty {
                    ContentUnavailableView(
                        "Aucun document",
                        systemImage: "doc.fill",
                        description: Text("Uploadez votre premier document")
                    )
                } else {
                    List {
                        ForEach(vm.documents) { doc in
                            NavigationLink(value: doc.id) {
                                DocumentRow(document: doc)
                            }
                        }
                        .onDelete { indexSet in
                            Task {
                                for idx in indexSet {
                                    await vm.deleteDocument(id: vm.documents[idx].id)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Documents")
            .navigationDestination(for: Int.self) { docId in
                DocumentDetailView(documentId: docId)
            }
            .searchable(text: $searchText, prompt: "Rechercher")
            .onChange(of: searchText) { _, newValue in
                Task { await vm.loadDocuments(search: newValue.isEmpty ? nil : newValue) }
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { showUpload = true } label: {
                        Image(systemName: "plus")
                    }
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    Menu {
                        Button("Deconnexion", role: .destructive) {
                            // Access authVM from environment
                        }
                    } label: {
                        Image(systemName: "person.circle")
                    }
                }
            }
            .sheet(isPresented: $showUpload) {
                DocumentUploadView {
                    Task { await vm.loadDocuments() }
                }
            }
            .refreshable { await vm.loadDocuments(search: searchText.isEmpty ? nil : searchText) }
            .task { await vm.loadDocuments() }
        }
    }
}

struct DocumentRow: View {
    let document: FDDocument

    var body: some View {
        HStack {
            Image(systemName: document.fileIcon)
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text(document.name)
                    .font(.headline)
                    .lineLimit(1)
                HStack {
                    Text(document.fileType?.uppercased() ?? "")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.blue.opacity(0.1))
                        .cornerRadius(4)
                    Text(document.fileSizeFormatted)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            if document.isExpired {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
            } else if document.isExpiringSoon {
                Image(systemName: "clock.fill")
                    .foregroundStyle(.orange)
            }
        }
        .padding(.vertical, 4)
    }
}
```

#### `Views/Documents/DocumentDetailView.swift`

```swift
import SwiftUI

struct DocumentDetailView: View {
    let documentId: Int
    @State private var document: FDDocument?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if let doc = document {
                List {
                    Section("Informations") {
                        LabeledContent("Nom", value: doc.name)
                        LabeledContent("Fichier", value: doc.originalFilename)
                        LabeledContent("Type", value: doc.fileType?.uppercased() ?? "—")
                        LabeledContent("Taille", value: doc.fileSizeFormatted)
                        LabeledContent("Confidentialite", value: doc.confidentiality)
                    }
                    if let desc = doc.description, !desc.isEmpty {
                        Section("Description") { Text(desc) }
                    }
                    if !doc.tags.isEmpty {
                        Section("Tags") {
                            FlowLayout(doc.tags) { tag in
                                Text(tag.name)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color.blue.opacity(0.1))
                                    .cornerRadius(8)
                            }
                        }
                    }
                    if let expiry = doc.expiryDate {
                        Section("Echeance") {
                            LabeledContent("Date d'expiration", value: expiry)
                            if doc.isExpired {
                                Label("Expire", systemImage: "exclamationmark.triangle.fill")
                                    .foregroundStyle(.red)
                            }
                        }
                    }
                    Section {
                        Button {
                            Task { await downloadDocument(doc) }
                        } label: {
                            Label("Telecharger", systemImage: "arrow.down.circle.fill")
                        }
                    }
                }
                .navigationTitle(doc.name)
            } else if let error = errorMessage {
                ContentUnavailableView("Erreur", systemImage: "exclamationmark.triangle", description: Text(error))
            }
        }
        .task { await loadDocument() }
    }

    private func loadDocument() async {
        do {
            let response: SingleDocumentResponse = try await APIService.shared.request(
                "GET", path: "/documents/\(documentId)"
            )
            document = response.document
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func downloadDocument(_ doc: FDDocument) async {
        do {
            let (data, filename) = try await APIService.shared.downloadFile(
                path: "/documents/\(doc.id)/download"
            )
            // Sauvegarder dans les fichiers temporaires et ouvrir le share sheet
            let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(filename)
            try data.write(to: tempURL)
            await MainActor.run {
                let activityVC = UIActivityViewController(activityItems: [tempURL], applicationActivities: nil)
                if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                   let rootVC = windowScene.windows.first?.rootViewController {
                    rootVC.present(activityVC, animated: true)
                }
            }
        } catch {}
    }
}

// Simple flow layout helper
struct FlowLayout<Data: RandomAccessCollection, Content: View>: View where Data.Element: Identifiable {
    let data: Data
    let content: (Data.Element) -> Content

    init(_ data: Data, @ViewBuilder content: @escaping (Data.Element) -> Content) {
        self.data = data
        self.content = content
    }

    var body: some View {
        HStack(spacing: 8) {
            ForEach(data) { item in
                content(item)
            }
        }
    }
}
```

#### `Views/Documents/DocumentUploadView.swift`

```swift
import SwiftUI
import PhotosUI

struct DocumentUploadView: View {
    @Environment(\.dismiss) var dismiss
    let onUpload: () -> Void

    @State private var name = ""
    @State private var description = ""
    @State private var confidentiality = "private"
    @State private var selectedItem: PhotosPickerItem?
    @State private var fileData: Data?
    @State private var fileName = ""
    @State private var isUploading = false
    @State private var showFilePicker = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Fichier") {
                    Button("Choisir un fichier") { showFilePicker = true }
                    if !fileName.isEmpty {
                        LabeledContent("Fichier", value: fileName)
                    }
                }
                Section("Informations") {
                    TextField("Nom du document", text: $name)
                    TextField("Description (optionnel)", text: $description)
                    Picker("Confidentialite", selection: $confidentiality) {
                        Text("Prive").tag("private")
                        Text("Public").tag("public")
                        Text("Restreint").tag("restricted")
                    }
                }
                if let error = errorMessage {
                    Section { Text(error).foregroundStyle(.red) }
                }
            }
            .navigationTitle("Upload")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Annuler") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Envoyer") {
                        Task { await upload() }
                    }
                    .disabled(fileData == nil || name.isEmpty || isUploading)
                }
            }
            .fileImporter(isPresented: $showFilePicker,
                          allowedContentTypes: [.pdf, .png, .jpeg, .plainText, .data]) { result in
                switch result {
                case .success(let url):
                    guard url.startAccessingSecurityScopedResource() else { return }
                    defer { url.stopAccessingSecurityScopedResource() }
                    fileData = try? Data(contentsOf: url)
                    fileName = url.lastPathComponent
                    if name.isEmpty { name = url.deletingPathExtension().lastPathComponent }
                case .failure(let error):
                    errorMessage = error.localizedDescription
                }
            }
        }
    }

    private func upload() async {
        guard let fileData else { return }
        isUploading = true
        errorMessage = nil

        let ext = (fileName as NSString).pathExtension.lowercased()
        let mimeType: String
        switch ext {
        case "pdf": mimeType = "application/pdf"
        case "png": mimeType = "image/png"
        case "jpg", "jpeg": mimeType = "image/jpeg"
        case "gif": mimeType = "image/gif"
        case "txt": mimeType = "text/plain"
        default: mimeType = "application/octet-stream"
        }

        do {
            let _: SingleDocumentResponse = try await APIService.shared.uploadFile(
                path: "/documents",
                fileData: fileData,
                fileName: fileName,
                mimeType: mimeType,
                fields: [
                    "name": name,
                    "description": description,
                    "confidentiality": confidentiality
                ]
            )
            onUpload()
            dismiss()
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
        isUploading = false
    }
}
```

#### `Views/Folders/FoldersListView.swift`

```swift
import SwiftUI

struct FoldersListView: View {
    @StateObject private var vm = FoldersViewModel()
    @State private var showCreate = false
    @State private var newFolderName = ""
    @State private var newFolderCategory = "Autres"

    let categories = ["Administratif", "Sante", "Banque", "Logement", "Autres"]

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.folders.isEmpty {
                    ProgressView("Chargement...")
                } else if vm.folders.isEmpty {
                    ContentUnavailableView("Aucun dossier", systemImage: "folder.fill")
                } else {
                    List {
                        ForEach(vm.folders) { folder in
                            NavigationLink(value: folder.id) {
                                HStack {
                                    Image(systemName: folder.categoryIcon)
                                        .font(.title2)
                                        .foregroundStyle(.blue)
                                        .frame(width: 40)
                                    VStack(alignment: .leading) {
                                        Text(folder.name).font(.headline)
                                        Text("\(folder.documentCount) doc(s)")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                        .onDelete { indexSet in
                            Task {
                                for idx in indexSet {
                                    await vm.deleteFolder(id: vm.folders[idx].id)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Dossiers")
            .navigationDestination(for: Int.self) { folderId in
                FolderDetailView(folderId: folderId)
            }
            .toolbar {
                Button { showCreate = true } label: { Image(systemName: "plus") }
            }
            .alert("Nouveau dossier", isPresented: $showCreate) {
                TextField("Nom", text: $newFolderName)
                Button("Annuler", role: .cancel) { newFolderName = "" }
                Button("Creer") {
                    Task {
                        await vm.createFolder(name: newFolderName, category: newFolderCategory)
                        newFolderName = ""
                    }
                }
            }
            .refreshable { await vm.loadFolders() }
            .task { await vm.loadFolders() }
        }
    }
}

struct FolderDetailView: View {
    let folderId: Int
    @State private var folder: FolderDetail?
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if let folder {
                List {
                    if let subfolders = folder.subfolders, !subfolders.isEmpty {
                        Section("Sous-dossiers") {
                            ForEach(subfolders) { sf in
                                Label(sf.name, systemImage: "folder.fill")
                            }
                        }
                    }
                    if let docs = folder.documents, !docs.isEmpty {
                        Section("Documents") {
                            ForEach(docs) { doc in
                                DocumentRow(document: doc)
                            }
                        }
                    }
                    if folder.documents?.isEmpty ?? true && folder.subfolders?.isEmpty ?? true {
                        ContentUnavailableView("Dossier vide", systemImage: "folder")
                    }
                }
                .navigationTitle(folder.name)
            }
        }
        .task {
            do {
                let response: SingleFolderResponse = try await APIService.shared.request(
                    "GET", path: "/folders/\(folderId)"
                )
                folder = response.folder
            } catch {}
            isLoading = false
        }
    }
}
```

#### `Views/Tasks/TasksListView.swift`

```swift
import SwiftUI

struct TasksListView: View {
    @StateObject private var vm = TasksViewModel()
    @State private var showCreate = false
    @State private var statusFilter: String?

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.tasks.isEmpty {
                    ProgressView("Chargement...")
                } else if vm.tasks.isEmpty {
                    ContentUnavailableView("Aucune tache", systemImage: "checklist")
                } else {
                    List {
                        if !vm.overdueTasks.isEmpty {
                            Section("En retard") {
                                ForEach(vm.overdueTasks) { task in
                                    NavigationLink(value: task.id) { TaskRow(task: task) }
                                }
                            }
                        }
                        Section("Toutes les taches") {
                            ForEach(vm.tasks) { task in
                                NavigationLink(value: task.id) { TaskRow(task: task) }
                            }
                            .onDelete { indexSet in
                                Task {
                                    for idx in indexSet {
                                        await vm.deleteTask(id: vm.tasks[idx].id)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Taches")
            .navigationDestination(for: Int.self) { taskId in
                TaskDetailView(taskId: taskId)
            }
            .toolbar {
                Button { showCreate = true } label: { Image(systemName: "plus") }
            }
            .sheet(isPresented: $showCreate) {
                TaskFormView { Task { await vm.loadTasks(); await vm.loadOverdue() } }
            }
            .refreshable { await vm.loadTasks(); await vm.loadOverdue() }
            .task { await vm.loadTasks(); await vm.loadOverdue() }
        }
    }
}

struct TaskRow: View {
    let task: FDTask

    var body: some View {
        HStack {
            Circle()
                .fill(Color(task.priorityColor))
                .frame(width: 10, height: 10)

            VStack(alignment: .leading, spacing: 4) {
                Text(task.title)
                    .font(.headline)
                    .strikethrough(task.status == "completed")
                HStack {
                    Text(task.statusLabel)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(task.status == "completed" ? .green.opacity(0.2) : .gray.opacity(0.2))
                        .cornerRadius(4)
                    if let date = task.dueDateFormatted {
                        Text(date)
                            .font(.caption)
                            .foregroundStyle(task.isOverdue ? .red : .secondary)
                    }
                }
            }
        }
        .padding(.vertical, 2)
    }
}
```

#### `Views/Tasks/TaskDetailView.swift`

```swift
import SwiftUI

struct TaskDetailView: View {
    let taskId: Int
    @State private var task: FDTask?
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if let task {
                List {
                    Section("Details") {
                        LabeledContent("Titre", value: task.title)
                        LabeledContent("Priorite", value: task.priority)
                        LabeledContent("Statut", value: task.statusLabel)
                        if let date = task.dueDateFormatted {
                            LabeledContent("Echeance", value: date)
                        }
                        if let assigned = task.assignedToName {
                            LabeledContent("Assigne a", value: assigned)
                        }
                    }
                    if let desc = task.description, !desc.isEmpty {
                        Section("Description") { Text(desc) }
                    }
                    Section("Actions") {
                        if task.status != "completed" {
                            Button {
                                Task { await updateStatus("completed") }
                            } label: {
                                Label("Marquer comme termine", systemImage: "checkmark.circle.fill")
                            }
                        }
                        if task.status == "pending" {
                            Button {
                                Task { await updateStatus("in_progress") }
                            } label: {
                                Label("Demarrer", systemImage: "play.circle.fill")
                            }
                        }
                    }
                }
                .navigationTitle(task.title)
            }
        }
        .task { await loadTask() }
    }

    private func loadTask() async {
        do {
            let response: SingleTaskResponse = try await APIService.shared.request(
                "GET", path: "/tasks/\(taskId)"
            )
            task = response.task
        } catch {}
        isLoading = false
    }

    private func updateStatus(_ status: String) async {
        do {
            let response: SingleTaskResponse = try await APIService.shared.request(
                "PUT", path: "/tasks/\(taskId)/status", body: ["status": status]
            )
            task = response.task
        } catch {}
    }
}
```

#### `Views/Tasks/TaskFormView.swift`

```swift
import SwiftUI

struct TaskFormView: View {
    @Environment(\.dismiss) var dismiss
    let onSave: () -> Void

    @State private var title = ""
    @State private var description = ""
    @State private var dueDate = Date()
    @State private var priority = "normal"
    @State private var isSubmitting = false
    @State private var errorMessage: String?

    let priorities = ["low", "normal", "high", "urgent"]
    let priorityLabels = ["low": "Basse", "normal": "Normale", "high": "Haute", "urgent": "Urgente"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Tache") {
                    TextField("Titre", text: $title)
                    TextField("Description (optionnel)", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }
                Section("Parametres") {
                    DatePicker("Echeance", selection: $dueDate, displayedComponents: .date)
                    Picker("Priorite", selection: $priority) {
                        ForEach(priorities, id: \.self) { p in
                            Text(priorityLabels[p] ?? p).tag(p)
                        }
                    }
                }
                if let error = errorMessage {
                    Section { Text(error).foregroundStyle(.red) }
                }
            }
            .navigationTitle("Nouvelle tache")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Annuler") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Creer") {
                        Task { await createTask() }
                    }
                    .disabled(title.isEmpty || isSubmitting)
                }
            }
        }
    }

    private func createTask() async {
        isSubmitting = true
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: dueDate)

        do {
            let _: SingleTaskResponse = try await APIService.shared.request(
                "POST", path: "/tasks",
                body: ["title": title, "due_date": dateString,
                       "description": description, "priority": priority]
            )
            onSave()
            dismiss()
        } catch {
            errorMessage = (error as? APIError)?.errorDescription ?? error.localizedDescription
        }
        isSubmitting = false
    }
}
```

#### `Views/Families/FamiliesListView.swift`

```swift
import SwiftUI

struct FamiliesListView: View {
    @StateObject private var vm = FamiliesViewModel()
    @State private var showCreate = false
    @State private var newFamilyName = ""
    @State private var showJoin = false
    @State private var inviteToken = ""

    var body: some View {
        NavigationStack {
            Group {
                if vm.isLoading && vm.families.isEmpty {
                    ProgressView("Chargement...")
                } else if vm.families.isEmpty {
                    ContentUnavailableView("Aucune famille", systemImage: "person.3.fill",
                        description: Text("Creez une famille ou rejoignez-en une"))
                } else {
                    List(vm.families) { family in
                        NavigationLink(value: family.id) {
                            VStack(alignment: .leading) {
                                Text(family.name).font(.headline)
                                HStack {
                                    Text("\(family.memberCount) membre(s)")
                                    if let role = family.myRole {
                                        Text("- \(role)")
                                    }
                                }
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Familles")
            .navigationDestination(for: Int.self) { familyId in
                FamilyDetailView(familyId: familyId, vm: vm)
            }
            .toolbar {
                Menu {
                    Button("Creer une famille") { showCreate = true }
                    Button("Rejoindre avec un code") { showJoin = true }
                } label: {
                    Image(systemName: "plus")
                }
            }
            .alert("Nouvelle famille", isPresented: $showCreate) {
                TextField("Nom de la famille", text: $newFamilyName)
                Button("Annuler", role: .cancel) { newFamilyName = "" }
                Button("Creer") {
                    Task { await vm.createFamily(name: newFamilyName); newFamilyName = "" }
                }
            }
            .alert("Rejoindre une famille", isPresented: $showJoin) {
                TextField("Code d'invitation", text: $inviteToken)
                Button("Annuler", role: .cancel) { inviteToken = "" }
                Button("Rejoindre") {
                    Task { await vm.joinFamily(token: inviteToken); inviteToken = "" }
                }
            }
            .refreshable { await vm.loadFamilies() }
            .task { await vm.loadFamilies() }
        }
    }
}
```

#### `Views/Families/FamilyDetailView.swift`

```swift
import SwiftUI

struct FamilyDetailView: View {
    let familyId: Int
    @ObservedObject var vm: FamiliesViewModel
    @State private var showInvite = false
    @State private var inviteLink: InviteLink?

    var body: some View {
        Group {
            if let family = vm.selectedFamily {
                List {
                    Section("Informations") {
                        LabeledContent("Nom", value: family.name)
                        if let desc = family.description, !desc.isEmpty {
                            LabeledContent("Description", value: desc)
                        }
                        LabeledContent("Membres", value: "\(family.memberCount)")
                        if let role = family.myRole {
                            LabeledContent("Mon role", value: role)
                        }
                    }

                    Section("Membres") {
                        ForEach(family.members) { member in
                            HStack {
                                Image(systemName: "person.circle.fill")
                                    .font(.title2)
                                    .foregroundStyle(.blue)
                                VStack(alignment: .leading) {
                                    Text(member.userName ?? "Inconnu").font(.headline)
                                    Text(member.roleLabel)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }

                    Section("Actions") {
                        NavigationLink {
                            ChatView(familyId: familyId)
                        } label: {
                            Label("Chat familial", systemImage: "bubble.left.and.bubble.right.fill")
                        }

                        if let role = family.myRole,
                           ["chef_famille", "admin", "parent", "gestionnaire"].contains(role) {
                            Button {
                                Task {
                                    inviteLink = await vm.createInvite(familyId: familyId)
                                    if inviteLink != nil { showInvite = true }
                                }
                            } label: {
                                Label("Generer une invitation", systemImage: "link.badge.plus")
                            }
                        }
                    }
                }
                .navigationTitle(family.name)
            } else {
                ProgressView()
            }
        }
        .alert("Lien d'invitation", isPresented: $showInvite) {
            Button("Copier") {
                if let token = inviteLink?.token {
                    UIPasteboard.general.string = token
                }
            }
            Button("OK", role: .cancel) {}
        } message: {
            if let link = inviteLink {
                Text("Token: \(link.token)\n\nPartagez ce code avec la personne a inviter.")
            }
        }
        .task { await vm.loadFamily(id: familyId) }
    }
}
```

#### `Views/Families/ChatView.swift`

```swift
import SwiftUI

struct ChatView: View {
    let familyId: Int
    @StateObject private var vm: ChatViewModel
    @EnvironmentObject var authVM: AuthViewModel
    @State private var messageText = ""

    init(familyId: Int) {
        self.familyId = familyId
        _vm = StateObject(wrappedValue: ChatViewModel(familyId: familyId))
    }

    var body: some View {
        VStack(spacing: 0) {
            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        if vm.hasMore {
                            Button("Charger plus") { Task { await vm.loadMore() } }
                                .font(.caption)
                        }
                        ForEach(vm.messages) { msg in
                            ChatBubble(
                                message: msg,
                                isMe: msg.senderId == authVM.currentUser?.id
                            )
                            .id(msg.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: vm.messages.count) { _, _ in
                    if let last = vm.messages.last {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }

            Divider()

            // Input
            HStack {
                TextField("Message...", text: $messageText, axis: .vertical)
                    .lineLimit(1...4)
                    .textFieldStyle(.roundedBorder)

                Button {
                    let text = messageText
                    messageText = ""
                    Task { await vm.sendMessage(content: text) }
                } label: {
                    Image(systemName: "paperplane.fill")
                }
                .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .padding()
        }
        .navigationTitle("Chat")
        .task { await vm.loadMessages() }
    }
}

struct ChatBubble: View {
    let message: ChatMessage
    let isMe: Bool

    var body: some View {
        HStack {
            if isMe { Spacer() }
            VStack(alignment: isMe ? .trailing : .leading, spacing: 4) {
                if !isMe {
                    Text(message.senderName ?? "")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Text(message.content)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(isMe ? Color.blue : Color(.systemGray5))
                    .foregroundStyle(isMe ? .white : .primary)
                    .cornerRadius(16)

                if message.isAnnouncement {
                    Label("Annonce", systemImage: "megaphone.fill")
                        .font(.caption2)
                        .foregroundStyle(.orange)
                }
            }
            if !isMe { Spacer() }
        }
    }
}
```

#### `Views/Notifications/NotificationsListView.swift`

```swift
import SwiftUI

struct NotificationsListView: View {
    @EnvironmentObject var notifVM: NotificationsViewModel

    var body: some View {
        NavigationStack {
            Group {
                if notifVM.isLoading && notifVM.notifications.isEmpty {
                    ProgressView("Chargement...")
                } else if notifVM.notifications.isEmpty {
                    ContentUnavailableView("Aucune notification", systemImage: "bell.slash.fill")
                } else {
                    List {
                        ForEach(notifVM.notifications) { notif in
                            HStack {
                                Image(systemName: notif.typeIcon)
                                    .foregroundStyle(notif.isRead ? .gray : .blue)
                                    .frame(width: 30)

                                VStack(alignment: .leading, spacing: 4) {
                                    Text(notif.title)
                                        .font(.headline)
                                        .foregroundStyle(notif.isRead ? .secondary : .primary)
                                    Text(notif.message)
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(2)
                                }
                            }
                            .swipeActions(edge: .trailing) {
                                if !notif.isRead {
                                    Button("Lu") { Task { await notifVM.markAsRead(id: notif.id) } }
                                        .tint(.blue)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Notifications")
            .toolbar {
                if !notifVM.notifications.isEmpty {
                    Button("Tout lire") {
                        Task { await notifVM.markAllAsRead() }
                    }
                }
            }
            .refreshable { await notifVM.loadNotifications() }
            .task { await notifVM.loadNotifications() }
        }
    }
}
```

---

## 6. Configuration Info.plist

Pour autoriser les connexions HTTP (non HTTPS) vers le serveur local, ajouter dans `Info.plist` :

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

Dans Xcode :
1. Cliquer sur le projet dans le navigateur
2. Onglet "Info"
3. Ajouter "App Transport Security Settings" > "Allows Local Networking" = YES

---

## 7. Deploiement sur iPhone

### 7.1 Avec un compte Apple gratuit

1. **Xcode > Settings > Accounts** : ajouter votre Apple ID
2. **Project > Signing & Capabilities** : selectionner votre "Personal Team"
3. Changer le **Bundle Identifier** en quelque chose d'unique (ex: `com.votrenom.familidocs`)
4. Brancher l'iPhone en USB
5. Sur l'iPhone : **Reglages > General > Gestion de l'appareil** > faire confiance au certificat developpeur
6. Selectionner l'iPhone comme destination dans Xcode
7. **Cmd+R** pour builder et lancer

### 7.2 Limitations du compte gratuit

- L'app expire apres **7 jours** (il faut re-deployer)
- Maximum **3 apps** simultanees
- Pas de notifications push
- Pas de publication sur l'App Store

### 7.3 Premiere utilisation

1. Lancer le serveur Flask sur le PC Windows (`flask run --host=0.0.0.0`)
2. Sur l'iPhone, ouvrir FamiliDocs
3. Aller dans "Configurer le serveur" sur l'ecran de login
4. Entrer `http://192.168.1.42:5000/api` (remplacer par l'IP reelle du PC)
5. Se connecter avec `admin@familidocs.local` / `Admin123!`

---

## Resume des correspondances API ↔ iOS

| Ecran iOS | Endpoint principal | ViewModel |
|-----------|-------------------|-----------|
| Login | POST /api/auth/login | AuthViewModel |
| Register | POST /api/auth/register | AuthViewModel |
| Documents | GET /api/documents | DocumentsViewModel |
| Detail document | GET /api/documents/:id | - (inline) |
| Upload | POST /api/documents (multipart) | - (inline) |
| Dossiers | GET /api/folders | FoldersViewModel |
| Detail dossier | GET /api/folders/:id | - (inline) |
| Taches | GET /api/tasks | TasksViewModel |
| Detail tache | GET /api/tasks/:id | - (inline) |
| Familles | GET /api/families | FamiliesViewModel |
| Detail famille | GET /api/families/:id | FamiliesViewModel |
| Chat | GET/POST /api/families/:id/messages | ChatViewModel |
| Notifications | GET /api/notifications | NotificationsViewModel |
