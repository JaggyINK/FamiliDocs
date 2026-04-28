# Analyse des risques - FamiliDocs

Analyse simplifiée inspirée de la méthode **EBIOS Risk Manager** (ANSSI), adaptée
au contexte d'un projet d'école familial.

---

## 1. Contexte et périmètre

**Application** : FamiliDocs (web Flask + desktop CustomTkinter, BDD PostgreSQL partagée).
**Utilisateurs** : familles (5-10 personnes par famille en moyenne).
**Données critiques** : documents administratifs (factures, identités, santé, finances).
**Hébergement étudié** : local (WSL2 + PostgreSQL local).

---

## 2. Identification des actifs

### Actifs primaires (à protéger en priorité)
| Actif | Pourquoi c'est critique |
|---|---|
| **Documents privés** | Données personnelles voire sensibles (santé, finances) |
| **Mots de passe** | Accès complet au compte si compromis |
| **Comptes admin** | Accès total à toutes les données |
| **Sauvegardes** | Contiennent l'intégralité des données |
| **Clé de chiffrement** | Si volée, tous les documents privés sont déchiffrables |

### Actifs supports (techniques)
| Actif | Rôle |
|---|---|
| Serveur Flask | Héberge l'application web |
| PostgreSQL | Base de données principale |
| Disque uploads | Fichiers physiques |
| `.secret_key` Flask | Sessions utilisateur |
| `.encryption_key` Fernet | Déchiffrement des documents |

---

## 3. Menaces identifiées et contre-mesures

Pour chaque menace, le **vecteur** d'attaque possible et la **contre-mesure technique**
implémentée dans le code pour s'en protéger.

| # | Menace | Source | Vecteur | Contre-mesure implémentée |
|---|---|---|---|---|
| M1 | Vol d'identifiants | Externe | Phishing, brute force, fuite mot de passe | Hachage **bcrypt** (coût 12) + **2FA TOTP** optionnelle + **rate limiting** (5 tentatives / 15 min). Fichier : `auth_service.py` |
| M2 | Injection SQL | Externe | Champs de formulaire, paramètres URL | **ORM SQLAlchemy** : toutes les requêtes sont paramétrées automatiquement, aucun SQL en dur. Fichier : tous les `models/` |
| M3 | XSS (Cross-Site Scripting) | Externe | Champs de description, message, etc. | **Échappement automatique Jinja2** sur toutes les variables `{{ var }}` + **Content-Security-Policy** restrictive. Fichiers : `templates/` + `__init__.py` |
| M4 | CSRF | Externe | Site malveillant tiers | **Token CSRF** Flask-WTF unique par formulaire, vérifié à chaque POST. Fichier : `__init__.py` |
| M5 | Vol de session | Externe | Sniffing réseau, XSS | Cookies **HttpOnly + SameSite=Lax + Secure** en prod + **HSTS**. Fichier : `config.py` |
| M6 | Path traversal | Externe | URL de téléchargement manipulée | `os.path.realpath()` + vérification que le chemin reste dans `uploads/`. Fichier : `document_service.py:140-148` |
| M7 | Vol physique du disque | Externe / Insider | Accès physique au serveur | **Chiffrement AES (Fernet)** automatique des documents privés. Fichier : `encryption_service.py` |
| M8 | Ransomware | Externe | Compromission du serveur | **Sauvegardes ZIP** régulières + code source **versionné sur GitHub** (recovery possible) |
| M9 | Erreur admin | Insider | Suppression accidentelle, mauvaise configuration | **Logs admin** tracés (27 types d'actions) + sauvegarde avant chaque restauration (`.before_restore`). Fichiers : `log.py`, `backup_service.py` |
| M10 | Fuite via export RGPD | Insider | Compte compromis -> export complet | L'export **n'inclut pas** le hash du mot de passe ni le secret TOTP. Vérifié par le test `test_export_does_not_contain_password_hash`. Fichier : `backup_service.py:export_user_data` |
| M11 | Déni de service (DoS) | Externe | Trop de requêtes, upload massif | **Limite 16 Mo / fichier** + rate limiting connexion + en prod, Nginx avec `limit_req`. Fichiers : `config.py`, `auth_service.py` |
| M12 | Accès non autorisé via lien de partage | Externe / Insider | Token deviné ou intercepté | Token **64 caractères aléatoires** via `secrets.token_urlsafe(48)` + expiration max 90 j + nombre maximum d'utilisations + révocation. Fichier : `family.py:ShareLink` |
| M13 | Compromission de la clé de chiffrement | Externe / Insider | Accès au fichier `.encryption_key` | `.encryption_key` **gitignoré** + permissions OS restreintes + recommandation Vault/KMS pour la production. Fichier : `encryption_service.py` |
| M14 | Modification des logs | Insider (admin) | Effacement de traces | Audit RGPD des accès admin (à étendre avec un log immuable type append-only en V3). Fichier : `log.py` |

---

## 4. Vulnérabilités à améliorer

Aucune vulnérabilité critique n'est connue, mais plusieurs points peuvent être renforcés
pour un déploiement multi-familles ou public.

| # | Point à améliorer | Justification du report |
|---|---|---|
| V1 | Clé de chiffrement stockée dans un fichier sur disque | Pour le projet d'école, c'est suffisant et explicable. En production, il faudrait un coffre type **Vault / KMS / HSM**. |
| V2 | Rate limiting en mémoire (mono-instance) | Suffisant pour une famille (1 instance Flask). Pour la production multi-workers, utiliser **Redis** comme stockage partagé. |
| V3 | CSP avec `unsafe-inline` | Compromis pratique pour permettre les `style=""` Bootstrap. À durcir en extrayant les styles inline dans des fichiers CSS dédiés. |
| V4 | Pas de chiffrement du fichier ZIP de sauvegarde | Les **fichiers privés** des utilisateurs sont déjà chiffrés en AES sur le disque (`.enc`). Cependant le `database.json` inclus dans le ZIP de sauvegarde contient des métadonnées en clair (noms de documents, emails, dates). Acceptable tant que la sauvegarde reste sur le poste local ; à chiffrer si elle transite vers un stockage externe. |
| V5 | Pas de signature des sauvegardes | Acceptable à l'échelle famille. Pour l'intégrité multi-poste, utiliser **HMAC** ou une signature GPG. |
| V6 | Logs lisibles par l'admin | Inhérent au modèle. Pour un usage entreprise, séparer les logs d'accès et les logs métier, et tracer l'admin lui-même dans un journal d'audit dédié. |
| V7 | Pas de verrouillage du compte sur tentatives réussies suspectes | Le rate limiting actuel se base uniquement sur l'IP. Améliorations possibles : détection de changement de géolocalisation, blocage temporaire si nouveau pays inhabituel. |

---

## 5. Matrice probabilité × impact

Échelle :
- **Probabilité** : 1 (rare) → 5 (fréquent)
- **Impact** : 1 (mineur) → 5 (catastrophique)
- **Niveau de risque** : Probabilité × Impact

| # | Menace | Proba | Impact | Risque | Niveau |
|---|---|---|---|---|---|
| M1 | Vol identifiants | 4 | 4 | 16 | **Élevé** |
| M2 | Injection SQL | 1 | 5 | 5 | Moyen |
| M3 | XSS | 2 | 4 | 8 | Moyen |
| M4 | CSRF | 1 | 3 | 3 | Faible |
| M5 | Vol session | 2 | 4 | 8 | Moyen |
| M6 | Path traversal | 1 | 4 | 4 | Faible |
| M7 | Vol physique disque | 2 | 5 | 10 | Moyen |
| M8 | Ransomware | 1 | 5 | 5 | Moyen |
| M9 | Erreur admin | 3 | 3 | 9 | Moyen |
| M10 | Fuite via export | 2 | 5 | 10 | Moyen |
| M11 | DoS | 2 | 2 | 4 | Faible |
| M12 | Token de partage | 2 | 3 | 6 | Faible |
| M13 | Clé de chiffrement | 1 | 5 | 5 | Moyen |
| M14 | Modification logs | 1 | 4 | 4 | Faible |

### Bonus : la matrice sous forme d'un dictionnaire Python

Un **dictionnaire Python** (`dict`) est une structure de données **clé-valeur** : chaque
clé (ici l'identifiant de menace `M1`, `M2`...) renvoie vers un objet structuré
(probabilité, impact, etc.). Cette représentation a deux avantages :

1. **Manipulable par script** : on peut filtrer (`[m for m in RISK_MATRIX.values() if m['risque'] > 10]`),
   trier, ou exporter en JSON en une ligne.
2. **Sérialisable** : un `dict` Python s'exporte directement en JSON (`json.dumps`),
   ce qui permet de l'intégrer dans une API ou un dashboard.

```python
RISK_MATRIX = {
    'M1':  {'menace': 'Vol identifiants',         'proba': 4, 'impact': 4, 'risque': 16, 'niveau': 'eleve'},
    'M2':  {'menace': 'Injection SQL',            'proba': 1, 'impact': 5, 'risque':  5, 'niveau': 'moyen'},
    'M3':  {'menace': 'XSS',                      'proba': 2, 'impact': 4, 'risque':  8, 'niveau': 'moyen'},
    'M4':  {'menace': 'CSRF',                     'proba': 1, 'impact': 3, 'risque':  3, 'niveau': 'faible'},
    'M5':  {'menace': 'Vol session',              'proba': 2, 'impact': 4, 'risque':  8, 'niveau': 'moyen'},
    'M6':  {'menace': 'Path traversal',           'proba': 1, 'impact': 4, 'risque':  4, 'niveau': 'faible'},
    'M7':  {'menace': 'Vol physique disque',      'proba': 2, 'impact': 5, 'risque': 10, 'niveau': 'moyen'},
    'M8':  {'menace': 'Ransomware',               'proba': 1, 'impact': 5, 'risque':  5, 'niveau': 'moyen'},
    'M9':  {'menace': 'Erreur admin',             'proba': 3, 'impact': 3, 'risque':  9, 'niveau': 'moyen'},
    'M10': {'menace': 'Fuite via export RGPD',    'proba': 2, 'impact': 5, 'risque': 10, 'niveau': 'moyen'},
    'M11': {'menace': 'DoS',                      'proba': 2, 'impact': 2, 'risque':  4, 'niveau': 'faible'},
    'M12': {'menace': 'Token de partage devine',  'proba': 2, 'impact': 3, 'risque':  6, 'niveau': 'faible'},
    'M13': {'menace': 'Cle de chiffrement volee', 'proba': 1, 'impact': 5, 'risque':  5, 'niveau': 'moyen'},
    'M14': {'menace': 'Modification des logs',    'proba': 1, 'impact': 4, 'risque':  4, 'niveau': 'faible'},
}
```

Cette structure est immédiatement exploitable par un script de revue automatique ou
par un dashboard.

---

## 6. Risques résiduels acceptés (et pourquoi)

Certains risques ne sont pas remédiés au stade actuel : voici les justifications.

| Risque résiduel | Justification |
|---|---|
| **Rate limiting non distribué** | Le projet vise un **usage familial** (5 à 10 utilisateurs maximum). Une seule instance Flask suffit, donc partager le compteur entre instances n'a pas de sens ici. Si le projet évoluait vers du multi-tenant, on migrerait sur Redis. |
| **Clé de chiffrement sur disque** | C'est un **compromis pédagogique** assumé pour le projet d'école : utiliser un Vault ou un KMS demanderait une infrastructure cloud. La clé est dans `.encryption_key`, **gitignorée**, avec des permissions OS restreintes. C'est documenté clairement dans le code. |
| **CSP avec `unsafe-inline`** | Nécessaire pour Bootstrap qui injecte du `style=""` inline. Plutôt que de dégrader le visuel, je l'**accepte** et je me réserve l'amélioration pour la V3 (extraction des inline). |
| **Pas de tests E2E avec navigateur réel** | J'ai 25 tests d'**intégration** qui couvrent les workflows complets côté serveur (login → upload → partage). Pour des tests E2E avec navigateur, il faudrait Selenium ou Playwright, ce qui ajoute de la complexité et du temps d'exécution sans gain critique pour la qualité à cette échelle. |
| **Pas de monitoring d'erreurs (Sentry, etc.)** | Les logs Python sont suffisants pour un usage familial. Pour la production, j'intégrerais Sentry pour les erreurs et Prometheus + Grafana pour les métriques. |
| **Pas de duplication offsite des sauvegardes BDD** | **Le code source est versionné sur GitHub**, qui sert déjà de sauvegarde distante de tout l'historique du projet. Pour les **données utilisateur** en production, il faudrait coupler `BackupService.create_backup()` avec un envoi automatique vers un stockage externe (S3, rclone, etc.). Acceptable au stade actuel car les données vivent uniquement sur le poste local. |

---

## 7. Plan d'amélioration (par ordre de priorité)

1. **Chiffrement du ZIP de sauvegarde** (V4) — utile dès qu'il quitte le poste local
2. **Signature HMAC des sauvegardes** (V5) — détection d'altération
3. **Verrouillage temporaire sur connexions inhabituelles** (V7) — détection de changement de géolocalisation, blocage du compte le temps qu'un parent valide
4. **Migration de la clé de chiffrement vers Vault** (V1) — pour la production
5. **CSP sans `unsafe-inline`** (V3) — extraction des scripts/styles inline
6. **Tests de pénétration** — audit externe avant tout déploiement public
7. **Monitoring et alertes** — Sentry + Prometheus + Grafana
8. **Plan de continuité d'activité (PCA)** — redondance, basculement

---

## 8. Méthodologie

L'analyse de risques a été réalisée avec l'assistance de **Claude Code (Anthropic)**,
un outil d'analyse de code par IA, pour :

- Cartographier les actifs et identifier les menaces classiques (OWASP, ANSSI)
- Croiser les contre-mesures présentes dans le code avec la matrice
- Vérifier la cohérence entre la politique de sécurité (`POLITIQUE_SECURITE.md`) et
  les implémentations réelles dans le code

L'utilisation d'un assistant IA pour l'analyse de risques est une pratique en
émergence dans l'industrie (revue de code automatisée, scan de vulnérabilités).
Les résultats ont été revus et validés manuellement par le développeur. Voir
détail dans `docs/POLITIQUE_SECURITE.md` (section 10).

---

## 9. Conclusion

FamiliDocs présente un **niveau de sécurité solide pour son périmètre cible** (usage
familial restreint, hébergement local). Les **contre-mesures techniques** couvrent la
quasi-totalité des menaces classiques OWASP : injection SQL, XSS, CSRF, path traversal,
brute force, vol de session, fuite RGPD.

### Points forts
- **Défense en profondeur** : la sécurité est présente à chaque couche (vue, contrôleur,
  service, modèle, données)
- **Authentification robuste** : bcrypt + 2FA TOTP + rate limiting + anti-énumération
- **Chiffrement automatique** des documents marqués privés (AES Fernet)
- **Conformité RGPD** documentée, avec export et droit à l'oubli implémentés
- **307 tests automatisés** dont 25 dédiés à la sécurité et 17 au RGPD
- **Audit complet** réalisé et tracé dans `POLITIQUE_SECURITE.md` section 10

### Risques résiduels assumés
Le risque le plus élevé identifié (M1 : vol d'identifiants, niveau 16) est **largement
mitigé** par la combinaison bcrypt + 2FA + rate limiting + anti-énumération. Un attaquant
externe n'a pratiquement aucune chance d'obtenir un accès sans complicité interne.

### Pour aller plus loin
Le projet est **prêt pour un déploiement familial** dans son état actuel. Pour un
déploiement public ou multi-familles, les améliorations 1, 4, 5 et 7 du plan
ci-dessus sont prioritaires. Un audit de pénétration externe serait également
indispensable avant toute mise en production publique.

L'**approche Security by Design** adoptée dès le départ (architecture en couches,
patrons de protection, tests automatisés) facilite ces évolutions futures sans avoir
à refondre l'application.
