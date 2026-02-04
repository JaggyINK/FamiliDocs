"""
Routes de recherche avancee et gestion des tags
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.tag import Tag
from app.models.log import Log
from app.services.search_service import SearchService

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
@login_required
def advanced_search():
    """Page de recherche avancee"""
    query = request.args.get('q', '').strip()
    file_type = request.args.get('type', '').strip()
    folder_id = request.args.get('folder', type=int)
    tag_ids = request.args.getlist('tags', type=int)
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()
    confidentiality = request.args.get('confidentiality', '').strip()
    sort_by = request.args.get('sort', 'updated_at')
    sort_order = request.args.get('order', 'desc')

    # Conversion des dates
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        except ValueError:
            pass
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        except ValueError:
            pass

    # Lancer la recherche si des criteres sont fournis
    documents = []
    has_searched = False

    if query or file_type or folder_id or tag_ids or date_from or date_to or confidentiality:
        has_searched = True
        documents = SearchService.search_documents(
            user_id=current_user.id,
            query=query,
            file_type=file_type,
            folder_id=folder_id,
            tags=tag_ids if tag_ids else None,
            date_from=date_from,
            date_to=date_to,
            confidentiality=confidentiality,
            sort_by=sort_by,
            sort_order=sort_order
        )

    # Donnees pour les filtres
    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    tags = Tag.get_user_tags(current_user.id)

    return render_template(
        'search.html',
        documents=documents,
        has_searched=has_searched,
        query=query,
        file_type=file_type,
        selected_folder=folder_id,
        selected_tags=tag_ids,
        date_from=date_from_str,
        date_to=date_to_str,
        confidentiality=confidentiality,
        sort_by=sort_by,
        sort_order=sort_order,
        folders=folders,
        tags=tags,
        result_count=len(documents)
    )


@search_bp.route('/search/global')
@login_required
def global_search():
    """Recherche globale (API AJAX)"""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify({'documents': [], 'tasks': [], 'tags': []})

    results = SearchService.global_search(current_user.id, query)

    return jsonify({
        'documents': [
            {
                'id': d.id,
                'name': d.name,
                'type': d.file_type,
                'url': url_for('document.view', document_id=d.id)
            } for d in results['documents']
        ],
        'tasks': [
            {
                'id': t.id,
                'title': t.title,
                'status': t.status,
                'url': url_for('task.view', task_id=t.id)
            } for t in results['tasks']
        ],
        'tags': [
            {
                'id': t.id,
                'name': t.name,
                'color': t.color
            } for t in results['tags']
        ]
    })


# --- Gestion des tags ---

@search_bp.route('/tags')
@login_required
def list_tags():
    """Liste tous les tags de l'utilisateur"""
    tags = Tag.get_user_tags(current_user.id)
    return render_template('tags.html', tags=tags)


@search_bp.route('/tags/create', methods=['POST'])
@login_required
def create_tag():
    """Cree un nouveau tag"""
    name = request.form.get('name', '').strip()
    color = request.form.get('color', '#6c757d').strip()

    if not name:
        flash('Le nom du tag est obligatoire.', 'warning')
        return redirect(url_for('search.list_tags'))

    if len(name) > 50:
        flash('Le nom du tag ne peut pas depasser 50 caracteres.', 'warning')
        return redirect(url_for('search.list_tags'))

    # Verifier si le tag existe deja
    existing = Tag.query.filter_by(name=name.lower(), owner_id=current_user.id).first()
    if existing:
        flash('Ce tag existe deja.', 'warning')
        return redirect(url_for('search.list_tags'))

    tag = Tag(name=name.lower(), color=color, owner_id=current_user.id)
    db.session.add(tag)
    db.session.commit()

    flash(f'Tag "{name}" cree.', 'success')
    return redirect(url_for('search.list_tags'))


@search_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    """Supprime un tag"""
    tag = Tag.query.get_or_404(tag_id)

    if tag.owner_id != current_user.id:
        flash("Vous ne pouvez pas supprimer ce tag.", 'danger')
        return redirect(url_for('search.list_tags'))

    tag_name = tag.name
    db.session.delete(tag)
    db.session.commit()

    flash(f'Tag "{tag_name}" supprime.', 'success')
    return redirect(url_for('search.list_tags'))


@search_bp.route('/documents/<int:document_id>/tags', methods=['POST'])
@login_required
def add_tag_to_document(document_id):
    """Ajoute un tag a un document"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash("Vous n'avez pas le droit de modifier ce document.", 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    tag_id = request.form.get('tag_id', type=int)
    new_tag_name = request.form.get('new_tag', '').strip()

    if tag_id:
        tag = Tag.query.get(tag_id)
        if tag and tag.owner_id == current_user.id:
            if tag not in document.tags.all():
                document.tags.append(tag)
                db.session.commit()
                flash(f'Tag "{tag.name}" ajoute.', 'success')
            else:
                flash('Ce tag est deja associe au document.', 'info')
    elif new_tag_name:
        tag = Tag.get_or_create(new_tag_name, current_user.id)
        if tag not in document.tags.all():
            document.tags.append(tag)
        db.session.commit()
        flash(f'Tag "{new_tag_name}" ajoute.', 'success')

    return redirect(url_for('document.view', document_id=document_id))


@search_bp.route('/documents/<int:document_id>/tags/<int:tag_id>/remove', methods=['POST'])
@login_required
def remove_tag_from_document(document_id, tag_id):
    """Retire un tag d'un document"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash("Vous n'avez pas le droit de modifier ce document.", 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    tag = Tag.query.get_or_404(tag_id)
    if tag in document.tags.all():
        document.tags.remove(tag)
        db.session.commit()
        flash(f'Tag "{tag.name}" retire.', 'success')

    return redirect(url_for('document.view', document_id=document_id))
