# Politique de sécurité - FamiliDocs

Document de référence pour les choix de sécurité du projet et leurs justifications.

La politique s'appuie sur le référentiel **DICT** (ANSSI / CNIL) qui évalue la sécurité
d'un système d'information selon **4 critères** :

- **D — Disponibilité** : le système et les données sont accessibles quand on en a besoin
- **I — Intégrité** : les données ne sont ni altérées ni détruites de manière non autorisée
- **C — Confidentialité** : seules les personnes autorisées peuvent accéder aux données
- **T — Traçabilité** : toutes les actions sont enregistrées et imputables à un acteur

> Variante : **DICP** — la lettre **P** (Preuve) remplace le **T** (Traçabilité).

L'analyse de risques associée est dans [`ANALYSE_RISQUES.md`](ANALYSE_RISQUES.md).
La synthèse des mesures par critère DICT est en section 12 de ce document.

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

## 10. Audit de securite

Un audit complet du projet a ete realise en suivant les referentiels **OWASP Top 10** et
les bonnes pratiques **ANSSI**. L'audit a couvert :

- **Failles applicatives classiques (OWASP)** : injection SQL, XSS, CSRF, path traversal,
  injection de chemin Zip-Slip dans la restauration des sauvegardes, IDOR (Insecure Direct
  Object References), enumeration d'utilisateurs
- **Authentification et sessions** : verification de la robustesse du hashage bcrypt,
  validation du rate limiting, contrôle de l'absence de fuite via les messages d'erreur,
  chiffrement TOTP de la 2FA
- **Configuration** : recherche de secrets en dur dans le code, validation des en-tetes
  HTTP de securite, verification que `.env` est bien dans `.gitignore`
- **Code mort et imports inutilises** : reduction de la surface d'attaque
- **Tests de securite** : verification de la couverture des cas critiques (CSRF token,
  controle d'acces aux ressources d'autres utilisateurs, RGPD)

**Resultats** : plusieurs ameliorations ont ete identifiees puis implementees, notamment :

- Retrait des identifiants de base de donnees en dur dans `app/config/config.py` (fallback
  remplace par une exception explicite si `DATABASE_URL` n'est pas definie)
- Uniformisation du message d'erreur de connexion ("Email ou mot de passe incorrect")
  pour empecher l'enumeration des comptes existants
- Validation au niveau modele du champ `role` de `FamilyMember` via `@validates('role')`
- Suppression de methodes mortes dans `EncryptionService`, `Log` et `BackupService`
- Documentation formelle de la politique de securite (ce document) et d'une analyse de
  risques inspiree de la methode EBIOS (`docs/ANALYSE_RISQUES.md`)

Toutes les remediations ont ete validees par les **307 tests automatises** existants et 8
nouveaux tests dedies a la securite (data minimization RGPD, retention logs, droit a
l'oubli en cascade, validation des roles).

---

## 11. Synthèse DICT des mesures de sécurité

Récapitulatif des contre-mesures classées par **critère DICT** qu'elles renforcent.

### D — Disponibilité

| Mesure | Localisation |
|---|---|
| Limite de taille à l'upload (16 Mo) | `app/config/config.py` |
| Rate limiting connexion (5 tentatives / 15 min) | `app/services/auth_service.py` |
| Sauvegardes ZIP régulières | `app/services/backup_service.py` |
| Code source versionné sur GitHub (recovery) | dépôt distant |
| Scheduler de nettoyage (logs, notifs, partages expirés) | `app/services/scheduler_service.py` |

### I — Intégrité

| Mesure | Localisation |
|---|---|
| Token CSRF Flask-WTF sur tous les formulaires | `app/__init__.py` |
| ORM SQLAlchemy (paramétrage anti-injection SQL) | tous les `models/` |
| Validation MIME et extension à l'upload | `app/services/document_service.py` |
| Validator `@validates('role')` sur `FamilyMember` | `app/models/family.py` |
| Cascade SQLAlchemy pour la cohérence référentielle | tous les `models/` |
| Protection anti Zip-Slip à la restauration | `app/services/backup_service.py` |

### C — Confidentialité

| Mesure | Localisation |
|---|---|
| Hachage bcrypt des mots de passe (coût 12 + sel) | `app/services/auth_service.py` |
| 2FA TOTP optionnelle (RFC 6238) | `app/routes/auth_routes.py` |
| Chiffrement AES Fernet des documents privés | `app/services/encryption_service.py` |
| Cookies HttpOnly + SameSite=Lax + Secure (prod) | `app/config/config.py` |
| HSTS en production | `app/__init__.py` |
| Content-Security-Policy restrictive | `app/__init__.py` |
| Anti-énumération sur le login (message uniforme) | `app/services/auth_service.py` |
| Permissions granulaires avec expiration | `app/services/permission_service.py` |
| Export RGPD sans hash mdp ni secret TOTP | `app/services/backup_service.py` |
| Path traversal protégé via `os.path.realpath()` | `app/services/document_service.py` |

### T — Traçabilité

| Mesure | Localisation |
|---|---|
| Journalisation de 27 types d'actions | `app/models/log.py` |
| IP + User-Agent + horodatage sur chaque log | `app/models/log.py` |
| Logs admin audités (`/admin/logs`) | `app/routes/admin_routes.py` |
| Rétention RGPD 180 jours configurable | `app/models/log.py:cleanup_old_logs` |
| Notification automatique des actions sensibles | `app/services/notification_service.py` |

---

## 12. Limitations connues

- Rate limiting en memoire (mono-instance)
- Cle de chiffrement sur disque (en prod : Vault/KMS recommande)
- CSP avec `unsafe-inline` (compromis pour Bootstrap inline)
- Pas de signature electronique des documents
