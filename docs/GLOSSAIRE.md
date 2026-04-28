# Glossaire - FamiliDocs

Termes techniques utilises dans le projet, definitions courtes pour l'oral.

---

## A

**AES (Advanced Encryption Standard)** : Algorithme de chiffrement symetrique, utilise dans
le projet via la bibliotheque Python `cryptography` (recette Fernet).

**AJAX (Asynchronous JavaScript And XML)** : Technique permettant a une page web d'envoyer
une requete au serveur sans recharger la page. Utilise pour la recherche globale et le
compteur de notifications.

**API REST** : Interface qui permet a deux logiciels de dialoguer en HTTP avec des verbes
GET, POST, PUT, DELETE et des donnees au format JSON.

**Attribut derive** : En UML, un attribut qui n'est pas stocke en BDD mais calcule
dynamiquement a partir d'autres attributs. Exemple : le statut "en retard" d'une tache.

## B

**bcrypt** : Algorithme de **hachage** de mots de passe, irreversible, qui ajoute un sel
aleatoire pour qu'un meme mot de passe donne deux hashs differents.

**Blueprint Flask** : Module qui regroupe des routes par fonctionnalite (auth, documents,
admin, etc.). FamiliDocs en a 10.

## C

**Chiffrement (vs hachage)** : Le chiffrement est **reversible** (avec une cle), le
hachage est **irreversible**. Les mots de passe sont haches (bcrypt), les documents prives
sont chiffres (AES).

**CRUD (Create, Read, Update, Delete)** : Les 4 operations de base sur des donnees.

**CSP (Content-Security-Policy)** : En-tete HTTP qui limite les sources autorisees pour
les scripts, styles, polices, images. Protege contre l'injection de code malveillant.

**CSRF (Cross-Site Request Forgery)** : Attaque ou un site malveillant force un utilisateur
connecte a executer une action a son insu. Protection : token CSRF unique dans chaque
formulaire (Flask-WTF).

## D

**Decorateur** : Fonction Python qui modifie le comportement d'une autre fonction. Exemples
dans le projet : `@login_required`, `@admin_required`, `@app.route()`.

## F

**Fernet** : Recette de chiffrement symetrique fournie par la bibliotheque Python
`cryptography`. Utilise AES-128 en mode CBC + HMAC-SHA256.

**Fixture pytest** : Fonction qui prepare des donnees de test reutilisables (utilisateur,
document, famille, etc.). Definies dans `conftest.py`.

## H

**Hachage** : Transformation a sens unique d'une donnee en une chaine de longueur fixe.
Utilise pour les mots de passe (bcrypt).

**HSTS (HTTP Strict Transport Security)** : En-tete HTTP qui force le navigateur a
utiliser HTTPS. Active uniquement en production.

**HttpOnly** : Attribut d'un cookie qui interdit son acces depuis JavaScript. Protege le
cookie de session contre le vol par XSS.

## J

**Jinja2** : Moteur de templates Python utilise par Flask. Permet d'inserer des variables
dans du HTML via `{{ variable }}` et des structures de controle via `{% if %}`.

## M

**MCD (Modele Conceptuel de Donnees)** : Schema qui represente les entites du systeme et
leurs relations, sans details d'implementation.

**MIME type** : Identifiant qui decrit le format d'un fichier (`application/pdf`,
`image/jpeg`, etc.). Verifie a l'upload pour eviter qu'un script soit deguise en image.

**MVC (Modele-Vue-Controleur)** : Patron de conception qui separe la logique en 3 couches :
Modele (donnees), Vue (affichage), Controleur (logique). FamiliDocs ajoute une couche
Service entre Controleur et Modele.

## O

**ORM (Object-Relational Mapping)** : Bibliotheque qui permet de manipuler une base de
donnees via des objets Python plutot qu'en SQL. FamiliDocs utilise SQLAlchemy 2.0.

## P

**Path traversal** : Attaque ou l'attaquant utilise `../../` dans un nom de fichier pour
acceder a des fichiers hors du dossier autorise. Protection : `os.path.realpath()` +
verification que le chemin reste dans le dossier `uploads`.

**PostgreSQL** : Systeme de gestion de base de donnees relationnel (SGBD), open-source,
robuste, utilise par FamiliDocs en developpement et en production.

**pseudo-etat initial** : Symbole UML (cercle plein noir) qui indique le point d'entree
d'un cycle de vie d'objet.

## R

**Rate limiting** : Limitation du nombre de requetes (ici : 5 tentatives de connexion en
15 minutes par IP) pour empecher les attaques par force brute.

**RGPD (Reglement General sur la Protection des Donnees)** : Reglementation europeenne
de 2018 qui impose 6 droits aux utilisateurs (acces, rectification, effacement,
portabilite, opposition, limitation).

## S

**SameSite (cookie)** : Attribut qui limite l'envoi du cookie entre sites differents.
Configure sur `Lax` dans le projet (compromis securite/UX).

**Sel (salt)** : Chaine aleatoire ajoutee a un mot de passe avant hachage, pour que deux
utilisateurs avec le meme mot de passe aient des hashs differents.

**Service Layer** : Couche intermediaire entre les controleurs (routes) et les modeles, qui
contient la logique metier complexe. FamiliDocs a 8 services.

**SQLAlchemy** : ORM Python utilise par FamiliDocs. Permet de changer de SGBD (PostgreSQL,
SQLite, MySQL) sans changer le code metier.

## T

**Token** : Chaine de caracteres unique et difficile a deviner. Utilise dans le projet pour
les liens de partage (`secrets.token_urlsafe(48)`) et la 2FA.

**TOTP (Time-based One-Time Password)** : Algorithme qui genere un code a 6 chiffres
change toutes les 30 secondes, base sur l'heure UTC + un secret partage. Standard RFC 6238,
utilise par Google Authenticator. Implemente via la bibliotheque `pyotp`.

## W

**Werkzeug** : Bibliotheque qui fournit le serveur de developpement Flask. En production
on utilise Gunicorn ou Waitress a la place.

**WSGI (Web Server Gateway Interface)** : Standard Python qui permet a un serveur web
(Nginx, Apache) de communiquer avec une application Python (Flask, Django).

## X

**XSS (Cross-Site Scripting)** : Attaque ou un attaquant injecte du JavaScript malveillant
dans une page. Protection : echappement automatique de Jinja2 + en-tete CSP.

## Z

**Zip Slip** : Attaque ou une archive ZIP contient un chemin avec `../../` pour ecraser
des fichiers a l'extraction. Protection : verification que chaque chemin reste dans le
dossier de destination.
