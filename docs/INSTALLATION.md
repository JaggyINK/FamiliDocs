# Guide d'installation - FamiliDocs

Procedure complete pour installer, configurer et lancer le projet.

---

## 1. Prerequis

| Outil | Version minimale | Verification |
|---|---|---|
| Python | 3.10 (recommande 3.12) | `python --version` |
| pip | 22+ | `pip --version` |
| PostgreSQL | 16 | `psql --version` |
| Git | 2.30+ | `git --version` |

**Systeme d'exploitation** : Windows 10/11, Linux (Debian/Ubuntu), macOS. Pour Windows on
recommande WSL2 si vous voulez heberger PostgreSQL en local sous Linux.

---

## 2. Recuperation du code

```bash
git clone <url-du-repo> FamiliDocs
cd FamiliDocs
```

---

## 3. Environnement virtuel Python

### Sous Windows (cmd)
```bash
python -m venv venv
venv\Scripts\activate
```

### Sous Linux / macOS / WSL
```bash
python3 -m venv venv
source venv/bin/activate
```

Une fois actif, le prompt commence par `(venv)`.

---

## 4. Installation des dependances

```bash
pip install -r requirements.txt
```

Ca installe : Flask 3.0, SQLAlchemy 2.0, Flask-Login, Flask-WTF, bcrypt 4.1,
cryptography 41, pyotp 2.9, qrcode, psycopg2-binary, schedule, pytest, pytest-flask,
customtkinter (desktop), pillow, pyinstaller.

---

## 5. Configuration de la base PostgreSQL

### Creer la base et l'utilisateur (psql)

```sql
CREATE USER jagadmin WITH PASSWORD 'pass';
CREATE DATABASE familidocs OWNER jagadmin;
GRANT ALL PRIVILEGES ON DATABASE familidocs TO jagadmin;
```

Sous WSL :
```bash
sudo -u postgres psql -c "CREATE USER jagadmin WITH PASSWORD 'pass';"
sudo -u postgres psql -c "CREATE DATABASE familidocs OWNER jagadmin;"
```

---

## 6. Configuration du fichier `.env`

```bash
cp .env.example .env
```

Editer `.env` avec :

```
FLASK_ENV=development
DATABASE_URL=postgresql://jagadmin:pass@localhost:5432/familidocs
LOG_LEVEL=INFO
```

Optionnel pour la production :
- `SECRET_KEY` (obligatoire en prod, sinon generation auto en dev)
- `ENCRYPTION_KEY` (sinon generation auto dans `.encryption_key`)
- `EMAIL_ENABLED=true` + variables SMTP pour les notifications par email

---

## 7. Donnees de demonstration (optionnel mais recommande)

```bash
python seed_demo_data.py
```

Cree la famille Dupont :
- 5 utilisateurs (Jean, Marie, Lucas, Emma, Pierre)
- 20 documents
- 19 partages, 9 taches, 14 messages, 10 notifications

Mot de passe pour tous les comptes demo : `Demo2024!`

---

## 8. Lancement

### Application web
```bash
python run.py
```
Acceder a http://localhost:5000.

### Application desktop
```bash
python desktop_app.py
```
La fenetre CustomTkinter s'ouvre. Memes identifiants que le web (meme BDD).

### Compiler le .exe (Windows uniquement)
```bash
build_exe.bat
```
Le binaire est genere dans `dist/FamiliDocs.exe`.

---

## 9. Verification

```bash
pytest tests/ -v
```
Resultat attendu : `307 passed`.

---

## 10. Deploiement en production (apercu)

Le `python run.py` utilise le serveur de developpement Werkzeug, **pas adapte a la production**.

Pour la prod il faut :

1. **Serveur WSGI** : Gunicorn (Linux) ou Waitress (Windows)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 'app:create_app("production")'
   ```

2. **Reverse proxy** : Nginx en frontal pour HTTPS, gestion des fichiers statiques,
   limitation de bande passante

3. **HTTPS** : certificat Let's Encrypt avec `certbot`

4. **Variables obligatoires** :
   - `SECRET_KEY` (cle aleatoire de 32 octets)
   - `DATABASE_URL` (PostgreSQL distant ou managed)
   - `ENCRYPTION_KEY` (cle Fernet)
   - `FLASK_ENV=production`

5. **Reverse proxy systemd** ou **Docker** pour redemarrage automatique

6. **Sauvegarde** : cron quotidien qui execute `BackupService.create_backup()`

---

## 11. Depannage

| Probleme | Solution |
|---|---|
| `ModuleNotFoundError` | Verifier que `venv` est bien active |
| `DATABASE_URL non definie` | Copier `.env.example` en `.env` |
| Connexion PostgreSQL refusee | Verifier que le service PostgreSQL est demarre |
| `Port 5000 deja utilise` | Lancer `python run.py` apres avoir libere le port (ou changer le port dans `run.py`) |
| Tests echouent | Re-lancer `pip install -r requirements.txt` |
