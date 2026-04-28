# Manuel Utilisateur - FamiliDocs

**Version :** 2.3
**Public :** Utilisateurs finaux (responsables, parents, enfants, membres invites d'une famille)

---

## Table des matieres

1. [Presentation](#1-presentation)
2. [Premiers pas](#2-premiers-pas)
3. [Tableau de bord](#3-tableau-de-bord)
4. [Gestion des documents](#4-gestion-des-documents)
5. [Partage de documents](#5-partage-de-documents)
6. [Taches et rappels](#6-taches-et-rappels)
7. [Famille et collaboration](#7-famille-et-collaboration)
8. [Notifications](#8-notifications)
9. [Profil et confidentialite](#9-profil-et-confidentialite)
10. [Application bureau](#10-application-bureau)
11. [FAQ](#11-faq)
12. [Glossaire](#12-glossaire)

---

## 1. Presentation

FamiliDocs est un coffre-fort numerique familial qui permet de centraliser, organiser et partager les documents administratifs d'une famille (bulletins scolaires, factures, documents medicaux, attestations, etc.).

### Fonctionnalites principales

- Stockage securise (chiffrement AES pour documents confidentiels)
- Partage avec controle d'acces granulaire et expiration
- Organisation par dossiers, tags et recherche multi-criteres
- Gestion de taches partagees au sein d'une famille
- Messagerie familiale et notifications
- Application web + application bureau Windows

[CAPTURE: page d'accueil de l'application avec le logo et la presentation]

---

## 2. Premiers pas

### 2.1 Creation d'un compte

1. Cliquer sur "S'inscrire" en haut a droite de la page d'accueil
2. Remplir le formulaire :
   - Email (sera votre identifiant)
   - Nom d'utilisateur
   - Prenom et nom
   - Mot de passe (au moins 8 caracteres, avec majuscules/minuscules/chiffres)
3. Le compteur de force du mot de passe (rouge -> orange -> vert) indique la robustesse
4. Cliquer sur "Creer mon compte"

[CAPTURE: formulaire d'inscription avec compteur de force]

### 2.2 Connexion

1. Saisir email + mot de passe
2. Cliquer sur "Se connecter"
3. Si la double authentification est activee, saisir le code a 6 chiffres genere par votre application (Google Authenticator, Authy, etc.)

[CAPTURE: page de connexion + ecran 2FA]

### 2.3 Activation de la double authentification (2FA)

Recommandee pour proteger votre compte.

1. Aller dans "Profil" -> "Securite"
2. Cliquer sur "Activer la 2FA"
3. Scanner le QR code avec une application TOTP (Google Authenticator, Authy, Microsoft Authenticator)
4. Saisir le code a 6 chiffres pour valider
5. Conserver les codes de secours en lieu sur

[CAPTURE: page d'activation 2FA avec QR code]

### 2.4 Mot de passe oublie

(Fonctionnalite en cours d'implementation - pour l'instant contacter un administrateur)

---

## 3. Tableau de bord

Le tableau de bord est la page d'accueil apres connexion. Il affiche :

- Nombre de documents, dossiers, taches en cours
- Documents recemment ajoutes
- Taches a echeance proche
- Notifications non lues
- Acces rapides aux fonctionnalites principales

Les cartes statistiques sont **cliquables** pour acceder directement a la section concernee.

[CAPTURE: tableau de bord avec stats et raccourcis]

---

## 4. Gestion des documents

### 4.1 Uploader un document

1. Menu "Documents" -> "Ajouter un document"
2. Choisir le fichier (formats acceptes : PDF, JPG, PNG, DOCX, XLSX, TXT - 16 MB max)
3. Renseigner :
   - Nom du document
   - Description (optionnelle)
   - Dossier de destination
   - Tags (optionnels)
   - Date d'expiration (optionnelle, format `YYYY-MM-DD`)
   - Niveau de confidentialite : public / privé / **confidentiel** (declenche le chiffrement AES)
4. Cliquer sur "Uploader"

[CAPTURE: formulaire d'upload avec tous les champs]

### 4.2 Organisation par dossiers

Cinq dossiers par defaut sont crees a l'inscription :
- Administratif
- Sante
- Scolaire
- Finances
- Autre

Vous pouvez en creer d'autres via "Documents" -> "Mes dossiers" -> "Nouveau dossier".

[CAPTURE: vue des dossiers en grille]

### 4.3 Tags et recherche

- **Tags** : libelles colores assignables a plusieurs documents (ex : "urgent", "2026", "impot")
- **Recherche multi-criteres** : nom, type, dossier, tag, date, proprietaire
- **Recherche globale AJAX** : barre de recherche en haut, suggestions en temps reel

[CAPTURE: barre de recherche avec suggestions + page resultats]

### 4.4 Versionnement

Chaque modification d'un document cree une nouvelle version. Vous pouvez :
- Consulter l'historique
- Telecharger une version anterieure
- Restaurer une version precedente

[CAPTURE: historique des versions d'un document]

### 4.5 Telecharger / Visualiser

- "Telecharger" : enregistre le fichier sur votre poste
- "Voir" : ouvre une previsualisation directe (PDF, images)

Les documents confidentiels sont **dechiffres en memoire** au moment du telechargement.

---

## 5. Partage de documents

### 5.1 Partager avec un membre de la famille

1. Sur la page du document, cliquer sur "Partager"
2. Selectionner le membre destinataire dans la liste
3. Cocher les permissions accordees :
   - Consulter
   - Telecharger
   - Modifier
   - Re-partager
4. Definir une date d'expiration (max 90 jours)
5. Cliquer sur "Confirmer"

[CAPTURE: dialogue de partage avec checkboxes des permissions]

### 5.2 Partage par lien externe

1. Cliquer sur "Generer un lien de partage"
2. Definir une date d'expiration et un nombre maximum d'utilisations
3. Copier le lien genere (token unique)
4. L'envoyer par le canal de votre choix (email, message, etc.)

Le lien peut etre revoque a tout moment depuis "Mes partages".

[CAPTURE: generation de lien + page "Mes partages"]

### 5.3 Revoquer un partage

Section "Mes partages" -> bouton "Revoquer" sur la ligne concernee.

---

## 6. Taches et rappels

### 6.1 Creer une tache

1. Menu "Taches" -> "Nouvelle tache"
2. Renseigner :
   - Titre
   - Description
   - Date d'echeance
   - Priorite : basse / moyenne / haute / urgente
   - Statut : a faire / en cours / a verifier / terminee
   - Assignation (soi-meme ou un membre de la famille)
   - Document associe (optionnel)
3. Enregistrer

[CAPTURE: formulaire de creation de tache]

### 6.2 Vue calendrier

Menu "Taches" -> onglet "Calendrier" : visualisation mensuelle.

[CAPTURE: vue calendrier des taches]

### 6.3 Taches automatiques

Lorsqu'un document a une date d'expiration, une tache de rappel est automatiquement creee 30 jours avant.

---

## 7. Famille et collaboration

### 7.1 Creer une famille

1. Menu "Famille" -> "Creer une famille"
2. Saisir le nom (ex : "Famille Dupont")
3. Vous devenez automatiquement le **responsable** (role principal)

[CAPTURE: ecran creation de famille]

### 7.2 Inviter des membres

1. Sur la page de la famille -> "Inviter un membre"
2. Saisir l'email
3. Choisir le role :
   - **responsable** : tous droits, gere la famille (max 2 par famille)
   - **admin** : tous droits sauf supprimer la famille
   - **parent** : gere documents et taches, peut inviter
   - **gestionnaire** : gere les documents
   - **enfant** : acces a son espace personnel
   - **editeur** : peut modifier les documents partages
   - **lecteur** : consultation seule
   - **invite** : acces temporaire restreint
4. L'invitation est envoyee, le membre la voit dans ses notifications

[CAPTURE: dialogue d'invitation avec roles]

### 7.3 Messagerie familiale

Menu "Famille" -> onglet "Chat" : echanges en temps reel entre membres de la meme famille.

[CAPTURE: interface de chat]

### 7.4 Tableau de bord taches famille

Vue d'ensemble des taches de la famille avec :
- Statistiques par membre
- Progression
- Recommandations (taches en retard, reequilibrage de charge)

[CAPTURE: dashboard taches famille]

---

## 8. Notifications

L'icone cloche en haut a droite affiche le nombre de notifications non lues. 12 types de notifications sont gerees :

| Type | Declenche par |
|---|---|
| `task_due` | Tache dont l'echeance approche |
| `task_overdue` | Tache en retard |
| `task_assigned` | Tache assignee a vous |
| `document_expiry` | Document arrivant a expiration |
| `document_expired` | Document expire |
| `document_shared` | Document partage avec vous |
| `permission_granted` | Permission accordee |
| `permission_revoked` | Permission revoquee |
| `permission_expiring` | Permission proche de l'expiration |
| `system` | Message systeme |
| `backup_complete` | Sauvegarde reussie (admin) |
| `welcome` | Bienvenue (a l'inscription) |

Le rafraichissement est automatique via AJAX.

[CAPTURE: liste des notifications]

---

## 9. Profil et confidentialite

### 9.1 Modifier son profil

Menu "Profil" -> onglet "Informations" : email, nom, prenom, avatar, telephone.

[CAPTURE: formulaire profil]

### 9.2 Changer son mot de passe

Menu "Profil" -> onglet "Securite" -> "Changer mon mot de passe".

### 9.3 Conformite RGPD

Menu "Profil" -> onglet "Mes donnees" :

- **Exporter mes donnees** : telechargement d'un fichier JSON contenant toutes vos donnees personnelles (droit a la portabilite)
- **Supprimer mon compte** : suppression definitive de votre compte et de toutes vos donnees (droit a l'effacement)

Les logs sont conserves 180 jours puis supprimes automatiquement.

[CAPTURE: page RGPD avec les deux boutons]

---

## 10. Application bureau

### 10.1 Installation

Telecharger l'executable `FamiliDocs.exe` (Windows uniquement) genere via PyInstaller.

[CAPTURE: dossier d'installation]

### 10.2 Connexion

L'application bureau utilise la **meme base de donnees PostgreSQL** que l'application web. Vos donnees sont synchronisees.

[CAPTURE: ecran de connexion desktop]

### 10.3 Differences avec la version web

L'application bureau couvre les fonctionnalites principales :
- Gestion documents et dossiers
- Partages
- Taches
- Chat familial
- Administration (pour les admins)

La 2FA n'est pour l'instant disponible que sur la version web.

[CAPTURE: interface principale desktop]

---

## 11. FAQ

### J'ai oublie mon mot de passe, que faire ?
La reinitialisation par email est en cours d'implementation. En attendant, contactez un administrateur.

### Quelle taille maximale pour un document ?
16 MB par fichier.

### Mes documents sont-ils chiffres ?
Les documents marques "confidentiel" sont chiffres avec AES (Fernet). Les autres ne le sont pas (consultez la politique de securite si besoin).

### Combien de temps les documents partages restent-ils accessibles ?
La duree maximum d'un partage est de 90 jours. Vous pouvez fixer une duree plus courte.

### Puis-je revoquer un partage ?
Oui, a tout moment depuis "Mes partages".

### Comment changer mon mot de passe ?
Menu "Profil" -> "Securite" -> "Changer mon mot de passe".

### Comment supprimer mon compte ?
Menu "Profil" -> "Mes donnees" -> "Supprimer mon compte". Action definitive.

### L'application est-elle conforme RGPD ?
Oui : droit d'acces, rectification, effacement et portabilite implementes. Logs anonymises apres 180 jours.

### Mes documents sont-ils sauvegardes ?
Une sauvegarde automatique de la base de donnees est realisee quotidiennement (gere cote administrateur).

---

## 12. Glossaire

| Terme | Definition |
|---|---|
| **2FA / TOTP** | Double authentification par code temporel a 6 chiffres |
| **AES / Fernet** | Algorithme de chiffrement symetrique utilise pour les documents confidentiels |
| **bcrypt** | Algorithme de hashage utilise pour les mots de passe |
| **CSRF** | Protection contre les requetes inter-sites malveillantes |
| **RGPD** | Reglement General sur la Protection des Donnees (UE) |
| **Tag** | Libelle colore assignable a plusieurs documents pour les categoriser |
| **Token de partage** | Identifiant unique d'un lien de partage externe |
| **Versionnement** | Conservation de l'historique des modifications d'un document |

---

**Pour toute question complementaire, contacter votre administrateur famille ou consulter la documentation technique dans `/docs/`.**
