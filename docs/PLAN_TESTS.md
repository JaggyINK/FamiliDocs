# Plan de tests - FamiliDocs

**Outil** : pytest 7.4 + pytest-flask 1.3
**Base de tests** : SQLite en memoire (configuree via `TestingConfig`)
**Total** : 307 tests automatises repartis en 14 fichiers, 100% passent

---

## 1. Strategie globale (pyramide des tests)

```
       /\        Tests d'integration  (~30 tests)
      /  \       workflow complets : inscription -> upload -> partage
     /----\
    /      \     Tests de routes      (~40 tests)
   /        \    code HTTP, redirections, droits d'acces
  /----------\
 /            \  Tests unitaires      (~190 tests)
/______________\ modeles + services isoles
```

La majorite des tests sont **unitaires** (rapides, isoles), quelques **integrations** valident
les workflows critiques, et un peu de **securite + RGPD** verifient les regles transversales.

---

## 2. Repartition par fichier

| Fichier | Cible | Nb tests |
|---|---|---|
| `test_models.py` | 13 modeles SQLAlchemy : creation, contraintes, methodes | ~80 |
| `test_services.py` | 8 services metier : auth, document, notification, backup, permission, search | ~50 |
| `test_routes.py` | Routes HTTP : status codes, redirections, acces protege | ~40 |
| `test_integration.py` | Workflows complets de bout en bout | ~25 |
| `test_security.py` | CSRF, rate limiting, injection, contournement auth | ~25 |
| `test_documents.py` | CRUD documents detaille | ~20 |
| `test_versions.py` | Versionnement de documents | ~10 |
| `test_tags.py` | Tags + relation N:N documents-tags | ~10 |
| `test_families.py` | Familles : creation, membres, roles, exclusion | ~10 |
| `test_chat.py` | Chat familial : envoi, edition, suppression | ~6 |
| `test_share_links.py` | Liens de partage : creation, expiration, limite usages | ~7 |
| `test_admin.py` | Routes admin : CRUD users, logs, backup | ~5 |
| `test_encryption.py` | Chiffrement Fernet : round-trip, mauvaise cle | ~5 |
| `test_rgpd.py` | Export RGPD, retention logs, droit a l'oubli, validation roles | ~17 |

**conftest.py** fournit les fixtures partagees :
`app`, `client`, `test_user`, `admin_user`, `second_user`, `test_folder`,
`test_document`, `test_task`, `test_family`, `auth_client`, `admin_client`.

---

## 3. Categories de tests

### 3.1 Tests unitaires (modeles)
Validation des regles metier au niveau objet :
- Creation d'un User refuse un email deja pris
- `User.can_access_document()` retourne True pour le proprietaire
- `Document.is_expired` calcule correctement par rapport a la date du jour
- `FamilyMember.role` rejette une valeur hors de `ROLES`
- Cascade `User -> Document` : la suppression du user supprime ses docs

### 3.2 Tests unitaires (services)
Logique metier isolee :
- `AuthService.hash_password()` produit un hash bcrypt different a chaque appel (sel)
- `AuthService.authenticate()` bloque apres 5 tentatives ratees
- `EncryptionService.encrypt_file()` chiffre puis on peut dechiffrer
- `DocumentService.upload_document()` refuse une extension non autorisee
- `PermissionService.check_permission()` respecte les droits granulaires

### 3.3 Tests d'integration
Workflows complets HTTP :
- Inscription -> connexion -> upload -> partage -> notification recue
- Creation famille -> invitation -> acceptation -> chat
- Creation tache -> assignation -> notification -> completion
- Upload doc prive -> chiffrement auto -> telechargement -> dechiffrement transparent

### 3.4 Tests de securite
- Token CSRF requis sur tous les POST
- Path traversal sur `/documents/<id>/download` rejete (utilise `os.path.realpath`)
- Acces a `/admin/*` interdit aux utilisateurs non-admin (403)
- Sessions expirees redirigent vers /login
- Injection SQL evitee par l'ORM SQLAlchemy

### 3.5 Tests RGPD
- Export en JSON contient toutes les donnees de l'utilisateur
- Le hash du mot de passe et le secret TOTP **ne sont pas** dans l'export
- `Log.cleanup_old_logs()` supprime les entrees > 180 jours
- Suppression d'un user supprime en cascade ses documents et dossiers

---

## 4. Comment lancer les tests

```bash
# Tous les tests (mode verbose)
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=app -v

# Un fichier specifique
pytest tests/test_security.py -v

# Un test specifique
pytest tests/test_models.py::TestUser::test_create_user -v

# En mode rapide (arrete au premier echec)
pytest tests/ -x
```

Resultat attendu : `307 passed in ~75s`

---

## 5. Limitations connues

- **Pas de tests end-to-end (E2E) avec un vrai navigateur** : pas de Selenium ni Playwright.
  Compense par les tests d'integration qui couvrent les workflows complets cote serveur.
- **Pas de tests de charge** (k6, Locust) : le projet vise un usage familial (~10 utilisateurs max),
  la performance n'est pas un enjeu majeur.
- **Pas de tests de la version desktop** : `desktop_app.py` n'a pas de tests automatises
  (l'interface CustomTkinter rend l'automatisation complexe). Tests manuels uniquement.

---

## 6. Pistes d'amelioration

- Ajouter des tests E2E avec **Playwright** pour valider l'experience utilisateur reelle
- Mettre en place un **CI/CD GitHub Actions** qui lance les tests a chaque push
- Mesurer la couverture de code (`pytest-cov`) et viser > 80%
- Ajouter des tests de mutation (mutmut) pour evaluer la qualite des tests
