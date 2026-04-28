# Analyse des risques - FamiliDocs

Analyse simplifiee inspiree de la methode **EBIOS Risk Manager** (ANSSI), adaptee
au contexte d'un projet d'ecole familial.

---

## 1. Contexte et perimetre

**Application** : FamiliDocs (web Flask + desktop CustomTkinter, BDD PostgreSQL partagee).
**Utilisateurs** : familles (5-10 personnes par famille en moyenne).
**Donnees critiques** : documents administratifs (factures, identites, sante, finances).
**Hebergement etudie** : local (WSL2 + PostgreSQL local).

---

## 2. Identification des actifs

### Actifs primaires (a proteger en priorite)
| Actif | Pourquoi c'est critique |
|---|---|
| **Documents prives** | Donnees personnelles voire sensibles (sante, finances) |
| **Mots de passe** | Acces complet au compte si compromis |
| **Comptes admin** | Acces total a toutes les donnees |
| **Sauvegardes** | Contiennent l'integralite des donnees |
| **Cle de chiffrement** | Si volee, tous les documents prives sont dechiffrables |

### Actifs supports (techniques)
| Actif | Role |
|---|---|
| Serveur Flask | Heberge l'application web |
| PostgreSQL | Base de donnees principale |
| Disque uploads | Fichiers physiques |
| .secret_key Flask | Sessions utilisateur |
| .encryption_key Fernet | Dechiffrement des documents |

---

## 3. Menaces identifiees et mesures de protection

Pour chaque menace, le **vecteur** d'attaque possible et la **mesure** que j'ai
implementee dans le code pour s'en proteger.

| # | Menace | Source | Vecteur | Comment je la contre (dans mon code) |
|---|---|---|---|---|
| M1 | Vol d'identifiants | Externe | Phishing, brute force, fuite mdp | Hachage **bcrypt** (cout 12) + **2FA TOTP** optionnelle + **rate limiting** (5 tentatives / 15 min). Fichier : `auth_service.py` |
| M2 | Injection SQL | Externe | Champs de formulaire, parametres URL | **ORM SQLAlchemy** : toutes les requetes sont parametrees automatiquement, pas de SQL en dur. Fichier : tous les `models/` |
| M3 | XSS (Cross-Site Scripting) | Externe | Champs de description, message, etc. | **Echappement automatique Jinja2** sur toutes les variables `{{ var }}` + **Content-Security-Policy** restrictive. Fichiers : `templates/` + `__init__.py` |
| M4 | CSRF | Externe | Site malveillant tiers | **Token CSRF** Flask-WTF unique par formulaire, verifie a chaque POST. Fichier : `__init__.py` |
| M5 | Vol de session | Externe | Sniffing reseau, XSS | Cookies **HttpOnly + SameSite=Lax + Secure** en prod + **HSTS**. Fichier : `config.py` |
| M6 | Path traversal | Externe | URL de telechargement manipulee | `os.path.realpath()` + verification que le chemin reste dans `uploads/`. Fichier : `document_service.py:140-148` |
| M7 | Vol physique du disque | Externe / Insider | Acces physique au serveur | **Chiffrement AES (Fernet)** automatique des documents prives. Fichier : `encryption_service.py` |
| M8 | Ransomware | Externe | Compromission du serveur | **Sauvegardes ZIP** regulieres + code source **versionne sur GitHub** (recovery possible) |
| M9 | Erreur admin | Insider | Suppression accidentelle, mauvaise config | **Logs admin** traces (27 types d'actions) + sauvegardes avant chaque restauration (`.before_restore`). Fichiers : `log.py`, `backup_service.py` |
| M10 | Fuite via export RGPD | Insider | Compte compromis -> export complet | L'export **n'inclut pas** le hash mot de passe ni le secret TOTP. Verifie par le test `test_export_does_not_contain_password_hash`. Fichier : `backup_service.py:export_user_data` |
| M11 | Denial of Service (DoS) | Externe | Trop de requetes, upload massif | **Limite 16 Mo / fichier** + rate limiting connexion + en prod, Nginx avec `limit_req`. Fichiers : `config.py`, `auth_service.py` |
| M12 | Acces non autorise via lien de partage | Externe / Insider | Token devine ou intercepte | Token **64 caracteres aleatoires** via `secrets.token_urlsafe(48)` + expiration max 90 j + nombre max d'utilisations + revocation. Fichier : `family.py:ShareLink` |
| M13 | Compromission de la cle de chiffrement | Externe / Insider | Acces au fichier `.encryption_key` | `.encryption_key` **gitignore** + permissions OS restreintes + recommandation Vault/KMS pour la prod. Fichier : `encryption_service.py` |
| M14 | Modification des logs | Insider (admin) | Effacement de traces | Audit RGPD des acces admin (a etendre avec un log immuable type append-only en V3). Fichier : `log.py` |

---

## 4. Vulnerabilites a ameliorer

Aucune vulnerabilite critique n'est connue, mais plusieurs points peuvent etre renforces
pour un deploiement multi-familles ou public.

| # | Point a ameliorer | Justification du report |
|---|---|---|
| V1 | Cle de chiffrement stockee dans un fichier sur disque | Pour le projet d'ecole, c'est suffisant et explicable. En prod, il faudrait un coffre type **Vault / KMS / HSM**. |
| V2 | Rate limiting en memoire (mono-instance) | Suffisant pour une famille (1 instance Flask). Pour la prod multi-workers, utiliser **Redis** comme stockage partage. |
| V3 | CSP avec `unsafe-inline` | Compromis pratique pour permettre les `style=""` Bootstrap. A durcir en extrayant les inline dans des fichiers CSS dedies. |
| V4 | Pas de chiffrement des sauvegardes ZIP | Acceptable car les ZIP restent sur le poste local (gitignore). En cas d'export hors poste, ajouter un chiffrement avant transfert. |
| V5 | Pas de signature des sauvegardes | Acceptable a l'echelle famille. Pour l'integrite multi-poste, utiliser **HMAC** ou signature GPG. |
| V6 | Logs lisibles par l'admin | Inherent au modele. Pour un usage entreprise, separer les logs d'acces et les logs metier, et tracer l'admin lui-meme dans un journal d'audit. |
| V7 | Pas de verrouillage du compte sur tentatives reussies suspectes | Le rate limiting actuel se base sur l'IP. Ameliorations possibles : detection geolocalisation, alerte par mail si nouveau pays. |

---

## 5. Matrice probabilite x impact

Echelle :
- **Probabilite** : 1 (rare) -> 5 (frequent)
- **Impact** : 1 (mineur) -> 5 (catastrophique)
- **Niveau de risque** : Probabilite x Impact

| # | Menace | Proba | Impact | Risque | Niveau |
|---|---|---|---|---|---|
| M1 | Vol identifiants | 4 | 4 | 16 | **Eleve** |
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
| M13 | Cle de chiffrement | 1 | 5 | 5 | Moyen |
| M14 | Modification logs | 1 | 4 | 4 | Faible |

### Bonus : la matrice sous forme de dictionnaire Python

A des fins de reutilisation programmatique (script de revision automatique, dashboard...),
la matrice peut s'exprimer naturellement en `dict` :

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

Avantages : tri, filtre, export JSON, integration dans un dashboard immediats.

---

## 6. Risques residuels acceptes (et pourquoi)

Certains risques ne sont pas remediés au stade actuel : les justifications.

| Risque residuel | Justification |
|---|---|
| **Rate limiting non distribue** | Le projet vise un **usage familial** (5 a 10 utilisateurs maximum). Une seule instance Flask suffit, donc partager le compteur entre instances n'a pas de sens ici. Si le projet evoluait vers du multi-tenant, on migrerait sur Redis. |
| **Cle de chiffrement sur disque** | C'est un **compromis pedagogique** assume pour le projet d'ecole : utiliser un Vault ou un KMS demanderait une infra cloud. La cle est dans `.encryption_key`, **gitignore**, avec des permissions OS restreintes. C'est documente clairement dans le code. |
| **CSP avec `unsafe-inline`** | Necessaire pour Bootstrap qui injecte du `style=""` inline. Plutot que de degrader le visuel, je l'**accepte** et je me reserve l'amelioration pour la V3 (extraction des inline). |
| **Pas de tests E2E avec navigateur reel** | J'ai 25 tests d'**integration** qui couvrent les workflows complets cote serveur (login -> upload -> partage). Pour des tests E2E avec navigateur, il faudrait Selenium ou Playwright, ce qui ajoute de la complexite et du temps d'execution sans gain critique pour la qualite a cette echelle. |
| **Pas de monitoring d'erreurs (Sentry, etc.)** | Les logs Python sont suffisants pour un usage familial. Pour la prod, j'integrerais Sentry pour les erreurs et Prometheus + Grafana pour les metriques. |
| **Pas de duplication offsite des sauvegardes BDD** | **Le code source est versionne sur GitHub**, qui sert deja de sauvegarde distante de tout l'historique du projet. Pour les **donnees utilisateur** en production, il faudrait coupler `BackupService.create_backup()` avec un envoi automatique vers un stockage externe (S3, rclone, etc.). Acceptable au stade actuel car les donnees vivent uniquement sur le poste local. |

---

## 7. Plan d'amelioration (par ordre de priorite)

1. **Chiffrement des sauvegardes ZIP** (V4) - protection si la sauvegarde quitte le poste
2. **Signature HMAC des sauvegardes** (V5) - detection d'alteration
3. **Verrouillage compte sur connexions suspectes** (V7) - geolocalisation + alerte mail
4. **Migration cle de chiffrement vers Vault** (V1) - pour la production
5. **CSP sans `unsafe-inline`** (V3) - extraction des inline scripts/styles
6. **Tests de penetration** - audit externe avant deploiement public
7. **Monitoring et alertes** - Sentry + Prometheus + Grafana
8. **Plan de continuite d'activite (PCA)** - redondance, basculement

---

## 8. Methodologie

L'analyse de risques a ete realisee avec l'assistance de **Claude Code (Anthropic)**,
un outil d'analyse de code par IA, pour :

- Cartographier les actifs et identifier les menaces classiques (OWASP, ANSSI)
- Cross-checker les mesures de securite presentes dans le code avec la matrice
- Verifier la coherence entre la politique de securite (`POLITIQUE_SECURITE.md`) et
  les implementations reelles dans le code

L'utilisation d'un assistant IA pour l'analyse de risques est une pratique en
emergence dans l'industrie (revue de code automatisee, scan de vulnerabilites).
Les resultats ont ete revus et valides manuellement par le developpeur. Voir
detail dans `docs/POLITIQUE_SECURITE.md` (section 10).

---

## 9. Conclusion

FamiliDocs presente un **niveau de securite solide pour son perimetre cible** (usage
familial restreint, hebergement local). Les **mesures de protection** couvrent la
quasi-totalite des menaces classiques OWASP : injection SQL, XSS, CSRF, path traversal,
brute force, vol de session, fuite RGPD.

### Points forts
- **Defense en profondeur** : la securite est presente a chaque couche (vue, controleur,
  service, modele, donnees)
- **Authentification robuste** : bcrypt + 2FA TOTP + rate limiting + anti-enumeration
- **Chiffrement automatique** des documents marques prives (AES Fernet)
- **Conformite RGPD** documentee, avec export et droit a l'oubli implementes
- **307 tests automatises** dont 25 dedies a la securite et 17 au RGPD
- **Audit complet** realise et trace dans `POLITIQUE_SECURITE.md` section 10

### Risques residuels assumes
Le risque le plus eleve identifie (M1 : vol d'identifiants, niveau 16) est **largement
mitige** par la combinaison bcrypt + 2FA + rate limiting + anti-enumeration. Un attaquant
externe n'a pratiquement aucune chance d'obtenir un acces sans complicite interne.

### Pour aller plus loin
Le projet est **pret pour un deploiement familial** dans son etat actuel. Pour un
deploiement public ou multi-familles, les ameliorations 1, 4, 5 et 7 du plan
ci-dessus sont prioritaires. Un audit de penetration externe serait egalement
indispensable avant toute mise en production publique.

L'**approche Security by Design** adoptee des le depart (architecture en couches,
patrons de protection, tests automatises) facilite ces evolutions futures sans avoir
a refondre l'application.
