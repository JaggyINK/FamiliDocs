# Politique de securite - FamiliDocs

Document de reference pour les choix de securite du projet et leurs justifications.

---

## 1. Authentification

### Mot de passe
- **Hachage** : bcrypt 4.1 (cout par defaut : 12 rounds)
- **Sel** : aleatoire genere automatiquement par bcrypt a chaque hachage
- **Politique** : minimum 8 caracteres, 1 majuscule, 1 minuscule, 1 chiffre, 1 caractere
  special. Validee cote serveur (`AuthService.validate_password`) **et** cote client
  (indicateur visuel temps reel sur les pages d'inscription et de changement).

### Double authentification (2FA)
- **Standard** : TOTP (RFC 6238), code a 6 chiffres genere toutes les 30 secondes
- **Bibliotheque** : `pyotp 2.9`
- **Activation** : optionnelle, via Profil > Securite > Activer la 2FA. QR code scannable
  avec Google Authenticator, Authy, Microsoft Authenticator
- **Stockage** : le secret TOTP (32 caracteres) est stocke dans la colonne `users.totp_secret`

### Rate limiting
- **5 tentatives** echouees depuis la meme IP -> blocage **15 minutes**
- Stockage en memoire (limite : ne fonctionne qu'avec une seule instance, en multi-workers
  il faudrait Redis)
- Reinitialise apres une connexion reussie

### Sessions
- **Duree** : 2 heures (renouvelees a chaque action)
- **Cookies** :
  - `HttpOnly` : interdit l'acces JavaScript (protection XSS)
  - `SameSite=Lax` : limite l'envoi inter-sites (protection CSRF)
  - `Secure` : actif uniquement en production (HTTPS obligatoire)

### Anti-enumeration
Les messages d'erreur de connexion sont **identiques** que l'email existe ou non
(`"Email ou mot de passe incorrect"`), pour ne pas reveler quels comptes existent en BDD.

---

## 2. Autorisation

### Roles applicatifs (table `users`)
- `admin` : tous droits + gestion users / logs / sauvegardes
- `user` : utilisateur standard
- `trusted` : personne de confiance (droits etendus)

### Roles familiaux (table `family_members`)
8 roles hierarchiques avec validation au niveau modele (`@validates('role')`) :
`responsable > admin > parent > gestionnaire > enfant > editeur > lecteur > invite`.

### Permissions documents (table `permissions`)
4 droits granulaires par document :
- `can_view` : consultation
- `can_edit` : modification des metadonnees
- `can_download` : telechargement du fichier
- `can_share` : re-partage avec d'autres utilisateurs

Chaque permission a une `start_date` et une `end_date` optionnelle (max 90 jours).

### Decorateurs de protection
- `@login_required` : sur toutes les routes utilisateur
- `@admin_required` : sur les routes `/admin/*`
- Verification proprietaire + admin pour les operations sur ressource

---

## 3. Chiffrement des donnees

### Mots de passe
Hashes bcrypt, jamais stockes en clair, jamais affiches.

### Documents prives
- Confidentialite "private" -> chiffrement automatique a l'upload via `Fernet` (AES-128-CBC + HMAC-SHA256)
- Cle stockee dans `app/database/.encryption_key` (gitignore)
- Dechiffrement transparent au telechargement (en memoire pour `decrypt_to_memory`)

### Cles
- `SECRET_KEY` Flask : auto-generee dans `app/database/.secret_key` au premier lancement
- `ENCRYPTION_KEY` Fernet : auto-generee dans `app/database/.encryption_key`
- En production, ces deux cles **doivent** etre fournies via variables d'environnement
  (`ProductionConfig.init_app` raise une exception sinon)

---

## 4. En-tetes HTTP de securite

7 en-tetes envoyees sur chaque reponse via `_setup_security_headers()` :

| En-tete | Valeur | Role |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Empeche le MIME sniffing |
| `X-Frame-Options` | `SAMEORIGIN` | Bloque l'iframe (anti-clickjacking) |
| `X-XSS-Protection` | `1; mode=block` | Filtre XSS du navigateur |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limite la fuite de l'URL |
| `Cache-Control` | `no-cache, no-store, must-revalidate` | Pas de cache des pages sensibles |
| `Content-Security-Policy` | sources whitelistees | Limite les scripts/styles externes |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (prod) | Force HTTPS |

---

## 5. Validations a l'upload

- Extension dans la whitelist : `pdf, png, jpg, jpeg, doc, docx, txt, xls, xlsx, gif`
- Taille <= 16 Mo (`MAX_CONTENT_LENGTH`)
- MIME type valide
- Path traversal evite : `os.path.realpath()` + verification que le chemin reste dans
  `uploads/`

---

## 6. Journalisation

- **27 types d'actions** tracees (table `logs`)
- Chaque entree contient : `user_id`, `action`, `details`, `ip_address`, `user_agent`,
  `created_at`
- Les tentatives de connexion echouees sont logues **uniquement si l'email existe**
  (sinon ca permettrait d'enumerer les comptes via les logs)

### Retention RGPD
Les logs sont automatiquement supprimes apres **180 jours** (configurable via
`LOG_RETENTION_DAYS`). Cleanup execute au demarrage et chaque jour a 02h via le scheduler.

---

## 7. Sauvegardes

### Strategie
- Sauvegarde manuelle via le panneau admin (`/admin/backups`)
- Format : ZIP contenant `database.json` (export JSON via SQLAlchemy) +
  dossier `uploads/` + `metadata.json`
- Stockage : dossier `backups/` (gitignore)

### Restauration
- Test des sauvegardes avant restauration : verification `metadata.json`,
  protection anti Zip-Slip a l'extraction (verification que chaque chemin reste dans
  le dossier d'extraction)
- Sauvegarde de l'etat actuel avant restauration (`.before_restore`)

---

## 8. Procedure d'incident (simplifiee)

1. **Detection** : alerte (logs anormaux, plainte utilisateur, monitoring)
2. **Confinement** : desactivation des comptes concernes (`is_active=false`),
   revocation des sessions
3. **Investigation** : consultation des logs (`/admin/logs`), recherche par utilisateur
   et par type d'action
4. **Communication** : information des utilisateurs concernes (RGPD : sous 72h pour
   les fuites de donnees)
5. **Remediation** : correctif applique, redeploiement, tests
6. **Post-mortem** : analyse de la cause racine, mise a jour de la politique

---

## 9. Mises a jour et maintenance

- **Dependances** : versions epinglees dans `requirements.txt`. Verification reguliere
  des CVE via `pip-audit`
- **Base de donnees** : migrations gerees par Flask-Migrate (Alembic)
- **Tests automatises** : 307 tests qui doivent passer avant chaque deploiement

---

## 10. Limitations connues

- Rate limiting en memoire (mono-instance)
- Cle de chiffrement sur disque (en prod : Vault/KMS recommande)
- CSP avec `unsafe-inline` (compromis pour Bootstrap inline)
- Pas de signature electronique des documents
