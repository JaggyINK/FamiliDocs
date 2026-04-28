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

## 3. Menaces identifiees

| # | Menace | Source | Vecteur |
|---|---|---|---|
| M1 | Vol d'identifiants | Externe (attaquant) | Phishing, brute force, fuite mot de passe |
| M2 | Injection SQL | Externe | Champs de formulaire, parametres URL |
| M3 | XSS (Cross-Site Scripting) | Externe | Champs de formulaire (description, message...) |
| M4 | CSRF | Externe | Site malveillant tiers |
| M5 | Vol de session | Externe | Sniffing reseau, XSS |
| M6 | Path traversal | Externe | URL de telechargement manipulee |
| M7 | Vol physique du disque | Externe / Insider | Acces physique au serveur |
| M8 | Ransomware | Externe | Compromission du serveur |
| M9 | Erreur admin | Insider | Suppression accidentelle, configuration erronee |
| M10 | Fuite de donnees via export RGPD | Insider | Compte compromis -> export complet |
| M11 | Denial of Service (DoS) | Externe | Trop de requetes, upload massif |
| M12 | Acces non autorise via lien de partage | Externe / Insider | Token devine ou intercepte |
| M13 | Compromission de la cle de chiffrement | Externe / Insider | Acces au fichier `.encryption_key` |
| M14 | Modification des logs | Insider (admin) | Effacement de traces |

---

## 4. Vulnerabilites actuelles

| # | Vulnerabilite | Etat |
|---|---|---|
| V1 | Cle de chiffrement sur disque | **Acceptee** (en prod : Vault/KMS) |
| V2 | Rate limiting en memoire (mono-instance) | **Acceptee** (suffisant pour usage familial) |
| V3 | CSP avec `unsafe-inline` | **Acceptee** (compromis pour Bootstrap inline) |
| V4 | Pas de chiffrement des sauvegardes ZIP | A corriger |
| V5 | Pas de signature/verification des sauvegardes | A corriger |
| V6 | Logs en clair (acces admin = lecture) | Acceptable, mais a journaliser separement les acces aux logs |
| V7 | Pas de verrouillage du compte apres N tentatives reussies (uniquement IP) | A ameliorer |

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

---

## 6. Mesures de securite mises en place

| Menace | Mesure | Localisation dans le code |
|---|---|---|
| M1 (vol identifiants) | bcrypt + 2FA TOTP + rate limiting | `auth_service.py` |
| M2 (injection SQL) | ORM SQLAlchemy (parametrage automatique) | tous les modeles |
| M3 (XSS) | Echappement Jinja2 + CSP | templates + `__init__.py` |
| M4 (CSRF) | Token Flask-WTF unique par formulaire | `__init__.py` |
| M5 (vol session) | HttpOnly + SameSite=Lax + Secure (prod) + HSTS | `config.py` + `__init__.py` |
| M6 (path traversal) | `os.path.realpath()` + verification | `document_service.py:140-148` |
| M7 (vol disque) | Chiffrement AES des documents prives | `encryption_service.py` |
| M9 (erreur admin) | Logs admin tracees + sauvegardes regulieres | `log.py` + `backup_service.py` |
| M10 (fuite export) | Pas d'export du hash mot de passe ni du secret TOTP | `backup_service.py:export_user_data` |
| M11 (DoS) | Limite 16 Mo / fichier, rate limiting | `config.py` + `auth_service.py` |
| M12 (token) | Tokens 64 caracteres aleatoires (`secrets.token_urlsafe`) + expiration | `family.py:ShareLink` |
| M13 (cle) | `.encryption_key` gitignore + perms OS | `encryption_service.py` |
| M14 (logs) | Audit RGPD des acces admin (a etendre) | `log.py` |

---

## 7. Risques residuels acceptes

| Risque | Justification |
|---|---|
| Rate limiting non distribue | Usage familial, mono-instance suffit |
| Cle de chiffrement sur disque | Compromis pedagogique, en prod = Vault/KMS |
| CSP unsafe-inline | Compromis pour Bootstrap, a durcir en V3 |
| Pas de tests E2E reels | Tests d'integration suffisants pour l'echelle |

---

## 8. Plan d'amelioration (ordre de priorite)

1. **Chiffrement des sauvegardes ZIP** (V4) - protection contre vol fichier de backup
2. **Signature des sauvegardes** (V5) - detection d'alteration
3. **Verrouillage compte apres tentatives reussies suspectes** (V7) - alerte si geo IP change
4. **Migration cle de chiffrement vers Vault** (V1) - production
5. **CSP sans unsafe-inline** (V3) - extraction des inline scripts/styles
6. **Tests de penetration** - audit externe avant deploiement public
7. **Monitoring et alertes** - Prometheus + Grafana ou equivalent
8. **Plan de continuite d'activite (PCA)** - redondance, basculement

---

## 9. Methodologie

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

## 10. Conclusion

Le projet presente un **niveau de securite raisonnable pour un usage familial restreint**.
Les risques eleves identifies (M1 : vol d'identifiants) sont **partiellement couverts**
par bcrypt + 2FA + rate limiting.

Pour un deploiement public ou multi-familles, les ameliorations 1, 4, 5 et 7 sont
prioritaires.
