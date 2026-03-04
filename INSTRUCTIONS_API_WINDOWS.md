# INSTRUCTIONS API REST - FamiliDocs (Windows / PyCharm)

> Guide complet pour implementer l'API REST JSON sur le backend Flask existant.
> L'app iOS communiquera avec cette API via le reseau local.

---

## Table des matieres

1. [Pre-requis](#1-pre-requis)
2. [Architecture](#2-architecture)
3. [Fichiers a modifier](#3-fichiers-a-modifier)
4. [Fichiers a creer](#4-fichiers-a-creer)
5. [Tests avec curl](#5-tests-avec-curl)
6. [Rendre le serveur accessible sur le reseau local](#6-rendre-le-serveur-accessible-sur-le-reseau-local)

---

## 1. Pre-requis

### Installer les dependances

```bash
# Dans le venv du projet
pip install PyJWT flask-cors
```

### Ajouter dans requirements.txt

```
PyJWT>=2.8.0
flask-cors>=4.0.0
```

---

## 2. Architecture

```
app/
  api/                          # NOUVEAU - Blueprint API REST
    __init__.py                 # Blueprint + decorateur jwt_required
    auth_api.py                 # POST /api/auth/login, /register, /me
    documents_api.py            # CRUD documents
    folders_api.py              # CRUD dossiers
    tasks_api.py                # CRUD taches
    families_api.py             # CRUD familles + membres + chat
    notifications_api.py        # Notifications
  services/
    jwt_service.py              # NOUVEAU - Generation/verification JWT
  config/
    config.py                   # MODIFIE - ajout JWT_SECRET_KEY, JWT_EXPIRATION
  __init__.py                   # MODIFIE - enregistrement blueprint api + CORS
```

Toutes les routes API sont prefixees par `/api/`.
L'authentification se fait via JWT (header `Authorization: Bearer <token>`).

---

## 3. Fichiers a modifier

### 3.1 `app/config/config.py`

Ajouter dans la classe `Config` (apres les autres attributs) :

```python
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 72))
```

### 3.2 `app/__init__.py`

Ajouter **en haut** du fichier, avec les autres imports :

```python
from flask_cors import CORS
```

Ajouter **dans la fonction `create_app`**, apres l'initialisation de l'app et avant l'enregistrement des blueprints existants :

```python
    # CORS pour l'API REST (permet les requetes depuis l'app iOS)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
```

Ajouter **avec les autres enregistrements de blueprints** :

```python
    # API REST
    from app.api import api_bp
    app.register_blueprint(api_bp)
```

---

## 4. Fichiers a creer

### 4.1 `app/services/jwt_service.py`

```python
"""Service JWT pour l'authentification API REST."""

import jwt
import datetime
from flask import current_app


def generate_token(user_id):
    """Genere un token JWT pour un utilisateur."""
    payload = {
        'user_id': user_id,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            hours=current_app.config['JWT_EXPIRATION_HOURS']
        )
    }
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )


def verify_token(token):
    """Verifie un token JWT et retourne le payload.

    Returns:
        dict avec 'user_id' si valide, None sinon.
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### 4.2 `app/api/__init__.py`

```python
"""Blueprint API REST avec authentification JWT."""

from functools import wraps
from flask import Blueprint, request, jsonify, g
from app.models.user import User
from app.services.jwt_service import verify_token

api_bp = Blueprint('api', __name__, url_prefix='/api')


def jwt_required(f):
    """Decorateur : verifie le token JWT dans le header Authorization."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token manquant'}), 401

        token = auth_header.split('Bearer ')[1]
        payload = verify_token(token)
        if payload is None:
            return jsonify({'error': 'Token invalide ou expire'}), 401

        user = User.query.get(payload['user_id'])
        if user is None or not user.is_active:
            return jsonify({'error': 'Utilisateur introuvable ou desactive'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorateur : verifie que l'utilisateur est admin (apres jwt_required)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.current_user.role != 'admin':
            return jsonify({'error': 'Acces refuse - admin requis'}), 403
        return f(*args, **kwargs)
    return decorated


# Import des sous-modules pour enregistrer les routes
from app.api import auth_api
from app.api import documents_api
from app.api import folders_api
from app.api import tasks_api
from app.api import families_api
from app.api import notifications_api
```

### 4.3 `app/api/auth_api.py`

```python
"""API Authentification : login, register, profil."""

from flask import request, jsonify, g
from app.api import api_bp, jwt_required
from app.models.user import User
from app.services.jwt_service import generate_token
from app import db


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Connexion et obtention du token JWT.

    Body JSON:
        {"email": "...", "password": "..."}

    Retourne:
        {"token": "...", "user": {...}}
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

    if not user.is_active:
        return jsonify({'error': 'Compte desactive'}), 403

    token = generate_token(user.id)

    return jsonify({
        'token': token,
        'user': _serialize_user(user)
    })


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """Inscription d'un nouvel utilisateur.

    Body JSON:
        {
            "email": "...",
            "username": "...",
            "password": "...",
            "first_name": "...",
            "last_name": "..."
        }

    Retourne:
        {"token": "...", "user": {...}}
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    # Validation
    if not all([email, username, password, first_name, last_name]):
        return jsonify({'error': 'Tous les champs sont requis'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Le mot de passe doit faire au moins 8 caracteres'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Cet email est deja utilise'}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Ce nom d\'utilisateur est deja pris'}), 409

    user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)

    return jsonify({
        'token': token,
        'user': _serialize_user(user)
    }), 201


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required
def api_me():
    """Retourne le profil de l'utilisateur connecte."""
    return jsonify({'user': _serialize_user(g.current_user)})


@api_bp.route('/auth/me', methods=['PUT'])
@jwt_required
def api_update_profile():
    """Met a jour le profil de l'utilisateur connecte.

    Body JSON (tous optionnels):
        {"first_name": "...", "last_name": "...", "email": "...", "family_title": "..."}
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    user = g.current_user

    if 'first_name' in data:
        user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        user.last_name = data['last_name'].strip()
    if 'email' in data:
        new_email = data['email'].strip().lower()
        existing = User.query.filter_by(email=new_email).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Cet email est deja utilise'}), 409
        user.email = new_email
    if 'family_title' in data:
        user.family_title = data['family_title']

    db.session.commit()
    return jsonify({'user': _serialize_user(user)})


@api_bp.route('/auth/change-password', methods=['POST'])
@jwt_required
def api_change_password():
    """Change le mot de passe.

    Body JSON:
        {"old_password": "...", "new_password": "..."}
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not g.current_user.check_password(old_password):
        return jsonify({'error': 'Ancien mot de passe incorrect'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'Le nouveau mot de passe doit faire au moins 8 caracteres'}), 400

    g.current_user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Mot de passe modifie avec succes'})


def _serialize_user(user):
    """Serialise un objet User en dict JSON."""
    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'family_title': user.family_title,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'profile_photo': user.profile_photo
    }
```

### 4.4 `app/api/documents_api.py`

```python
"""API Documents : CRUD, upload, download, partage."""

import os
import uuid
from datetime import datetime, date
from flask import request, jsonify, g, current_app, send_file
from werkzeug.utils import secure_filename
from app.api import api_bp, jwt_required
from app.models.document import Document
from app.models.folder import Folder
from app.models.permission import Permission
from app.models.tag import Tag
from app import db


@api_bp.route('/documents', methods=['GET'])
@jwt_required
def api_list_documents():
    """Liste les documents de l'utilisateur.

    Query params:
        folder_id (int, optionnel) : filtrer par dossier
        search (str, optionnel) : recherche dans le nom
        sort (str) : name, created_at, file_size (defaut: created_at)
        order (str) : asc, desc (defaut: desc)
        page (int) : numero de page (defaut: 1)
        per_page (int) : elements par page (defaut: 20)
    """
    user = g.current_user
    query = Document.query.filter_by(owner_id=user.id)

    # Filtre par dossier
    folder_id = request.args.get('folder_id', type=int)
    if folder_id is not None:
        query = query.filter_by(folder_id=folder_id)

    # Recherche
    search = request.args.get('search', '').strip()
    if search:
        query = query.filter(Document.name.ilike(f'%{search}%'))

    # Tri
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    sort_col = getattr(Document, sort, Document.created_at)
    if order == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'documents': [_serialize_document(d) for d in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@api_bp.route('/documents/shared', methods=['GET'])
@jwt_required
def api_shared_documents():
    """Liste les documents partages avec l'utilisateur."""
    user = g.current_user
    permissions = Permission.query.filter_by(user_id=user.id, can_view=True).all()
    docs = []
    for perm in permissions:
        doc = Document.query.get(perm.document_id)
        if doc and doc.owner_id != user.id:
            d = _serialize_document(doc)
            d['permissions'] = {
                'can_view': perm.can_view,
                'can_edit': perm.can_edit,
                'can_download': perm.can_download,
                'can_share': perm.can_share
            }
            docs.append(d)

    return jsonify({'documents': docs})


@api_bp.route('/documents/<int:doc_id>', methods=['GET'])
@jwt_required
def api_get_document(doc_id):
    """Retourne les details d'un document."""
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if not user.can_access_document(doc):
        return jsonify({'error': 'Acces refuse'}), 403

    result = _serialize_document(doc)

    # Ajouter les tags
    result['tags'] = [{'id': t.id, 'name': t.name, 'color': t.color} for t in doc.tags]

    # Ajouter les permissions (si proprietaire)
    if doc.owner_id == user.id:
        result['permissions'] = [
            {
                'id': p.id,
                'user_id': p.user_id,
                'user_name': f"{p.user.first_name} {p.user.last_name}" if p.user else None,
                'can_view': p.can_view,
                'can_edit': p.can_edit,
                'can_download': p.can_download,
                'can_share': p.can_share,
                'end_date': p.end_date.isoformat() if p.end_date else None
            }
            for p in doc.permissions
        ]

    return jsonify({'document': result})


@api_bp.route('/documents', methods=['POST'])
@jwt_required
def api_upload_document():
    """Upload un nouveau document.

    Multipart form:
        file (fichier) : le fichier a uploader
        name (str) : nom du document
        description (str, optionnel)
        folder_id (int, optionnel)
        confidentiality (str) : public, private, restricted (defaut: private)
        expiry_date (str, optionnel) : YYYY-MM-DD
    """
    user = g.current_user

    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier envoye'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400

    # Verifier l'extension
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    if ext not in allowed:
        return jsonify({'error': f'Extension .{ext} non autorisee'}), 400

    # Generer un nom unique
    stored_filename = f"{uuid.uuid4().hex}.{ext}"

    # Sauvegarder le fichier
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, stored_filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    # Creer le document en base
    name = request.form.get('name', original_filename).strip()
    description = request.form.get('description', '').strip()
    folder_id = request.form.get('folder_id', type=int)
    confidentiality = request.form.get('confidentiality', 'private')
    expiry_date_str = request.form.get('expiry_date', '')

    # Verifier que le dossier appartient a l'utilisateur
    if folder_id:
        folder = Folder.query.get(folder_id)
        if not folder or folder.owner_id != user.id:
            return jsonify({'error': 'Dossier introuvable'}), 404

    expiry_date = None
    if expiry_date_str:
        try:
            expiry_date = date.fromisoformat(expiry_date_str)
        except ValueError:
            return jsonify({'error': 'Format de date invalide (YYYY-MM-DD)'}), 400

    doc = Document(
        name=name,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=ext,
        file_size=file_size,
        description=description,
        confidentiality=confidentiality,
        expiry_date=expiry_date,
        owner_id=user.id,
        folder_id=folder_id
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({'document': _serialize_document(doc)}), 201


@api_bp.route('/documents/<int:doc_id>', methods=['PUT'])
@jwt_required
def api_update_document(doc_id):
    """Met a jour les metadonnees d'un document.

    Body JSON (tous optionnels):
        {
            "name": "...",
            "description": "...",
            "folder_id": int ou null,
            "confidentiality": "...",
            "expiry_date": "YYYY-MM-DD" ou null,
            "next_review_date": "YYYY-MM-DD" ou null
        }
    """
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if not user.can_edit_document(doc):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    if 'name' in data:
        doc.name = data['name'].strip()
    if 'description' in data:
        doc.description = data['description'].strip() if data['description'] else ''
    if 'folder_id' in data:
        if data['folder_id'] is not None:
            folder = Folder.query.get(data['folder_id'])
            if not folder or folder.owner_id != user.id:
                return jsonify({'error': 'Dossier introuvable'}), 404
        doc.folder_id = data['folder_id']
    if 'confidentiality' in data:
        if data['confidentiality'] in ('public', 'private', 'restricted'):
            doc.confidentiality = data['confidentiality']
    if 'expiry_date' in data:
        if data['expiry_date']:
            try:
                doc.expiry_date = date.fromisoformat(data['expiry_date'])
            except ValueError:
                return jsonify({'error': 'Format de date invalide'}), 400
        else:
            doc.expiry_date = None
    if 'next_review_date' in data:
        if data['next_review_date']:
            try:
                doc.next_review_date = date.fromisoformat(data['next_review_date'])
            except ValueError:
                return jsonify({'error': 'Format de date invalide'}), 400
        else:
            doc.next_review_date = None

    db.session.commit()
    return jsonify({'document': _serialize_document(doc)})


@api_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@jwt_required
def api_delete_document(doc_id):
    """Supprime un document (proprietaire ou admin uniquement)."""
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if doc.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    # Supprimer le fichier physique
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(doc)
    db.session.commit()

    return jsonify({'message': 'Document supprime'})


@api_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@jwt_required
def api_download_document(doc_id):
    """Telecharge un fichier document."""
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if not user.can_access_document(doc):
        return jsonify({'error': 'Acces refuse'}), 403

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.stored_filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Fichier introuvable sur le serveur'}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=doc.original_filename
    )


@api_bp.route('/documents/<int:doc_id>/share', methods=['POST'])
@jwt_required
def api_share_document(doc_id):
    """Partage un document avec un ou plusieurs utilisateurs.

    Body JSON:
        {
            "user_ids": [1, 2, 3],
            "can_edit": false,
            "can_download": true,
            "can_share": false,
            "end_date": "YYYY-MM-DD" (optionnel)
        }
    """
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if doc.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Seul le proprietaire peut partager'}), 403

    data = request.get_json()
    if not data or 'user_ids' not in data:
        return jsonify({'error': 'user_ids requis'}), 400

    user_ids = data['user_ids']
    can_edit = data.get('can_edit', False)
    can_download = data.get('can_download', True)
    can_share = data.get('can_share', False)
    end_date = None
    if data.get('end_date'):
        try:
            end_date = date.fromisoformat(data['end_date'])
        except ValueError:
            return jsonify({'error': 'Format de date invalide'}), 400

    created = []
    for uid in user_ids:
        if uid == user.id:
            continue
        target_user = User.query.get(uid)
        if not target_user:
            continue
        # Verifier si permission existe deja
        existing = Permission.query.filter_by(document_id=doc.id, user_id=uid).first()
        if existing:
            existing.can_edit = can_edit
            existing.can_download = can_download
            existing.can_share = can_share
            existing.end_date = end_date
        else:
            perm = Permission(
                document_id=doc.id,
                user_id=uid,
                granted_by=user.id,
                can_edit=can_edit,
                can_download=can_download,
                can_share=can_share,
                end_date=end_date
            )
            db.session.add(perm)
            created.append(uid)

    db.session.commit()
    return jsonify({'message': f'Document partage avec {len(created)} utilisateur(s)'})


@api_bp.route('/documents/<int:doc_id>/revoke/<int:user_id>', methods=['DELETE'])
@jwt_required
def api_revoke_permission(doc_id, user_id):
    """Revoque la permission d'un utilisateur sur un document."""
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if doc.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    perm = Permission.query.filter_by(document_id=doc.id, user_id=user_id).first()
    if not perm:
        return jsonify({'error': 'Permission introuvable'}), 404

    db.session.delete(perm)
    db.session.commit()
    return jsonify({'message': 'Permission revoquee'})


@api_bp.route('/documents/<int:doc_id>/tags', methods=['POST'])
@jwt_required
def api_add_tag(doc_id):
    """Ajoute un tag a un document.

    Body JSON:
        {"tag_id": int}  OU  {"name": "...", "color": "#hex"}
    """
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if not user.can_edit_document(doc):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    if 'tag_id' in data:
        tag = Tag.query.get(data['tag_id'])
        if not tag or tag.owner_id != user.id:
            return jsonify({'error': 'Tag introuvable'}), 404
    elif 'name' in data:
        name = data['name'].strip().lower()
        color = data.get('color', '#6c757d')
        tag = Tag.query.filter_by(name=name, owner_id=user.id).first()
        if not tag:
            tag = Tag(name=name, color=color, owner_id=user.id)
            db.session.add(tag)
            db.session.flush()
    else:
        return jsonify({'error': 'tag_id ou name requis'}), 400

    if tag not in doc.tags:
        doc.tags.append(tag)
        db.session.commit()

    return jsonify({'tag': {'id': tag.id, 'name': tag.name, 'color': tag.color}})


@api_bp.route('/documents/<int:doc_id>/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required
def api_remove_tag(doc_id, tag_id):
    """Retire un tag d'un document."""
    user = g.current_user
    doc = Document.query.get_or_404(doc_id)

    if not user.can_edit_document(doc):
        return jsonify({'error': 'Acces refuse'}), 403

    tag = Tag.query.get_or_404(tag_id)
    if tag in doc.tags:
        doc.tags.remove(tag)
        db.session.commit()

    return jsonify({'message': 'Tag retire'})


def _serialize_document(doc):
    """Serialise un Document en dict JSON."""
    return {
        'id': doc.id,
        'name': doc.name,
        'original_filename': doc.original_filename,
        'file_type': doc.file_type,
        'file_size': doc.file_size,
        'description': doc.description,
        'confidentiality': doc.confidentiality,
        'is_encrypted': doc.is_encrypted,
        'created_at': doc.created_at.isoformat() if doc.created_at else None,
        'updated_at': doc.updated_at.isoformat() if doc.updated_at else None,
        'expiry_date': doc.expiry_date.isoformat() if doc.expiry_date else None,
        'next_review_date': doc.next_review_date.isoformat() if doc.next_review_date else None,
        'is_expired': doc.is_expired,
        'is_expiring_soon': doc.is_expiring_soon,
        'owner_id': doc.owner_id,
        'folder_id': doc.folder_id,
        'folder_name': doc.folder.name if doc.folder else None,
        'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in doc.tags]
    }
```

### 4.5 `app/api/folders_api.py`

```python
"""API Dossiers : CRUD dossiers."""

from flask import request, jsonify, g
from app.api import api_bp, jwt_required
from app.models.folder import Folder
from app.models.document import Document
from app import db


@api_bp.route('/folders', methods=['GET'])
@jwt_required
def api_list_folders():
    """Liste les dossiers racine de l'utilisateur.

    Query params:
        parent_id (int, optionnel) : lister les sous-dossiers d'un dossier
    """
    user = g.current_user
    parent_id = request.args.get('parent_id', type=int)

    query = Folder.query.filter_by(owner_id=user.id, parent_id=parent_id)
    folders = query.order_by(Folder.name.asc()).all()

    return jsonify({
        'folders': [_serialize_folder(f) for f in folders]
    })


@api_bp.route('/folders/<int:folder_id>', methods=['GET'])
@jwt_required
def api_get_folder(folder_id):
    """Retourne un dossier avec ses documents et sous-dossiers."""
    user = g.current_user
    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    result = _serialize_folder(folder)
    from app.api.documents_api import _serialize_document
    result['documents'] = [_serialize_document(d) for d in folder.documents]
    result['subfolders'] = [_serialize_folder(sf) for sf in folder.subfolders]
    result['path'] = folder.get_path()

    return jsonify({'folder': result})


@api_bp.route('/folders', methods=['POST'])
@jwt_required
def api_create_folder():
    """Cree un nouveau dossier.

    Body JSON:
        {
            "name": "...",
            "description": "..." (optionnel),
            "category": "..." (optionnel, defaut: Autres),
            "parent_id": int (optionnel)
        }
    """
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Le nom est requis'}), 400

    parent_id = data.get('parent_id')
    if parent_id:
        parent = Folder.query.get(parent_id)
        if not parent or parent.owner_id != user.id:
            return jsonify({'error': 'Dossier parent introuvable'}), 404

    folder = Folder(
        name=name,
        description=data.get('description', '').strip(),
        category=data.get('category', 'Autres'),
        owner_id=user.id,
        parent_id=parent_id
    )
    db.session.add(folder)
    db.session.commit()

    return jsonify({'folder': _serialize_folder(folder)}), 201


@api_bp.route('/folders/<int:folder_id>', methods=['PUT'])
@jwt_required
def api_update_folder(folder_id):
    """Met a jour un dossier.

    Body JSON (tous optionnels):
        {"name": "...", "description": "...", "category": "..."}
    """
    user = g.current_user
    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != user.id:
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    if 'name' in data:
        folder.name = data['name'].strip()
    if 'description' in data:
        folder.description = data['description'].strip()
    if 'category' in data:
        folder.category = data['category']

    db.session.commit()
    return jsonify({'folder': _serialize_folder(folder)})


@api_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@jwt_required
def api_delete_folder(folder_id):
    """Supprime un dossier (doit etre vide)."""
    user = g.current_user
    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != user.id:
        return jsonify({'error': 'Acces refuse'}), 403

    if folder.documents or folder.subfolders:
        return jsonify({'error': 'Le dossier doit etre vide pour etre supprime'}), 400

    db.session.delete(folder)
    db.session.commit()
    return jsonify({'message': 'Dossier supprime'})


def _serialize_folder(folder):
    """Serialise un Folder en dict JSON."""
    return {
        'id': folder.id,
        'name': folder.name,
        'description': folder.description,
        'category': folder.category,
        'parent_id': folder.parent_id,
        'created_at': folder.created_at.isoformat() if folder.created_at else None,
        'updated_at': folder.updated_at.isoformat() if folder.updated_at else None,
        'document_count': len(folder.documents),
        'subfolder_count': len(folder.subfolders)
    }
```

### 4.6 `app/api/tasks_api.py`

```python
"""API Taches : CRUD taches."""

from datetime import date, datetime
from flask import request, jsonify, g
from app.api import api_bp, jwt_required
from app.models.task import Task
from app.models.user import User
from app import db


@api_bp.route('/tasks', methods=['GET'])
@jwt_required
def api_list_tasks():
    """Liste les taches de l'utilisateur (propres + assignees).

    Query params:
        status (str, optionnel) : pending, in_progress, completed, cancelled
        priority (str, optionnel) : low, normal, high, urgent
        page (int) : defaut 1
        per_page (int) : defaut 20
    """
    user = g.current_user

    # Taches dont l'utilisateur est proprietaire OU assignataire
    query = Task.query.filter(
        db.or_(Task.owner_id == user.id, Task.assigned_to_id == user.id)
    )

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    priority = request.args.get('priority')
    if priority:
        query = query.filter_by(priority=priority)

    query = query.order_by(Task.due_date.asc())

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tasks': [_serialize_task(t) for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@api_bp.route('/tasks/overdue', methods=['GET'])
@jwt_required
def api_overdue_tasks():
    """Liste les taches en retard."""
    user = g.current_user
    tasks = Task.query.filter(
        db.or_(Task.owner_id == user.id, Task.assigned_to_id == user.id),
        Task.due_date < date.today(),
        Task.status.in_(['pending', 'in_progress'])
    ).order_by(Task.due_date.asc()).all()

    return jsonify({'tasks': [_serialize_task(t) for t in tasks]})


@api_bp.route('/tasks/upcoming', methods=['GET'])
@jwt_required
def api_upcoming_tasks():
    """Liste les taches a venir.

    Query params:
        days (int) : nombre de jours a l'avance (defaut: 30)
    """
    from datetime import timedelta
    user = g.current_user
    days = request.args.get('days', 30, type=int)
    end_date = date.today() + timedelta(days=days)

    tasks = Task.query.filter(
        db.or_(Task.owner_id == user.id, Task.assigned_to_id == user.id),
        Task.due_date >= date.today(),
        Task.due_date <= end_date,
        Task.status.in_(['pending', 'in_progress'])
    ).order_by(Task.due_date.asc()).all()

    return jsonify({'tasks': [_serialize_task(t) for t in tasks]})


@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required
def api_get_task(task_id):
    """Retourne les details d'une tache."""
    user = g.current_user
    task = Task.query.get_or_404(task_id)

    if task.owner_id != user.id and task.assigned_to_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify({'task': _serialize_task(task)})


@api_bp.route('/tasks', methods=['POST'])
@jwt_required
def api_create_task():
    """Cree une nouvelle tache.

    Body JSON:
        {
            "title": "...",
            "description": "..." (optionnel),
            "due_date": "YYYY-MM-DD",
            "priority": "low|normal|high|urgent" (defaut: normal),
            "document_id": int (optionnel),
            "reminder_days": int (defaut: 7),
            "assigned_to_id": int (optionnel)
        }
    """
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    title = data.get('title', '').strip()
    due_date_str = data.get('due_date', '')

    if not title:
        return jsonify({'error': 'Le titre est requis'}), 400
    if not due_date_str:
        return jsonify({'error': 'La date d\'echeance est requise'}), 400

    try:
        due_date = date.fromisoformat(due_date_str)
    except ValueError:
        return jsonify({'error': 'Format de date invalide (YYYY-MM-DD)'}), 400

    task = Task(
        title=title,
        description=data.get('description', '').strip(),
        due_date=due_date,
        priority=data.get('priority', 'normal'),
        reminder_days=data.get('reminder_days', 7),
        owner_id=user.id,
        document_id=data.get('document_id'),
        assigned_to_id=data.get('assigned_to_id')
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({'task': _serialize_task(task)}), 201


@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required
def api_update_task(task_id):
    """Met a jour une tache.

    Body JSON (tous optionnels):
        {
            "title": "...",
            "description": "...",
            "due_date": "YYYY-MM-DD",
            "priority": "...",
            "reminder_days": int,
            "document_id": int ou null,
            "assigned_to_id": int ou null
        }
    """
    user = g.current_user
    task = Task.query.get_or_404(task_id)

    if task.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    if 'title' in data:
        task.title = data['title'].strip()
    if 'description' in data:
        task.description = data['description'].strip() if data['description'] else ''
    if 'due_date' in data:
        try:
            task.due_date = date.fromisoformat(data['due_date'])
        except ValueError:
            return jsonify({'error': 'Format de date invalide'}), 400
    if 'priority' in data:
        if data['priority'] in ('low', 'normal', 'high', 'urgent'):
            task.priority = data['priority']
    if 'reminder_days' in data:
        task.reminder_days = data['reminder_days']
    if 'document_id' in data:
        task.document_id = data['document_id']
    if 'assigned_to_id' in data:
        task.assigned_to_id = data['assigned_to_id']

    db.session.commit()
    return jsonify({'task': _serialize_task(task)})


@api_bp.route('/tasks/<int:task_id>/status', methods=['PUT'])
@jwt_required
def api_update_task_status(task_id):
    """Change le statut d'une tache.

    Body JSON:
        {"status": "pending|in_progress|completed|cancelled"}
    """
    user = g.current_user
    task = Task.query.get_or_404(task_id)

    if task.owner_id != user.id and task.assigned_to_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'status requis'}), 400

    new_status = data['status']
    if new_status not in ('pending', 'in_progress', 'completed', 'cancelled'):
        return jsonify({'error': 'Statut invalide'}), 400

    task.status = new_status
    if new_status == 'completed':
        task.completed_at = datetime.utcnow()
    else:
        task.completed_at = None

    db.session.commit()
    return jsonify({'task': _serialize_task(task)})


@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required
def api_delete_task(task_id):
    """Supprime une tache (proprietaire ou admin)."""
    user = g.current_user
    task = Task.query.get_or_404(task_id)

    if task.owner_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Tache supprimee'})


def _serialize_task(task):
    """Serialise une Task en dict JSON."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'priority': task.priority,
        'status': task.status,
        'reminder_days': task.reminder_days,
        'owner_id': task.owner_id,
        'owner_name': f"{task.owner.first_name} {task.owner.last_name}" if task.owner else None,
        'document_id': task.document_id,
        'assigned_to_id': task.assigned_to_id,
        'assigned_to_name': f"{task.assigned_to.first_name} {task.assigned_to.last_name}" if task.assigned_to else None,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'is_overdue': task.due_date < date.today() if task.due_date and task.status in ('pending', 'in_progress') else False
    }
```

### 4.7 `app/api/families_api.py`

```python
"""API Familles : CRUD familles, membres, chat."""

from datetime import datetime
from flask import request, jsonify, g
from app.api import api_bp, jwt_required
from app.models.family import Family, FamilyMember, ShareLink
from app.models.user import User
from app.models.message import Message
from app import db


@api_bp.route('/families', methods=['GET'])
@jwt_required
def api_list_families():
    """Liste les familles de l'utilisateur (creees + membre)."""
    user = g.current_user

    # Familles creees par l'utilisateur
    created = Family.query.filter_by(creator_id=user.id).all()

    # Familles dont l'utilisateur est membre
    memberships = FamilyMember.query.filter_by(user_id=user.id).all()
    member_family_ids = [m.family_id for m in memberships]
    member_families = Family.query.filter(
        Family.id.in_(member_family_ids),
        Family.creator_id != user.id
    ).all() if member_family_ids else []

    all_families = list({f.id: f for f in created + member_families}.values())

    return jsonify({
        'families': [_serialize_family(f, user) for f in all_families]
    })


@api_bp.route('/families/<int:family_id>', methods=['GET'])
@jwt_required
def api_get_family(family_id):
    """Retourne les details d'une famille avec ses membres."""
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    # Verifier que l'utilisateur est membre
    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership and family.creator_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    result = _serialize_family(family, user)
    result['members'] = [
        {
            'id': m.id,
            'user_id': m.user_id,
            'user_name': f"{m.user.first_name} {m.user.last_name}" if m.user else None,
            'user_email': m.user.email if m.user else None,
            'role': m.role,
            'joined_at': m.joined_at.isoformat() if m.joined_at else None
        }
        for m in family.members
    ]

    return jsonify({'family': result})


@api_bp.route('/families', methods=['POST'])
@jwt_required
def api_create_family():
    """Cree une nouvelle famille.

    Body JSON:
        {"name": "...", "description": "..." (optionnel)}
    """
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Le nom est requis'}), 400

    family = Family(
        name=name,
        description=data.get('description', '').strip(),
        creator_id=user.id
    )
    db.session.add(family)
    db.session.flush()

    # Ajouter le createur comme chef_famille
    member = FamilyMember(
        family_id=family.id,
        user_id=user.id,
        role='chef_famille'
    )
    db.session.add(member)
    db.session.commit()

    return jsonify({'family': _serialize_family(family, user)}), 201


@api_bp.route('/families/<int:family_id>', methods=['PUT'])
@jwt_required
def api_update_family(family_id):
    """Met a jour une famille.

    Body JSON (tous optionnels):
        {"name": "...", "description": "..."}
    """
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership or membership.role not in ('chef_famille', 'admin'):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON requis'}), 400

    if 'name' in data:
        family.name = data['name'].strip()
    if 'description' in data:
        family.description = data['description'].strip()

    db.session.commit()
    return jsonify({'family': _serialize_family(family, user)})


@api_bp.route('/families/<int:family_id>', methods=['DELETE'])
@jwt_required
def api_delete_family(family_id):
    """Supprime une famille (createur uniquement)."""
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    if family.creator_id != user.id:
        return jsonify({'error': 'Seul le createur peut supprimer la famille'}), 403

    db.session.delete(family)
    db.session.commit()
    return jsonify({'message': 'Famille supprimee'})


@api_bp.route('/families/<int:family_id>/invite', methods=['POST'])
@jwt_required
def api_create_invite(family_id):
    """Genere un lien d'invitation.

    Body JSON:
        {
            "expires_hours": 24 (defaut),
            "max_uses": 1 (defaut),
            "role": "lecteur" (defaut)
        }
    """
    import secrets
    from datetime import timedelta

    user = g.current_user
    family = Family.query.get_or_404(family_id)

    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership or membership.role not in ('chef_famille', 'admin', 'parent', 'gestionnaire'):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json() or {}
    expires_hours = data.get('expires_hours', 24)
    max_uses = data.get('max_uses', 1)
    role = data.get('role', 'lecteur')

    link = ShareLink(
        token=secrets.token_urlsafe(48),
        family_id=family.id,
        created_by=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
        max_uses=max_uses,
        granted_role=role
    )
    db.session.add(link)
    db.session.commit()

    return jsonify({
        'invite': {
            'token': link.token,
            'expires_at': link.expires_at.isoformat(),
            'max_uses': link.max_uses,
            'role': link.granted_role
        }
    }), 201


@api_bp.route('/families/join/<token>', methods=['POST'])
@jwt_required
def api_join_family(token):
    """Rejoindre une famille via un token d'invitation."""
    user = g.current_user

    link = ShareLink.query.filter_by(token=token).first()
    if not link or not link.is_valid:
        return jsonify({'error': 'Lien d\'invitation invalide ou expire'}), 400

    if not link.family_id:
        return jsonify({'error': 'Ce lien n\'est pas un lien de famille'}), 400

    # Verifier si deja membre
    existing = FamilyMember.query.filter_by(
        family_id=link.family_id, user_id=user.id
    ).first()
    if existing:
        return jsonify({'error': 'Vous etes deja membre de cette famille'}), 409

    member = FamilyMember(
        family_id=link.family_id,
        user_id=user.id,
        role=link.granted_role,
        invited_by=link.created_by
    )
    db.session.add(member)

    link.use_count += 1
    db.session.commit()

    family = Family.query.get(link.family_id)
    return jsonify({
        'message': f'Vous avez rejoint la famille {family.name}',
        'family': _serialize_family(family, user)
    })


@api_bp.route('/families/<int:family_id>/members/<int:member_id>/role', methods=['PUT'])
@jwt_required
def api_change_member_role(family_id, member_id):
    """Change le role d'un membre.

    Body JSON:
        {"role": "..."}
    """
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    my_membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not my_membership or my_membership.role not in ('chef_famille', 'admin', 'parent', 'gestionnaire'):
        return jsonify({'error': 'Acces refuse'}), 403

    target = FamilyMember.query.get_or_404(member_id)
    if target.family_id != family.id:
        return jsonify({'error': 'Membre introuvable dans cette famille'}), 404

    data = request.get_json()
    if not data or 'role' not in data:
        return jsonify({'error': 'role requis'}), 400

    new_role = data['role']
    valid_roles = ['chef_famille', 'admin', 'parent', 'gestionnaire', 'enfant', 'editeur', 'lecteur', 'invite']
    if new_role not in valid_roles:
        return jsonify({'error': 'Role invalide'}), 400

    # Restrictions
    if new_role == 'chef_famille':
        chef_count = FamilyMember.query.filter_by(family_id=family.id, role='chef_famille').count()
        if chef_count >= 2:
            return jsonify({'error': 'Maximum 2 chefs de famille'}), 400

    target.role = new_role
    db.session.commit()

    return jsonify({'message': f'Role modifie en {new_role}'})


@api_bp.route('/families/<int:family_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required
def api_remove_member(family_id, member_id):
    """Retire un membre de la famille."""
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    my_membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not my_membership or my_membership.role not in ('chef_famille', 'admin', 'parent', 'gestionnaire'):
        return jsonify({'error': 'Acces refuse'}), 403

    target = FamilyMember.query.get_or_404(member_id)
    if target.family_id != family.id:
        return jsonify({'error': 'Membre introuvable'}), 404

    if target.user_id == family.creator_id:
        return jsonify({'error': 'Impossible de retirer le createur'}), 400

    db.session.delete(target)
    db.session.commit()

    return jsonify({'message': 'Membre retire'})


@api_bp.route('/families/<int:family_id>/leave', methods=['POST'])
@jwt_required
def api_leave_family(family_id):
    """Quitter une famille."""
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    if family.creator_id == user.id:
        return jsonify({'error': 'Le createur ne peut pas quitter sa famille. Supprimez-la.'}), 400

    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership:
        return jsonify({'error': 'Vous n\'etes pas membre'}), 400

    db.session.delete(membership)
    db.session.commit()

    return jsonify({'message': 'Vous avez quitte la famille'})


# ---- Chat familial ----

@api_bp.route('/families/<int:family_id>/messages', methods=['GET'])
@jwt_required
def api_list_messages(family_id):
    """Liste les messages du chat familial.

    Query params:
        offset (int) : defaut 0
        limit (int) : defaut 50, max 100
    """
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    # Verifier l'appartenance
    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership and family.creator_id != user.id:
        return jsonify({'error': 'Acces refuse'}), 403

    offset = request.args.get('offset', 0, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)

    messages = Message.query.filter_by(
        family_id=family.id
    ).order_by(
        Message.created_at.desc()
    ).offset(offset).limit(limit).all()

    # Inverser pour avoir l'ordre chronologique
    messages.reverse()

    total = Message.query.filter_by(family_id=family.id).count()

    return jsonify({
        'messages': [_serialize_message(m) for m in messages],
        'total': total,
        'has_more': offset + limit < total
    })


@api_bp.route('/families/<int:family_id>/messages', methods=['POST'])
@jwt_required
def api_send_message(family_id):
    """Envoie un message dans le chat familial.

    Body JSON:
        {
            "content": "...",
            "is_announcement": false (optionnel)
        }
    """
    user = g.current_user
    family = Family.query.get_or_404(family_id)

    membership = FamilyMember.query.filter_by(family_id=family.id, user_id=user.id).first()
    if not membership:
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': 'Le contenu est requis'}), 400

    content = data['content'].strip()
    if len(content) > 2000:
        return jsonify({'error': 'Message trop long (max 2000 caracteres)'}), 400

    is_announcement = data.get('is_announcement', False)
    if is_announcement and membership.role not in ('admin', 'chef_famille', 'parent'):
        is_announcement = False

    msg = Message(
        family_id=family.id,
        sender_id=user.id,
        content=content,
        is_announcement=is_announcement
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({'message': _serialize_message(msg)}), 201


@api_bp.route('/messages/<int:message_id>', methods=['PUT'])
@jwt_required
def api_edit_message(message_id):
    """Modifie un message (auteur uniquement).

    Body JSON:
        {"content": "..."}
    """
    user = g.current_user
    msg = Message.query.get_or_404(message_id)

    if msg.sender_id != user.id:
        return jsonify({'error': 'Vous ne pouvez modifier que vos messages'}), 403

    data = request.get_json()
    if not data or not data.get('content', '').strip():
        return jsonify({'error': 'Le contenu est requis'}), 400

    msg.content = data['content'].strip()
    db.session.commit()

    return jsonify({'message': _serialize_message(msg)})


@api_bp.route('/messages/<int:message_id>', methods=['DELETE'])
@jwt_required
def api_delete_message(message_id):
    """Supprime un message (soft delete, auteur uniquement)."""
    user = g.current_user
    msg = Message.query.get_or_404(message_id)

    if msg.sender_id != user.id and user.role != 'admin':
        return jsonify({'error': 'Acces refuse'}), 403

    msg.soft_delete()
    db.session.commit()

    return jsonify({'message': 'Message supprime'})


def _serialize_family(family, current_user=None):
    """Serialise une Family en dict JSON."""
    membership = None
    if current_user:
        membership = FamilyMember.query.filter_by(
            family_id=family.id, user_id=current_user.id
        ).first()

    return {
        'id': family.id,
        'name': family.name,
        'description': family.description,
        'creator_id': family.creator_id,
        'created_at': family.created_at.isoformat() if family.created_at else None,
        'member_count': len(family.members),
        'my_role': membership.role if membership else None
    }


def _serialize_message(msg):
    """Serialise un Message en dict JSON."""
    return {
        'id': msg.id,
        'family_id': msg.family_id,
        'sender_id': msg.sender_id,
        'sender_name': f"{msg.sender.first_name} {msg.sender.last_name}" if msg.sender else None,
        'content': msg.content,
        'is_announcement': msg.is_announcement,
        'is_deleted': msg.is_deleted,
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
        'updated_at': msg.updated_at.isoformat() if msg.updated_at else None
    }
```

### 4.8 `app/api/notifications_api.py`

```python
"""API Notifications : lecture, marquage, suppression."""

from flask import request, jsonify, g
from app.api import api_bp, jwt_required
from app.models.notification import Notification
from app import db


@api_bp.route('/notifications', methods=['GET'])
@jwt_required
def api_list_notifications():
    """Liste les notifications de l'utilisateur.

    Query params:
        unread (bool, optionnel) : 1 pour ne voir que les non-lues
        type (str, optionnel) : filtrer par type
        page (int) : defaut 1
        per_page (int) : defaut 20
    """
    user = g.current_user
    query = Notification.query.filter_by(user_id=user.id)

    if request.args.get('unread') == '1':
        query = query.filter_by(is_read=False)

    notif_type = request.args.get('type')
    if notif_type:
        query = query.filter_by(type=notif_type)

    query = query.order_by(Notification.created_at.desc())

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'notifications': [_serialize_notification(n) for n in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
        'unread_count': Notification.query.filter_by(user_id=user.id, is_read=False).count()
    })


@api_bp.route('/notifications/count', methods=['GET'])
@jwt_required
def api_notification_count():
    """Retourne le nombre de notifications non lues."""
    count = Notification.query.filter_by(
        user_id=g.current_user.id, is_read=False
    ).count()
    return jsonify({'count': count})


@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@jwt_required
def api_mark_read(notif_id):
    """Marque une notification comme lue."""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != g.current_user.id:
        return jsonify({'error': 'Acces refuse'}), 403

    from datetime import datetime
    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Notification marquee comme lue'})


@api_bp.route('/notifications/read-all', methods=['POST'])
@jwt_required
def api_mark_all_read():
    """Marque toutes les notifications comme lues."""
    from datetime import datetime
    Notification.query.filter_by(
        user_id=g.current_user.id, is_read=False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    db.session.commit()

    return jsonify({'message': 'Toutes les notifications marquees comme lues'})


@api_bp.route('/notifications/<int:notif_id>', methods=['DELETE'])
@jwt_required
def api_delete_notification(notif_id):
    """Supprime une notification."""
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != g.current_user.id:
        return jsonify({'error': 'Acces refuse'}), 403

    db.session.delete(notif)
    db.session.commit()

    return jsonify({'message': 'Notification supprimee'})


@api_bp.route('/notifications/delete-read', methods=['POST'])
@jwt_required
def api_delete_read_notifications():
    """Supprime toutes les notifications lues."""
    Notification.query.filter_by(
        user_id=g.current_user.id, is_read=True
    ).delete()
    db.session.commit()

    return jsonify({'message': 'Notifications lues supprimees'})


def _serialize_notification(notif):
    """Serialise une Notification en dict JSON."""
    return {
        'id': notif.id,
        'type': notif.type,
        'title': notif.title,
        'message': notif.message,
        'priority': notif.priority,
        'is_read': notif.is_read,
        'document_id': notif.document_id,
        'task_id': notif.task_id,
        'created_at': notif.created_at.isoformat() if notif.created_at else None,
        'read_at': notif.read_at.isoformat() if notif.read_at else None
    }
```

---

## 5. Tests avec curl

### 5.1 Login et obtenir un token

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@familidocs.local", "password": "Admin123!"}'
```

Reponse :
```json
{
  "token": "eyJ0eXAi...",
  "user": {"id": 1, "email": "admin@familidocs.local", ...}
}
```

Sauvegarder le token :
```bash
TOKEN="eyJ0eXAi..."
```

### 5.2 Profil utilisateur

```bash
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 5.3 Lister les documents

```bash
curl http://localhost:5000/api/documents \
  -H "Authorization: Bearer $TOKEN"
```

### 5.4 Uploader un document

```bash
curl -X POST http://localhost:5000/api/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/chemin/vers/fichier.pdf" \
  -F "name=Mon document" \
  -F "confidentiality=private"
```

### 5.5 Creer un dossier

```bash
curl -X POST http://localhost:5000/api/folders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Administratif", "category": "Administratif"}'
```

### 5.6 Creer une tache

```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Renouveler passeport", "due_date": "2026-06-01", "priority": "high"}'
```

### 5.7 Lister les familles

```bash
curl http://localhost:5000/api/families \
  -H "Authorization: Bearer $TOKEN"
```

### 5.8 Notifications non lues

```bash
curl http://localhost:5000/api/notifications/count \
  -H "Authorization: Bearer $TOKEN"
```

---

## 6. Rendre le serveur accessible sur le reseau local

### 6.1 Lancer Flask sur toutes les interfaces

Dans votre fichier de lancement (ou en ligne de commande) :

```bash
flask run --host=0.0.0.0 --port=5000
```

Ou dans votre script Python :

```python
if __name__ == '__main__':
    app = create_app('development')
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 6.2 Trouver l'adresse IP du PC Windows

```bash
ipconfig
```

Cherchez l'adresse IPv4 de votre connexion Wi-Fi (ex: `192.168.1.42`).

### 6.3 Ouvrir le port dans le pare-feu Windows

1. Ouvrir "Pare-feu Windows Defender avec securite avancee"
2. Regles de trafic entrant > Nouvelle regle
3. Type : Port
4. TCP, Port specifique : 5000
5. Autoriser la connexion
6. Cocher : Prive (reseau domestique)
7. Nom : "FamiliDocs API"

### 6.4 Tester depuis le Mac

```bash
curl http://192.168.1.42:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@familidocs.local", "password": "Admin123!"}'
```

Si vous obtenez une reponse JSON avec un token, le serveur est bien accessible.

### 6.5 Configuration .env recommandee

```env
FLASK_ENV=development
DATABASE_URL=postgresql://jagadmin:pass@localhost:5432/familidocs
JWT_SECRET_KEY=votre-cle-secrete-longue-et-aleatoire
JWT_EXPIRATION_HOURS=72
```

---

## Resume des endpoints API

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/login` | Connexion (retourne token) |
| POST | `/api/auth/register` | Inscription |
| GET | `/api/auth/me` | Profil courant |
| PUT | `/api/auth/me` | Modifier profil |
| POST | `/api/auth/change-password` | Changer mot de passe |
| GET | `/api/documents` | Lister documents |
| GET | `/api/documents/shared` | Documents partages avec moi |
| GET | `/api/documents/:id` | Detail document |
| POST | `/api/documents` | Upload document (multipart) |
| PUT | `/api/documents/:id` | Modifier document |
| DELETE | `/api/documents/:id` | Supprimer document |
| GET | `/api/documents/:id/download` | Telecharger fichier |
| POST | `/api/documents/:id/share` | Partager document |
| DELETE | `/api/documents/:id/revoke/:user_id` | Revoquer permission |
| POST | `/api/documents/:id/tags` | Ajouter tag |
| DELETE | `/api/documents/:id/tags/:tag_id` | Retirer tag |
| GET | `/api/folders` | Lister dossiers |
| GET | `/api/folders/:id` | Detail dossier |
| POST | `/api/folders` | Creer dossier |
| PUT | `/api/folders/:id` | Modifier dossier |
| DELETE | `/api/folders/:id` | Supprimer dossier |
| GET | `/api/tasks` | Lister taches |
| GET | `/api/tasks/overdue` | Taches en retard |
| GET | `/api/tasks/upcoming` | Taches a venir |
| GET | `/api/tasks/:id` | Detail tache |
| POST | `/api/tasks` | Creer tache |
| PUT | `/api/tasks/:id` | Modifier tache |
| PUT | `/api/tasks/:id/status` | Changer statut |
| DELETE | `/api/tasks/:id` | Supprimer tache |
| GET | `/api/families` | Lister familles |
| GET | `/api/families/:id` | Detail famille |
| POST | `/api/families` | Creer famille |
| PUT | `/api/families/:id` | Modifier famille |
| DELETE | `/api/families/:id` | Supprimer famille |
| POST | `/api/families/:id/invite` | Creer invitation |
| POST | `/api/families/join/:token` | Rejoindre famille |
| PUT | `/api/families/:id/members/:mid/role` | Changer role membre |
| DELETE | `/api/families/:id/members/:mid` | Retirer membre |
| POST | `/api/families/:id/leave` | Quitter famille |
| GET | `/api/families/:id/messages` | Chat - lister messages |
| POST | `/api/families/:id/messages` | Chat - envoyer message |
| PUT | `/api/messages/:id` | Chat - modifier message |
| DELETE | `/api/messages/:id` | Chat - supprimer message |
| GET | `/api/notifications` | Lister notifications |
| GET | `/api/notifications/count` | Compteur non-lues |
| POST | `/api/notifications/:id/read` | Marquer comme lue |
| POST | `/api/notifications/read-all` | Tout marquer comme lu |
| DELETE | `/api/notifications/:id` | Supprimer notification |
| POST | `/api/notifications/delete-read` | Supprimer les lues |
