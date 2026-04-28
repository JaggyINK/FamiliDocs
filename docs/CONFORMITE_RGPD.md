# Conformite RGPD - FamiliDocs

Audit de la conformite au Reglement General sur la Protection des Donnees (RGPD,
reglement UE 2016/679 applicable depuis le 25 mai 2018).

---

## 1. Donnees personnelles collectees

| Donnee | Champ | Usage | Sensibilite |
|---|---|---|---|
| Email | `users.email` | Identifiant de connexion + contact | Personnelle |
| Nom d'utilisateur | `users.username` | Affichage public | Personnelle |
| Prenom | `users.first_name` | Affichage | Personnelle |
| Nom | `users.last_name` | Affichage | Personnelle |
| Mot de passe (hash) | `users.password_hash` | Authentification | Sensible (jamais en clair) |
| Photo de profil | `users.profile_photo` | Affichage | Personnelle |
| Titre familial | `users.family_title` | Affichage (Papa, Maman...) | Personnelle |
| Secret 2FA | `users.totp_secret` | Authentification | Sensible (jamais affiche) |
| Adresse IP | `logs.ip_address` | Audit / detection fraude | Personnelle |
| User-Agent | `logs.user_agent` | Audit | Quasi-identifiant |
| Documents uploades | `documents.*` + fichiers disque | Stockage prive | Variable selon contenu |
| Messages chat | `messages.content` | Communication familiale | Personnelle |

**Donnees non collectees** : pas de geolocalisation, pas de cookies tiers, pas de tracking
analytique, pas de telephone (sauf si l'utilisateur le met dans son profil).

---

## 2. Base legale (article 6 RGPD)

| Traitement | Base legale |
|---|---|
| Inscription / connexion | Execution du contrat (l'utilisateur s'inscrit volontairement) |
| Stockage des documents | Execution du contrat |
| Logs d'audit | Interet legitime (securite, detection de fraude) |
| Notifications | Execution du contrat |
| Sauvegarde | Interet legitime (continuite de service) |

Pas de consentement explicite recolte (l'usage du service implique l'acceptation des CGU,
qui doivent etre formalisees dans une version production).

---

## 3. Droits implementes (chapitre III RGPD)

### 3.1 Droit d'acces (art. 15)
**Implemente** : route `/profile/export-data` -> `BackupService.export_user_data()`.
Telecharge un JSON contenant toutes les donnees de l'utilisateur :
- Profil (sans le hash du mot de passe ni le secret TOTP)
- Liste des dossiers
- Liste des documents
- Liste des taches

### 3.2 Droit de rectification (art. 16)
**Implemente** : page Profil permet de modifier email, prenom, nom, titre familial.
Le changement de mot de passe se fait via une page dediee.

### 3.3 Droit a l'effacement / oubli (art. 17)
**Implemente** : suppression du compte via Profil > Mes donnees > Supprimer mon compte.
Cascade SQLAlchemy : supprime documents, dossiers, taches, logs, notifications, permissions.
Les fichiers physiques sur disque sont supprimes (cascade `DocumentService.delete_document`).

### 3.4 Droit a la portabilite (art. 20)
**Implemente** : meme route que l'acces (export JSON), format structure et lisible
machine.

### 3.5 Droit d'opposition (art. 21)
**Partiellement** : pas de tracking publicitaire ni de profilage automatise dans le
projet, donc peu de cas concrets. L'utilisateur peut neanmoins supprimer son compte.

### 3.6 Droit a la limitation (art. 18)
**Non implemente formellement** : pas de mecanisme "geler le compte sans le supprimer".
Le compte peut etre desactive (`is_active=false`) par un admin.

---

## 4. Duree de conservation

| Donnees | Duree | Justification |
|---|---|---|
| Compte utilisateur | Tant que l'utilisateur ne le supprime pas | Execution du contrat |
| Documents uploades | Idem | Execution du contrat |
| Logs d'audit | **180 jours** (configurable via `LOG_RETENTION_DAYS`) | RGPD : duree minimale necessaire |
| Notifications | 90 jours apres lecture, 30 jours sinon | Pertinence operationnelle |
| Liens de partage | Jusqu'a `expires_at` ou usage epuise | Pertinence operationnelle |
| Sauvegardes ZIP | A discretion de l'admin | Securite operationnelle |

Le nettoyage des logs est automatique via le scheduler (`SchedulerService` execute
`Log.cleanup_old_logs()` chaque jour a 02h).

---

## 5. Securite des donnees (art. 32)

### 5.1 Mesures techniques
- Mots de passe **haches** (bcrypt avec sel)
- Documents prives **chiffres** (AES via Fernet)
- Authentification **2FA** optionnelle (TOTP)
- **HTTPS** obligatoire en production (HSTS)
- 7 **en-tetes HTTP** de securite
- Protection **CSRF** sur tous les formulaires
- **Rate limiting** anti brute-force
- **Logs d'audit** de 27 types d'actions

### 5.2 Mesures organisationnelles
- Acces admin restreint (decorateur `@admin_required`)
- Roles familiaux hierarchiques (8 niveaux)
- Permissions granulaires sur les documents (4 droits)

---

## 6. Donnees a caractere sensible

Les documents stockes peuvent contenir des donnees sensibles (sante, finances, identite).
Mesures de protection :
- Confidentialite "private" -> chiffrement AES automatique
- Permissions granulaires temporelles (expiration max 90j)
- Audit complet (qui a vu/telecharge quoi et quand via `logs`)
- Suppression definitive a la suppression du document

L'utilisateur reste **responsable du contenu** qu'il uploade.

---

## 7. Sous-traitants

Aucun sous-traitant externe dans la version actuelle (PostgreSQL, fichiers, tout en local).
Si deploiement cloud (AWS, OVH, etc.), il faudrait verifier la conformite du sous-traitant
et signer un avenant de sous-traitance (article 28 RGPD).

---

## 8. Transferts hors UE

Aucun. Donnees hebergees localement.

---

## 9. Mineurs

L'application est concue pour un usage familial, donc des mineurs peuvent y avoir acces.
Mesures :
- Compte cree par un parent / responsable
- Role "enfant" dans la famille avec acces limite supervise
- Pas de fonctionnalite publique (pas de profil visible hors famille)

En production, prevoir une verification de l'age des inscrits (consentement parental
sous 15 ans en France).

---

## 10. DPO et contact

Pour un projet d'ecole, pas de DPO designe.
En production, designer un Delegue a la Protection des Donnees (DPO) si la structure
exploitante traite des donnees personnelles a grande echelle.

Contact technique pour exercer ses droits : prevoir une adresse type `dpo@familidocs.local`
dans la version production.

---

## 11. Registre des traitements (art. 30)

A formaliser en production. Doit contenir :
- Categories de personnes concernees
- Categories de donnees
- Finalites
- Destinataires (interne / externe)
- Duree de conservation
- Mesures de securite

---

## 12. Notification de violation (art. 33)

En cas de fuite de donnees personnelles :
- Notification a la CNIL **sous 72h** si risque eleve pour les personnes
- Information des personnes concernees si risque eleve pour leurs droits
- Procedure documentee dans `POLITIQUE_SECURITE.md` (point 8)

---

## 13. Limitations / pistes d'amelioration

- Pas de banniere de consentement aux cookies (mais aucun cookie tiers utilise)
- Pas de CGU formalisees ni de politique de confidentialite affichee
- Pas de DPO designe
- Pas de chiffrement de tous les documents (uniquement les prives, sur choix utilisateur)
- Pas de pseudonymisation systematique des logs apres expiration
