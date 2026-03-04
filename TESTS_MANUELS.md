# FamiliDocs - Checklist de Tests Manuels

## Instructions
- Cocher chaque test une fois effectue avec succes : `[x]`
- Noter les anomalies dans la colonne "Remarques"
- Tester avec au moins 2 comptes utilisateurs (1 admin + 1 utilisateur normal)

---

## 1. AUTHENTIFICATION

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 1.1 | Acceder a `/` sans etre connecte | Redirection vers `/login` | [ ] | |
| 1.2 | Login avec email + mot de passe corrects | Redirection vers le dashboard, message "Bienvenue" | [ ] | |
| 1.3 | Login avec mot de passe incorrect | Message "Email ou mot de passe incorrect", pas de detail sur quel champ | [ ] | |
| 1.4 | Login avec email inexistant | Meme message que 1.3 (pas d'enumeration) | [ ] | |
| 1.5 | Login avec champs vides | Message "Veuillez remplir tous les champs" | [ ] | |
| 1.6 | Inscription avec tous les champs valides | Compte cree, connexion auto, redirection dashboard | [ ] | |
| 1.7 | Inscription avec email deja utilise | Message d'erreur, pas de doublon | [ ] | |
| 1.8 | Inscription avec mots de passe differents | Message "Les mots de passe ne correspondent pas" | [ ] | |
| 1.9 | Inscription avec mot de passe < 8 caracteres | Erreur de validation | [ ] | |
| 1.10 | Deconnexion | Redirection vers login, message "deconnecte" | [ ] | |
| 1.11 | Acceder a une page protegee sans etre connecte | Redirection vers login avec message | [ ] | |
| 1.12 | Changement de mot de passe (`/change-password`) | Page s'affiche, ancien mdp demande, nouveau mdp valide | [ ] | |
| 1.13 | Changement mdp avec ancien mdp incorrect | Message d'erreur | [ ] | |
| 1.14 | Tester `/login?next=/tasks/` | Apres login, redirige vers `/tasks/` | [ ] | |
| 1.15 | Tester `/login?next=https://google.com` | Apres login, redirige vers le dashboard (PAS vers google) | [ ] | |
| 1.16 | Brute force : 5+ tentatives echouees | Blocage temporaire avec message | [ ] | |

---

## 2. DOCUMENTS

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 2.1 | Upload d'un fichier PDF | Document cree, visible dans la liste | [ ] | |
| 2.2 | Upload d'un fichier DOCX | Idem | [ ] | |
| 2.3 | Upload d'une image (JPG/PNG) | Idem | [ ] | |
| 2.4 | Upload d'un fichier interdit (.exe, .py) | Message "Type de fichier non autorise" | [ ] | |
| 2.5 | Upload d'un fichier > 16 Mo | Erreur de taille | [ ] | |
| 2.6 | Upload sans fichier selectionne | Message d'erreur | [ ] | |
| 2.7 | Telecharger un document uploade | Le fichier telecharge est identique a l'original | [ ] | |
| 2.8 | Upload doc "prive" (confidentiel) | Document chiffre (verifie `is_encrypted=True` dans la fiche) | [ ] | |
| 2.9 | Telecharger un doc chiffre | Le fichier telecharge est lisible (dechiffre correctement) | [ ] | |
| 2.10 | Modifier un document (nom, description) | Modifications sauvegardees | [ ] | |
| 2.11 | Supprimer un document | Document supprime de la liste et du disque | [ ] | |
| 2.12 | Voir les details d'un document | Page de detail avec infos completes | [ ] | |
| 2.13 | Definir une date d'echeance | Date affichee, alerte si proche | [ ] | |
| 2.14 | Document avec date de revision | Indicateur si revision necessaire | [ ] | |
| 2.15 | Marquer un document comme revise | Date de revision mise a jour | [ ] | |
| 2.16 | Selection en masse (cocher plusieurs docs) | Barre d'actions en masse apparait | [ ] | |
| 2.17 | Suppression en masse | Les documents selectionnes sont supprimes | [ ] | |
| 2.18 | Filtrer par type de fichier | Seuls les fichiers du type choisi apparaissent | [ ] | |
| 2.19 | Rechercher un document par nom | Resultats corrects | [ ] | |

---

## 3. DOSSIERS

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 3.1 | Creer un dossier | Dossier cree avec categorie | [ ] | |
| 3.2 | Renommer un dossier | Nom mis a jour | [ ] | |
| 3.3 | Supprimer un dossier vide | Dossier supprime | [ ] | |
| 3.4 | Supprimer un dossier avec documents | Les documents sont dissocies (pas supprimes) | [ ] | |
| 3.5 | Deplacer un document dans un dossier | Document visible dans le dossier | [ ] | |
| 3.6 | Partager un dossier avec un membre | Tous les docs du dossier partages | [ ] | |
| 3.7 | Voir le contenu d'un dossier | Liste des documents du dossier | [ ] | |

---

## 4. VERSIONING

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 4.1 | Uploader une nouvelle version d'un document | Version creee, compteur incremente | [ ] | |
| 4.2 | Voir l'historique des versions | Liste des versions avec dates | [ ] | |
| 4.3 | Telecharger une ancienne version | Fichier correct telecharge | [ ] | |

---

## 5. PARTAGE DE DOCUMENTS

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 5.1 | Partager un document avec un utilisateur | Permission creee, visible dans "Partages" | [ ] | |
| 5.2 | L'utilisateur destinataire voit le doc dans "Partages" | Document visible | [ ] | |
| 5.3 | Revoquer l'acces d'un utilisateur | Le document n'est plus visible pour lui | [ ] | |
| 5.4 | Generer un lien de partage securise | Lien genere avec token | [ ] | |
| 5.5 | Utiliser un lien de partage valide | Acces accorde au document | [ ] | |
| 5.6 | Utiliser un lien de partage expire | Message "lien expire" | [ ] | |
| 5.7 | Utiliser un lien de partage revoque | Message "lien invalide" | [ ] | |
| 5.8 | Partager avec droits lecture seule | Le destinataire ne peut pas modifier | [ ] | |
| 5.9 | Partager avec droits d'edition | Le destinataire peut modifier | [ ] | |
| 5.10 | Copier un lien de partage (bouton copier) | Lien copie dans le presse-papier, notification visible | [ ] | |

---

## 6. FAMILLES / GROUPES

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 6.1 | Creer un groupe familial | Groupe cree, createur = admin | [ ] | |
| 6.2 | Generer un lien d'invitation | Lien cree avec role et expiration | [ ] | |
| 6.3 | Accepter une invitation (utilisateur connecte) | Ajout au groupe avec le role prevu | [ ] | |
| 6.4 | Invitation avec utilisateur non connecte | Page choix login/register avec infos famille | [ ] | |
| 6.5 | S'inscrire via invitation | Compte cree + ajout auto au groupe | [ ] | |
| 6.6 | Invitation expiree | Message "lien expire" | [ ] | |
| 6.7 | Invitation max utilisations atteint | Message "limite atteinte" | [ ] | |
| 6.8 | Changer le role d'un membre (admin) | Role mis a jour | [ ] | |
| 6.9 | Un gestionnaire essaie de promouvoir en admin | Refuse avec message | [ ] | |
| 6.10 | Retirer un membre du groupe | Membre retire, ses acces revoques | [ ] | |
| 6.11 | Un gestionnaire retire un invite | Fonctionne | [ ] | |
| 6.12 | Un gestionnaire retire un editeur | Refuse avec message | [ ] | |
| 6.13 | Le createur essaie de quitter le groupe | Refuse avec message | [ ] | |
| 6.14 | Un membre quitte volontairement | Membre retire | [ ] | |
| 6.15 | Supprimer un groupe (createur) | Groupe supprime avec tous ses membres | [ ] | |
| 6.16 | Revoquer un lien d'invitation | Lien revoque, inutilisable | [ ] | |
| 6.17 | Limite de 2 chefs de famille | 3eme promotion en chef refuse | [ ] | |

---

## 7. TACHES

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 7.1 | Creer une tache avec titre + date | Tache creee | [ ] | |
| 7.2 | Creer une tache sans titre | Message "titre obligatoire" | [ ] | |
| 7.3 | Creer une tache sans date | Message "date obligatoire" | [ ] | |
| 7.4 | Lier une tache a un document | Lien affiche dans la fiche tache | [ ] | |
| 7.5 | Assigner une tache a un membre de famille | Notification envoyee a l'assigne | [ ] | |
| 7.6 | L'assigne voit la tache dans sa liste | Tache visible (pas seulement pour le owner) | [ ] | |
| 7.7 | L'assigne peut voir les details de la tache | Page de detail accessible | [ ] | |
| 7.8 | L'assigne peut changer le statut | Statut mis a jour | [ ] | |
| 7.9 | Modifier une tache | Modifications sauvegardees | [ ] | |
| 7.10 | Supprimer une tache | Tache supprimee | [ ] | |
| 7.11 | Changer le statut : pending -> in_progress | Statut mis a jour | [ ] | |
| 7.12 | Changer le statut : in_progress -> completed | Tache marquee terminee avec date | [ ] | |
| 7.13 | Annuler une tache | Statut "cancelled" | [ ] | |
| 7.14 | Tache en retard (date passee) | Indicateur "en retard" visible | [ ] | |
| 7.15 | Filtrer par statut (en attente, en cours, etc.) | Filtre fonctionne | [ ] | |
| 7.16 | Filtrer par priorite | Filtre fonctionne | [ ] | |
| 7.17 | Page taches en retard (`/tasks/overdue`) | Liste des taches en retard | [ ] | |
| 7.18 | Page taches a venir (`/tasks/upcoming`) | Liste des taches avec echeance proche | [ ] | |

---

## 8. CALENDRIER

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 8.1 | Acceder a `/tasks/calendar` | Calendrier affiche | [ ] | |
| 8.2 | Les taches apparaissent aux bonnes dates | Positionnement correct | [ ] | |
| 8.3 | Couleurs selon priorite/retard | Rouge=retard, Orange=urgent, Jaune=haute, Bleu=normal | [ ] | |
| 8.4 | Cliquer sur une tache dans le calendrier | Modal avec details + lien "Voir details" | [ ] | |
| 8.5 | Naviguer entre les mois | Navigation fluide | [ ] | |
| 8.6 | Vue semaine et vue liste | Changement de vue fonctionne | [ ] | |
| 8.7 | Calendrier en francais | Jours et mois en francais | [ ] | |

---

## 9. NOTIFICATIONS

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 9.1 | Notification a la creation de compte | Message de bienvenue | [ ] | |
| 9.2 | Notification quand un doc est partage avec moi | Notification recue | [ ] | |
| 9.3 | Notification quand une tache m'est assignee | Notification recue | [ ] | |
| 9.4 | Notification quand un membre rejoint ma famille | Notification recue | [ ] | |
| 9.5 | Badge compteur dans la sidebar | Nombre de notifs non lues affiche | [ ] | |
| 9.6 | Marquer une notification comme lue | Badge decremente | [ ] | |
| 9.7 | Marquer toutes comme lues | Badge disparait | [ ] | |
| 9.8 | Supprimer une notification | Notification supprimee | [ ] | |
| 9.9 | Rafraichissement auto du compteur (60s) | Le badge se met a jour sans recharger | [ ] | |

---

## 10. RECHERCHE

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 10.1 | Recherche rapide dans la sidebar (AJAX) | Resultats en temps reel sous le champ | [ ] | |
| 10.2 | Recherche avec moins de 2 caracteres | Pas de resultats (min 2 caracteres) | [ ] | |
| 10.3 | Recherche avancee (`/search`) | Page de recherche avec filtres | [ ] | |
| 10.4 | Recherche par nom de document | Resultats corrects | [ ] | |
| 10.5 | Recherche par tag | Documents associes au tag affiches | [ ] | |
| 10.6 | Raccourci Ctrl+K | Focus sur le champ de recherche | [ ] | |

---

## 11. TAGS

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 11.1 | Creer un tag | Tag cree | [ ] | |
| 11.2 | Associer un tag a un document | Tag visible sur le document | [ ] | |
| 11.3 | Retirer un tag d'un document | Tag retire | [ ] | |
| 11.4 | Liste des tags (`/tags`) | Tous les tags affiches | [ ] | |

---

## 12. PROFIL UTILISATEUR

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 12.1 | Voir mon profil | Infos affichees correctement | [ ] | |
| 12.2 | Modifier nom et prenom | Modifications sauvegardees | [ ] | |
| 12.3 | Upload d'un avatar (JPG/PNG) | Avatar affiche dans la sidebar et le profil | [ ] | |
| 12.4 | Avatar avec format invalide | Message d'erreur | [ ] | |
| 12.5 | Sidebar avec noms vides ou None | Initiales affichent "?" au lieu de crasher | [ ] | |

---

## 13. CHAT / MESSAGES

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 13.1 | Acceder au chat d'un groupe familial | Page de chat affichee | [ ] | |
| 13.2 | Envoyer un message | Message affiche dans le chat | [ ] | |
| 13.3 | Modifier un message (son propre message) | Message mis a jour | [ ] | |
| 13.4 | Supprimer un message | Message supprime | [ ] | |
| 13.5 | Envoyer une annonce (si autorise) | Annonce affichee differemment | [ ] | |

---

## 14. ADMINISTRATION

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 14.1 | Acceder au dashboard admin (compte admin) | Dashboard avec statistiques | [ ] | |
| 14.2 | Acceder au dashboard admin (compte normal) | Acces refuse / erreur 403 | [ ] | |
| 14.3 | Lister les utilisateurs | Liste complete | [ ] | |
| 14.4 | Creer un utilisateur (admin) | Utilisateur cree | [ ] | |
| 14.5 | Modifier un utilisateur | Modifications sauvegardees | [ ] | |
| 14.6 | Desactiver un utilisateur | Utilisateur ne peut plus se connecter | [ ] | |
| 14.7 | Reactiver un utilisateur | Utilisateur peut se connecter | [ ] | |
| 14.8 | Consulter les logs d'activite | Logs affiches avec actions et dates | [ ] | |
| 14.9 | Filtrer les logs par type d'action | Filtre fonctionne | [ ] | |

---

## 15. SAUVEGARDES

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 15.1 | Creer une sauvegarde (admin) | Fichier ZIP cree dans le dossier backups | [ ] | |
| 15.2 | Lister les sauvegardes | Liste avec date et taille | [ ] | |
| 15.3 | Telecharger une sauvegarde | Fichier ZIP telecharge | [ ] | |
| 15.4 | Restaurer une sauvegarde | Donnees restaurees correctement | [ ] | |
| 15.5 | Supprimer une sauvegarde | Fichier supprime | [ ] | |
| 15.6 | Export RGPD des donnees utilisateur | JSON avec toutes les donnees de l'utilisateur | [ ] | |

---

## 16. HISTORIQUE / ACTIVITE

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 16.1 | Page historique (`/activity`) | Liste des actions recentes | [ ] | |
| 16.2 | Actions loguees : upload, modif, suppression | Chaque action apparait dans l'historique | [ ] | |
| 16.3 | Actions loguees : login, logout | Connexions/deconnexions visibles | [ ] | |
| 16.4 | Detail d'un log | Informations completes | [ ] | |

---

## 17. SECURITE

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 17.1 | Soumettre un formulaire sans token CSRF | Erreur 400 (CSRF validation failed) | [ ] | |
| 17.2 | Acceder au document d'un autre utilisateur | Acces refuse | [ ] | |
| 17.3 | Modifier la tache d'un autre utilisateur | Acces refuse | [ ] | |
| 17.4 | Headers de securite presents (X-Frame-Options, etc.) | Verifier avec F12 > Network | [ ] | |
| 17.5 | Cookies HttpOnly et SameSite=Lax | Verifier avec F12 > Application > Cookies | [ ] | |
| 17.6 | Titre de tache avec `<script>alert('xss')</script>` | Script echappe, pas d'alerte | [ ] | |
| 17.7 | Open redirect bloque (`/login?next=//evil.com`) | Redirige vers dashboard, pas vers evil.com | [ ] | |

---

## 18. INTERFACE / UX

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 18.1 | Mode sombre (bouton lune/soleil) | Theme sombre active/desactive | [ ] | |
| 18.2 | Mode sombre persiste apres rechargement | Preference sauvegardee (localStorage) | [ ] | |
| 18.3 | Sidebar responsive (mobile) | Sidebar se cache, bouton hamburger visible | [ ] | |
| 18.4 | Sidebar toggle sur mobile | Sidebar s'ouvre/ferme au clic | [ ] | |
| 18.5 | Messages flash auto-dismiss (5s) | Les alertes disparaissent apres 5 secondes | [ ] | |
| 18.6 | Tooltips Bootstrap | Survol des elements avec `data-bs-toggle="tooltip"` | [ ] | |
| 18.7 | Validation inline Bootstrap (formulaires) | Champs invalides affiches en rouge | [ ] | |
| 18.8 | Pagination sur les listes longues | Navigation entre pages | [ ] | |
| 18.9 | Pages d'erreur personnalisees (404, 403, 500) | Pages d'erreur stylees | [ ] | |
| 18.10 | Impression (Ctrl+P) | Mise en page correcte pour impression | [ ] | |

---

## 19. DESKTOP APP

| # | Test | Resultat attendu | OK ? | Remarques |
|---|------|-------------------|------|-----------|
| 19.1 | Lancer `desktop_app.py` | Application Tkinter demarre | [ ] | |
| 19.2 | Interface desktop fonctionnelle | Navigation possible dans l'app | [ ] | |
| 19.3 | `desktop_launcher.py` (si pywebview installe) | WebView s'ouvre avec l'app | [ ] | |

---

## Resume des corrections appliquees

Les bugs suivants ont ete corriges dans cette version :

1. **Open redirect** : le parametre `next` est maintenant valide (doit commencer par `/` et pas `//`)
2. **can_manage()** : utilise maintenant `FamilyMember.MANAGER_ROLES` (inclut `chef_famille`, `parent`)
3. **Sidebar crash** : protection si `first_name` ou `last_name` est vide/None
4. **XSS calendrier** : utilisation de `|tojson` au lieu de `|e` pour les valeurs JS
5. **showNotification()** : cherche `.flash-container` ou `.main-content` au lieu de `.container`
6. **FullCalendar locale FR** : suppression du script locale 404 (deja inclus dans le bundle)
7. **Cascade delete logs** : ajout `cascade='all, delete-orphan'` sur la relation Document.logs
8. **Taches assignees** : les utilisateurs assignes peuvent voir/modifier les taches qui leur sont assignees
9. **Ordre auth remove_member** : verification `can_manage` avant les regles metier
10. **Zip Slip** : validation des chemins dans l'archive avant extraction
11. **Path traversal backup** : validation que le fichier est dans le dossier backups
12. **Nettoyage backup** : nettoyage du dossier temporaire en cas d'erreur de restauration
13. **Chiffrement silencieux** : log d'avertissement au lieu de `pass` silencieux
14. **Log retention** : configurable via variable d'environnement `LOG_RETENTION_DAYS`
15. **ProductionConfig.init_app()** : maintenant appelee au demarrage
16. **Session warning** : ne s'active plus sur les pages non authentifiees
17. **.gitignore** : ajout `.secret_key` et `.encryption_key`
