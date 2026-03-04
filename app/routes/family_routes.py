"""
Routes de gestion des familles virtuelles et liens de partage securises
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from app.models import db
from app.models.family import Family, FamilyMember, ShareLink
from app.models.document import Document
from app.models.permission import Permission
from app.models.user import User
from app.models.log import Log
from app.services.notification_service import NotificationService

family_bp = Blueprint('family', __name__)


# --- Route d'invitation smart (accessible sans connexion) ---

@family_bp.route('/join/<token>')
def join_family(token):
    """
    Route d'invitation smart - F6
    Redirige vers login ou register selon l'état de connexion
    """
    link = ShareLink.query.filter_by(token=token).first()

    if not link:
        flash("Lien d'invitation invalide ou expiré.", 'danger')
        return redirect(url_for('auth.login'))

    if not link.is_valid:
        flash("Ce lien a expiré ou a atteint sa limite d'utilisation.", 'warning')
        return redirect(url_for('auth.login'))

    if not link.family_id:
        flash("Lien invalide.", 'danger')
        return redirect(url_for('auth.login'))

    family = Family.query.get(link.family_id)
    if not family:
        flash("Groupe introuvable.", 'danger')
        return redirect(url_for('auth.login'))

    # Si l'utilisateur est connecté, traiter directement l'invitation
    if current_user.is_authenticated:
        return redirect(url_for('family.accept_invite', token=token))

    # Stocker le token en session pour après login/register
    session['pending_invite_token'] = token

    # Afficher la page de choix login/register avec infos famille
    return render_template(
        'join_family.html',
        family=family,
        link=link,
        role_name=FamilyMember.ROLES.get(link.granted_role, 'Membre')
    )


# --- Gestion des familles ---

@family_bp.route('/families')
@login_required
def list_families():
    """Liste des groupes familiaux de l'utilisateur"""
    # Familles creees par l'utilisateur
    created = Family.query.filter_by(creator_id=current_user.id).all()

    # Familles dont l'utilisateur est membre
    memberships = FamilyMember.query.filter_by(user_id=current_user.id).all()
    member_families = []
    for m in memberships:
        if m.family.creator_id != current_user.id:
            member_families.append(m.family)

    return render_template(
        'families.html',
        created_families=created,
        member_families=member_families,
        roles=FamilyMember.ROLES
    )


@family_bp.route('/families/create', methods=['GET', 'POST'])
@login_required
def create_family():
    """Cree un nouveau groupe familial"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Le nom du groupe est obligatoire.', 'warning')
            return redirect(url_for('family.create_family'))

        if len(name) > 100:
            flash('Le nom ne peut pas depasser 100 caracteres.', 'warning')
            return redirect(url_for('family.create_family'))

        family = Family(
            name=name,
            description=description,
            creator_id=current_user.id
        )
        db.session.add(family)
        db.session.flush()

        # Le createur est automatiquement admin
        member = FamilyMember(
            family_id=family.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(member)
        db.session.commit()

        flash(f'Groupe "{name}" cree avec succes.', 'success')
        return redirect(url_for('family.view_family', family_id=family.id))

    return render_template('create_family.html')


@family_bp.route('/families/<int:family_id>')
@login_required
def view_family(family_id):
    """Affiche les details d'un groupe familial"""
    family = Family.query.get_or_404(family_id)

    if not family.is_member(current_user.id):
        flash("Vous n'etes pas membre de ce groupe.", 'danger')
        return redirect(url_for('family.list_families'))

    members = FamilyMember.query.filter_by(family_id=family_id).all()
    can_manage = family.can_manage(current_user.id)

    # Liens d'invitation actifs (si gestionnaire)
    invite_links = []
    if can_manage:
        invite_links = ShareLink.query.filter(
            ShareLink.family_id == family_id,
            ShareLink.is_revoked == False
        ).all()
        # Filtrer les expires
        valid_links = []
        for link in invite_links:
            if link.is_valid:
                valid_links.append(link)
        invite_links = valid_links

    return render_template(
        'view_family.html',
        family=family,
        members=members,
        can_manage=can_manage,
        invite_links=invite_links,
        roles=FamilyMember.ROLES
    )


@family_bp.route('/families/<int:family_id>/invite', methods=['POST'])
@login_required
def create_invite_link(family_id):
    """Genere un lien d'invitation securise pour le groupe"""
    family = Family.query.get_or_404(family_id)

    if not family.can_manage(current_user.id):
        flash("Vous n'avez pas le droit d'inviter des membres.", 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    expires_hours = request.form.get('expires_hours', 24, type=int)
    max_uses = request.form.get('max_uses', 1, type=int)
    granted_role = request.form.get('role', 'lecteur')

    # Validation
    if expires_hours not in [1, 24, 72, 168]:
        expires_hours = 24
    if max_uses not in [1, 3, 5, 10]:
        max_uses = 1
    if granted_role not in FamilyMember.ROLES:
        granted_role = 'lecteur'

    link = ShareLink.create_share_link(
        family_id=family_id,
        created_by=current_user.id,
        expires_hours=expires_hours,
        max_uses=max_uses,
        granted_role=granted_role
    )
    db.session.commit()

    flash('Lien d\'invitation genere avec succes.', 'success')
    return redirect(url_for('family.view_family', family_id=family_id))


@family_bp.route('/families/<int:family_id>/members/<int:member_id>/role', methods=['POST'])
@login_required
def change_member_role(family_id, member_id):
    """Modifie le role d'un membre"""
    family = Family.query.get_or_404(family_id)

    if not family.can_manage(current_user.id):
        flash("Vous n'avez pas le droit de modifier les roles.", 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    member = FamilyMember.query.get_or_404(member_id)
    if member.family_id != family_id:
        flash('Membre invalide.', 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    # On ne peut pas modifier le role du createur
    if member.user_id == family.creator_id:
        flash('Impossible de modifier le role du createur.', 'warning')
        return redirect(url_for('family.view_family', family_id=family_id))

    new_role = request.form.get('role', 'lecteur')
    current_member = FamilyMember.query.filter_by(
        family_id=family_id, user_id=current_user.id
    ).first()

    # RESTRICTION: Un gestionnaire ne peut pas promouvoir en admin ou chef_famille
    if current_member and current_member.role == 'gestionnaire':
        if new_role in ('admin', 'chef_famille'):
            flash("Un gestionnaire ne peut pas promouvoir quelqu'un en admin ou chef de famille.", 'warning')
            return redirect(url_for('family.view_family', family_id=family_id))

    # RESTRICTION: Limite de 2 chefs de famille max
    if new_role == 'chef_famille':
        chefs_count = FamilyMember.query.filter_by(
            family_id=family_id, role='chef_famille'
        ).count()
        if chefs_count >= 2:
            flash("Il ne peut y avoir que 2 chefs de famille maximum.", 'warning')
            return redirect(url_for('family.view_family', family_id=family_id))

    if new_role in FamilyMember.ROLES:
        member.role = new_role
        db.session.commit()
        flash(f'Role mis a jour.', 'success')

    return redirect(url_for('family.view_family', family_id=family_id))


@family_bp.route('/families/<int:family_id>/members/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_member(family_id, member_id):
    """Retire un membre du groupe + revoque ses acces aux documents"""
    from app.services.permission_service import PermissionService

    family = Family.query.get_or_404(family_id)
    member = FamilyMember.query.get_or_404(member_id)

    # On ne peut pas retirer le createur
    if member.user_id == family.creator_id:
        flash('Impossible de retirer le createur du groupe.', 'warning')
        return redirect(url_for('family.view_family', family_id=family_id))

    # Verification des droits d'abord
    if not family.can_manage(current_user.id):
        flash("Vous n'avez pas le droit de retirer des membres.", 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    # RESTRICTION: Un gestionnaire ne peut retirer que les invites et lecteurs
    current_member = FamilyMember.query.filter_by(
        family_id=family_id, user_id=current_user.id
    ).first()

    if current_member and current_member.role == 'gestionnaire':
        if member.role not in ('invite', 'lecteur'):
            flash("Un gestionnaire ne peut retirer que les invites et lecteurs.", 'warning')
            return redirect(url_for('family.view_family', family_id=family_id))

    user = User.query.get(member.user_id)
    if not user:
        flash("Utilisateur introuvable.", 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    user_name = user.full_name

    # REVOCATION AUTO: Supprimer tous les acces aux documents partages par les membres de la famille
    revoked_count = PermissionService.revoke_all_permissions_for_user(member.user_id)

    db.session.delete(member)
    db.session.commit()

    flash(f'{user_name} a ete retire du groupe. {revoked_count} acces revoque(s).', 'success')
    return redirect(url_for('family.view_family', family_id=family_id))


@family_bp.route('/families/<int:family_id>/leave', methods=['POST'])
@login_required
def leave_family(family_id):
    """Quitter un groupe familial"""
    family = Family.query.get_or_404(family_id)

    if family.creator_id == current_user.id:
        flash('Le createur ne peut pas quitter le groupe. Supprimez-le a la place.', 'warning')
        return redirect(url_for('family.view_family', family_id=family_id))

    member = FamilyMember.query.filter_by(
        family_id=family_id, user_id=current_user.id
    ).first()

    if member:
        db.session.delete(member)
        db.session.commit()
        flash(f'Vous avez quitte le groupe "{family.name}".', 'info')

    return redirect(url_for('family.list_families'))


@family_bp.route('/families/<int:family_id>/delete', methods=['POST'])
@login_required
def delete_family(family_id):
    """Supprime un groupe familial"""
    family = Family.query.get_or_404(family_id)

    if family.creator_id != current_user.id:
        flash("Seul le createur peut supprimer le groupe.", 'danger')
        return redirect(url_for('family.view_family', family_id=family_id))

    family_name = family.name
    db.session.delete(family)
    db.session.commit()

    flash(f'Groupe "{family_name}" supprime.', 'success')
    return redirect(url_for('family.list_families'))


# --- Liens de partage securises ---

@family_bp.route('/invite/<token>')
@login_required
def accept_invite(token):
    """Accepte une invitation via lien securise"""
    link = ShareLink.query.filter_by(token=token).first()

    if not link:
        flash('Lien d\'invitation invalide ou expire.', 'danger')
        return redirect(url_for('user.dashboard'))

    if not link.is_valid:
        flash('Ce lien a expire ou a atteint sa limite d\'utilisation.', 'warning')
        return redirect(url_for('user.dashboard'))

    # Invitation a un groupe familial
    if link.family_id:
        family = Family.query.get(link.family_id)
        if not family:
            flash('Groupe introuvable.', 'danger')
            return redirect(url_for('user.dashboard'))

        # Verifier si deja membre
        if family.is_member(current_user.id):
            flash('Vous etes deja membre de ce groupe.', 'info')
            return redirect(url_for('family.view_family', family_id=family.id))

        # Ajouter comme membre
        member = FamilyMember(
            family_id=family.id,
            user_id=current_user.id,
            role=link.granted_role,
            invited_by=link.created_by
        )
        db.session.add(member)
        link.use()
        db.session.commit()

        # Notification au createur
        NotificationService.notify_system(
            link.created_by,
            f'Nouveau membre : {current_user.full_name}',
            f'{current_user.full_name} a rejoint le groupe "{family.name}" via lien d\'invitation.'
        )

        flash(f'Bienvenue dans le groupe "{family.name}" !', 'success')
        return redirect(url_for('family.view_family', family_id=family.id))

    # Lien de partage de document
    if link.document_id:
        return redirect(url_for('family.accept_share_link', token=token))

    flash('Lien invalide.', 'danger')
    return redirect(url_for('user.dashboard'))


@family_bp.route('/share/<token>')
@login_required
def accept_share_link(token):
    """Accepte un lien de partage de document"""
    link = ShareLink.query.filter_by(token=token).first()

    if not link or not link.is_valid:
        flash('Lien de partage invalide ou expire.', 'danger')
        return redirect(url_for('user.dashboard'))

    if not link.document_id:
        flash('Lien invalide.', 'danger')
        return redirect(url_for('user.dashboard'))

    document = Document.query.get(link.document_id)
    if not document:
        flash('Document introuvable.', 'danger')
        return redirect(url_for('user.dashboard'))

    # Ne pas partager avec soi-meme
    if document.owner_id == current_user.id:
        flash('C\'est votre propre document.', 'info')
        return redirect(url_for('document.view', document_id=document.id))

    # Definir les permissions selon le role
    role_permissions = {
        'lecteur': {'can_edit': False, 'can_download': False, 'can_share': False},
        'editeur': {'can_edit': True, 'can_download': True, 'can_share': False},
        'gestionnaire': {'can_edit': True, 'can_download': True, 'can_share': True},
        'admin': {'can_edit': True, 'can_download': True, 'can_share': True},
        'invite': {'can_edit': False, 'can_download': False, 'can_share': False},
    }
    perms = role_permissions.get(link.granted_role, role_permissions['lecteur'])

    # Creer ou mettre a jour la permission
    permission = Permission.grant_access(
        document_id=document.id,
        user_id=current_user.id,
        granted_by=link.created_by,
        can_edit=perms['can_edit'],
        can_download=perms['can_download'],
        can_share=perms['can_share']
    )

    existing = Permission.query.filter_by(
        document_id=document.id, user_id=current_user.id
    ).first()
    if not existing:
        db.session.add(permission)

    link.use()

    Log.create_log(
        user_id=current_user.id,
        action='document_share',
        document_id=document.id,
        details=f"Acces obtenu via lien securise (role: {link.granted_role})"
    )
    db.session.commit()

    # Notification au proprietaire
    NotificationService.notify_document_shared(document, current_user.id, current_user)

    flash(f'Acces au document "{document.name}" accorde.', 'success')
    return redirect(url_for('document.view', document_id=document.id))


@family_bp.route('/documents/<int:document_id>/share-link', methods=['POST'])
@login_required
def create_share_link(document_id):
    """Genere un lien de partage pour un document"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash("Vous ne pouvez pas partager ce document.", 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    expires_hours = request.form.get('expires_hours', 24, type=int)
    max_uses = request.form.get('max_uses', 1, type=int)

    if expires_hours not in [1, 24, 72, 168]:
        expires_hours = 24
    if max_uses not in [1, 3, 5, 10]:
        max_uses = 1

    link = ShareLink.create_share_link(
        document_id=document_id,
        created_by=current_user.id,
        expires_hours=expires_hours,
        max_uses=max_uses,
        granted_role='lecteur'
    )
    db.session.commit()

    flash('Lien de partage securise genere.', 'success')
    return redirect(url_for('document.share', document_id=document_id))


@family_bp.route('/share-links/<int:link_id>/revoke', methods=['POST'])
@login_required
def revoke_share_link(link_id):
    """Revoque un lien de partage"""
    link = ShareLink.query.get_or_404(link_id)

    if link.created_by != current_user.id and not current_user.is_admin():
        flash("Vous ne pouvez pas revoquer ce lien.", 'danger')
        return redirect(url_for('user.dashboard'))

    link.revoke()
    db.session.commit()

    flash('Lien revoque.', 'success')

    if link.document_id:
        return redirect(url_for('document.share', document_id=link.document_id))
    if link.family_id:
        return redirect(url_for('family.view_family', family_id=link.family_id))

    return redirect(url_for('user.dashboard'))
