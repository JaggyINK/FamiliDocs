# seed bdd donnees demo - python seed_demo_data.py
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime, date, timedelta
from app import create_app
from app.models import db
from app.models.user import User
from app.models.family import Family, FamilyMember, ShareLink
from app.models.folder import Folder
from app.models.document import Document
from app.models.task import Task
from app.models.notification import Notification
from app.models.permission import Permission
from app.models.tag import Tag, document_tags
from app.models.message import Message
from app.services.auth_service import AuthService


def seed():
    """insert data demo"""
    app = create_app('development')

    with app.app_context():
        print("=" * 60)
        print("  FamiliDocs - Insertion des donnees de demonstration")
        print("=" * 60 + "\n")

        # Verifier si les donnees de demo existent deja
        if User.query.filter_by(email='jean.dupont@email.com').first():
            print("Les donnees de demo existent deja. Suppression...")
            _cleanup_demo_data()
            print("Donnees de demo supprimees.\n")

        # Supprimer l'ancien compte admin par defaut s'il existe
        old_admin = User.query.filter_by(email='admin@familidocs.local').first()
        if old_admin:
            Notification.query.filter_by(user_id=old_admin.id).delete()
            db.session.delete(old_admin)
            db.session.commit()
            print("Ancien compte admin@familidocs.local supprime.\n")

        # ================================================================
        # 1. UTILISATEURS
        # Papa et Maman ont le role 'admin' (tous les droits systeme)
        # ================================================================
        print("[1/9] Creation des utilisateurs...")

        papa = User(
            email='jean.dupont@email.com',
            username='jean_dupont',
            password_hash=AuthService.hash_password('Demo2024!'),
            first_name='Jean',
            last_name='Dupont',
            role='admin',
            family_title='Papa',
            is_active=True
        )

        maman = User(
            email='marie.dupont@email.com',
            username='marie_dupont',
            password_hash=AuthService.hash_password('Demo2024!'),
            first_name='Marie',
            last_name='Dupont',
            role='admin',
            family_title='Maman',
            is_active=True
        )

        fils = User(
            email='lucas.dupont@email.com',
            username='lucas_dupont',
            password_hash=AuthService.hash_password('Demo2024!'),
            first_name='Lucas',
            last_name='Dupont',
            role='user',
            family_title='Fils',
            is_active=True
        )

        fille = User(
            email='emma.dupont@email.com',
            username='emma_dupont',
            password_hash=AuthService.hash_password('Demo2024!'),
            first_name='Emma',
            last_name='Dupont',
            role='user',
            family_title='Fille',
            is_active=True
        )

        grandpere = User(
            email='pierre.dupont@email.com',
            username='pierre_dupont',
            password_hash=AuthService.hash_password('Demo2024!'),
            first_name='Pierre',
            last_name='Dupont',
            role='user',
            family_title='Grand-Pere',
            is_active=True
        )

        db.session.add_all([papa, maman, fils, fille, grandpere])
        db.session.commit()
        print("   5 utilisateurs crees")
        print("   -> Jean & Marie = admin (tous les droits)")
        print("   -> Lucas, Emma, Pierre = utilisateur standard")

        # ================================================================
        # 2. DOSSIERS
        # ================================================================
        print("\n[2/9] Creation des dossiers...")

        for user in [papa, maman, fils, fille, grandpere]:
            default_folders = Folder.create_default_folders(user.id)
            for folder in default_folders:
                db.session.add(folder)
        db.session.commit()

        # Sous-dossiers supplementaires
        f_admin_papa = Folder.query.filter_by(owner_id=papa.id, category='Administratif').first()
        f_logement_papa = Folder.query.filter_by(owner_id=papa.id, category='Logement').first()
        f_admin_maman = Folder.query.filter_by(owner_id=maman.id, category='Administratif').first()

        dossier_impots = Folder(
            name='Impots 2024', description='Declarations fiscales 2024',
            category='Administratif', owner_id=papa.id, parent_id=f_admin_papa.id
        )
        dossier_ecole = Folder(
            name='Scolarite Enfants', description='Bulletins, inscriptions, certificats',
            category='Autres', owner_id=maman.id
        )
        dossier_maison = Folder(
            name='Travaux Maison', description='Devis et factures travaux',
            category='Logement', owner_id=papa.id, parent_id=f_logement_papa.id
        )
        dossier_retraite = Folder(
            name='Retraite', description='Documents retraite et pension',
            category='Administratif', owner_id=grandpere.id,
            parent_id=Folder.query.filter_by(owner_id=grandpere.id, category='Administratif').first().id
        )
        db.session.add_all([dossier_impots, dossier_ecole, dossier_maison, dossier_retraite])
        db.session.commit()
        print("   25 dossiers par defaut + 4 sous-dossiers crees")

        # ================================================================
        # 3. DOCUMENTS (20 documents realistes)
        # ================================================================
        print("\n[3/9] Creation des documents...")

        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        documents_data = [
            # ---- PAPA (Jean) ----
            # [0] CNI Jean
            {'name': 'Carte d\'identite Jean', 'original_filename': 'cni_jean_dupont.pdf',
             'stored_filename': 'demo_cni_jean_001.pdf', 'file_type': 'pdf',
             'file_size': 245760, 'description': 'Carte nationale d\'identite - valide jusqu\'au 15/06/2028',
             'confidentiality': 'private', 'owner_id': papa.id,
             'folder_id': f_admin_papa.id, 'expiry_date': date(2028, 6, 15)},
            # [1] Avis imposition
            {'name': 'Avis d\'imposition 2024', 'original_filename': 'avis_imposition_2024.pdf',
             'stored_filename': 'demo_impots_002.pdf', 'file_type': 'pdf',
             'file_size': 512000, 'description': 'Avis d\'imposition sur les revenus 2023 - foyer fiscal',
             'confidentiality': 'restricted', 'owner_id': papa.id,
             'folder_id': dossier_impots.id},
            # [2] Contrat assurance
            {'name': 'Contrat assurance habitation', 'original_filename': 'contrat_assurance_habitation.pdf',
             'stored_filename': 'demo_assurance_003.pdf', 'file_type': 'pdf',
             'file_size': 1048576, 'description': 'Contrat MAIF n.2024-789456 - Habitation principale',
             'confidentiality': 'restricted', 'owner_id': papa.id,
             'folder_id': f_logement_papa.id,
             'expiry_date': date.today() + timedelta(days=45),
             'next_review_date': date.today() + timedelta(days=30)},
            # [3] RIB
            {'name': 'RIB Compte Joint', 'original_filename': 'rib_compte_joint.pdf',
             'stored_filename': 'demo_rib_004.pdf', 'file_type': 'pdf',
             'file_size': 102400, 'description': 'RIB du compte joint Banque Populaire - Jean & Marie',
             'confidentiality': 'restricted', 'owner_id': papa.id,
             'folder_id': Folder.query.filter_by(owner_id=papa.id, category='Banque').first().id},
            # [4] Ordonnance
            {'name': 'Ordonnance Dr. Martin', 'original_filename': 'ordonnance_martin_2024.jpg',
             'stored_filename': 'demo_ordo_005.jpg', 'file_type': 'jpg',
             'file_size': 204800, 'description': 'Ordonnance du 15/01/2024 - Dr. Martin - Jean',
             'confidentiality': 'private', 'owner_id': papa.id,
             'folder_id': Folder.query.filter_by(owner_id=papa.id, category='Sante').first().id},
            # [5] Devis peinture
            {'name': 'Devis peinture salon', 'original_filename': 'devis_peinture_salon.pdf',
             'stored_filename': 'demo_devis_006.pdf', 'file_type': 'pdf',
             'file_size': 358400, 'description': 'Devis Entreprise Martin - Peinture salon et couloir',
             'confidentiality': 'public', 'owner_id': papa.id,
             'folder_id': dossier_maison.id},
            # [6] Facture electricite
            {'name': 'Facture EDF Janvier 2024', 'original_filename': 'facture_edf_jan2024.pdf',
             'stored_filename': 'demo_edf_012.pdf', 'file_type': 'pdf',
             'file_size': 178000, 'description': 'Facture EDF mensuelle - janvier 2024',
             'confidentiality': 'restricted', 'owner_id': papa.id,
             'folder_id': f_logement_papa.id},
            # [7] Permis de conduire
            {'name': 'Permis de conduire Jean', 'original_filename': 'permis_jean.jpg',
             'stored_filename': 'demo_permis_013.jpg', 'file_type': 'jpg',
             'file_size': 320000, 'description': 'Permis B - delivre le 05/03/2010',
             'confidentiality': 'private', 'owner_id': papa.id,
             'folder_id': f_admin_papa.id},

            # ---- MAMAN (Marie) ----
            # [8] CNI Marie
            {'name': 'Carte d\'identite Marie', 'original_filename': 'cni_marie_dupont.pdf',
             'stored_filename': 'demo_cni_marie_007.pdf', 'file_type': 'pdf',
             'file_size': 256000, 'description': 'Carte nationale d\'identite Marie Dupont',
             'confidentiality': 'private', 'owner_id': maman.id,
             'folder_id': f_admin_maman.id, 'expiry_date': date(2029, 3, 20)},
            # [9] Bulletin salaire
            {'name': 'Bulletin de salaire Mars 2024', 'original_filename': 'bulletin_mars_2024.pdf',
             'stored_filename': 'demo_salaire_008.pdf', 'file_type': 'pdf',
             'file_size': 184320, 'description': 'Fiche de paie Mars 2024 - Societe TechCorp',
             'confidentiality': 'private', 'owner_id': maman.id,
             'folder_id': f_admin_maman.id},
            # [10] Carnet sante Lucas
            {'name': 'Carnet de sante Lucas', 'original_filename': 'carnet_sante_lucas.pdf',
             'stored_filename': 'demo_carnet_009.pdf', 'file_type': 'pdf',
             'file_size': 3145728, 'description': 'Carnet de sante numerise - Lucas Dupont - a jour',
             'confidentiality': 'restricted', 'owner_id': maman.id,
             'folder_id': Folder.query.filter_by(owner_id=maman.id, category='Sante').first().id},
            # [11] Contrat travail Marie
            {'name': 'Contrat de travail Marie', 'original_filename': 'contrat_travail_marie.pdf',
             'stored_filename': 'demo_contrat_014.pdf', 'file_type': 'pdf',
             'file_size': 890000, 'description': 'CDI TechCorp - signe le 01/09/2019',
             'confidentiality': 'private', 'owner_id': maman.id,
             'folder_id': f_admin_maman.id},
            # [12] Livret de famille
            {'name': 'Livret de famille', 'original_filename': 'livret_famille.pdf',
             'stored_filename': 'demo_livret_015.pdf', 'file_type': 'pdf',
             'file_size': 1250000, 'description': 'Livret de famille Dupont - tous les membres',
             'confidentiality': 'restricted', 'owner_id': maman.id,
             'folder_id': f_admin_maman.id},

            # ---- FILS (Lucas) ----
            # [13] Bulletin scolaire
            {'name': 'Bulletin scolaire T1 2024', 'original_filename': 'bulletin_t1_2024.pdf',
             'stored_filename': 'demo_bulletin_010.pdf', 'file_type': 'pdf',
             'file_size': 409600, 'description': 'Bulletin du 1er trimestre 2023-2024 - Terminale',
             'confidentiality': 'restricted', 'owner_id': fils.id,
             'folder_id': Folder.query.filter_by(owner_id=fils.id, category='Administratif').first().id},
            # [14] Certificat sport
            {'name': 'Certificat medical sport', 'original_filename': 'certificat_sport.pdf',
             'stored_filename': 'demo_sport_011.pdf', 'file_type': 'pdf',
             'file_size': 153600, 'description': 'Certificat medical pour pratique sportive - Football',
             'confidentiality': 'public', 'owner_id': fils.id,
             'folder_id': Folder.query.filter_by(owner_id=fils.id, category='Sante').first().id,
             'expiry_date': date.today() + timedelta(days=10)},
            # [15] Carte etudiante
            {'name': 'Carte etudiante Lucas', 'original_filename': 'carte_etudiante_lucas.jpg',
             'stored_filename': 'demo_carte_etu_016.jpg', 'file_type': 'jpg',
             'file_size': 198000, 'description': 'Carte etudiante 2023-2024 - Lycee Victor Hugo',
             'confidentiality': 'public', 'owner_id': fils.id,
             'folder_id': Folder.query.filter_by(owner_id=fils.id, category='Administratif').first().id},

            # ---- FILLE (Emma) ----
            # [16] Inscription college
            {'name': 'Inscription college Emma', 'original_filename': 'inscription_college.pdf',
             'stored_filename': 'demo_inscription_017.pdf', 'file_type': 'pdf',
             'file_size': 345000, 'description': 'Dossier inscription College Pasteur - 4eme',
             'confidentiality': 'restricted', 'owner_id': fille.id,
             'folder_id': Folder.query.filter_by(owner_id=fille.id, category='Administratif').first().id},
            # [17] Carnet sante Emma
            {'name': 'Carnet de sante Emma', 'original_filename': 'carnet_sante_emma.pdf',
             'stored_filename': 'demo_carnet_emma_018.pdf', 'file_type': 'pdf',
             'file_size': 2800000, 'description': 'Carnet de sante numerise - Emma Dupont',
             'confidentiality': 'private', 'owner_id': fille.id,
             'folder_id': Folder.query.filter_by(owner_id=fille.id, category='Sante').first().id},

            # ---- GRAND-PERE (Pierre) ----
            # [18] Carte retraite
            {'name': 'Attestation retraite CNAV', 'original_filename': 'attestation_retraite.pdf',
             'stored_filename': 'demo_retraite_019.pdf', 'file_type': 'pdf',
             'file_size': 420000, 'description': 'Attestation de droits pension de retraite 2024',
             'confidentiality': 'private', 'owner_id': grandpere.id,
             'folder_id': dossier_retraite.id,
             'next_review_date': date.today() + timedelta(days=60)},
            # [19] Carte vitale
            {'name': 'Carte Vitale Pierre', 'original_filename': 'carte_vitale_pierre.jpg',
             'stored_filename': 'demo_vitale_020.jpg', 'file_type': 'jpg',
             'file_size': 180000, 'description': 'Carte Vitale de Pierre Dupont',
             'confidentiality': 'private', 'owner_id': grandpere.id,
             'folder_id': Folder.query.filter_by(owner_id=grandpere.id, category='Sante').first().id},
        ]

        created_docs = []
        for doc_data in documents_data:
            doc = Document(**doc_data)
            db.session.add(doc)
            created_docs.append(doc)

            # Fichier physique placeholder
            filepath = os.path.join(upload_folder, doc_data['stored_filename'])
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{'=' * 50}\n")
                    f.write(f"  DOCUMENT DE DEMONSTRATION - FamiliDocs\n")
                    f.write(f"{'=' * 50}\n\n")
                    f.write(f"Nom        : {doc_data['name']}\n")
                    f.write(f"Fichier    : {doc_data['original_filename']}\n")
                    f.write(f"Format     : {doc_data['file_type'].upper()}\n")
                    f.write(f"Taille     : {doc_data['file_size'] // 1024} Ko\n")
                    f.write(f"Acces      : {doc_data['confidentiality']}\n\n")
                    f.write(f"Description :\n{doc_data['description']}\n\n")
                    f.write(f"Ce fichier est un placeholder pour la demonstration.\n")
                    f.write(f"En production, il s'agirait du vrai document numerise.\n")

        db.session.commit()
        print(f"   {len(created_docs)} documents crees avec fichiers physiques")

        # ================================================================
        # 4. FAMILLE
        # ================================================================
        print("\n[4/9] Creation de la famille Dupont...")

        famille = Family(
            name='Famille Dupont',
            description='Espace collaboratif de la famille Dupont pour la gestion centralisee des documents administratifs.',
            creator_id=papa.id
        )
        db.session.add(famille)
        db.session.commit()

        members_data = [
            (papa.id, 'responsable', None),
            (maman.id, 'responsable', papa.id),
            (fils.id, 'enfant', papa.id),
            (fille.id, 'enfant', maman.id),
            (grandpere.id, 'lecteur', papa.id),
        ]
        for user_id, role, invited_by in members_data:
            db.session.add(FamilyMember(
                family_id=famille.id, user_id=user_id,
                role=role, invited_by=invited_by
            ))
        db.session.commit()
        print("   Famille 'Dupont' : 2 responsables, 2 enfants, 1 lecteur")

        # ================================================================
        # 5. PARTAGES (Permissions croisees entre membres)
        # ================================================================
        print("\n[5/9] Creation des partages entre membres...")

        permissions_data = [
            # --- Papa partage avec Maman (couple, acces complet) ---
            # Avis imposition -> Marie (edit + download + share)
            (created_docs[1].id, maman.id, papa.id, True, True, True, None,
             'Document fiscal commun - acces complet couple'),
            # Contrat assurance -> Marie (edit + download)
            (created_docs[2].id, maman.id, papa.id, True, True, False, None,
             'Contrat commun habitation'),
            # RIB compte joint -> Marie (download)
            (created_docs[3].id, maman.id, papa.id, False, True, False, None,
             'RIB du compte joint'),
            # Devis peinture -> Marie (edit, elle peut commenter)
            (created_docs[5].id, maman.id, papa.id, True, True, False, None,
             'Travaux maison - consultation couple'),
            # Facture EDF -> Marie
            (created_docs[6].id, maman.id, papa.id, False, True, False, None,
             'Facture mensuelle partagee'),

            # --- Papa partage avec Lucas (pere -> fils, lecture seule) ---
            # RIB pour inscription sport
            (created_docs[3].id, fils.id, papa.id, False, True, False,
             date.today() + timedelta(days=30),
             'RIB pour inscription club de foot - acces temporaire'),
            # Devis peinture (Lucas aide a la maison)
            (created_docs[5].id, fils.id, papa.id, False, False, False, None,
             'Consultation devis travaux'),

            # --- Maman partage avec les enfants ---
            # Carnet sante Lucas -> Lucas (il peut consulter son propre carnet)
            (created_docs[10].id, fils.id, maman.id, False, True, False, None,
             'Lucas peut consulter son carnet de sante'),
            # Livret de famille -> toute la famille
            (created_docs[12].id, papa.id, maman.id, False, True, False, None,
             'Livret de famille - consultation Jean'),
            (created_docs[12].id, fils.id, maman.id, False, False, False, None,
             'Livret de famille - consultation Lucas'),
            (created_docs[12].id, fille.id, maman.id, False, False, False, None,
             'Livret de famille - consultation Emma'),
            (created_docs[12].id, grandpere.id, maman.id, False, False, False, None,
             'Livret de famille - consultation Pierre'),

            # --- Grand-Pere partage avec Emma (lien special) ---
            # Attestation retraite -> Emma (elle l'aide pour ses papiers)
            (created_docs[18].id, fille.id, grandpere.id, False, True, False,
             date.today() + timedelta(days=60),
             'Emma aide Pierre pour ses demarches administratives'),
            # Carte vitale -> Emma
            (created_docs[19].id, fille.id, grandpere.id, False, False, False,
             date.today() + timedelta(days=60),
             'Consultation en cas d\'urgence medicale'),

            # --- Papa partage avec Grand-Pere ---
            # Contrat assurance -> Grand-Pere (il vit avec eux)
            (created_docs[2].id, grandpere.id, papa.id, False, True, False, None,
             'Pierre vit au domicile - besoin du contrat assurance'),

            # --- Lucas partage bulletin avec parents ---
            # Bulletin scolaire -> Papa
            (created_docs[13].id, papa.id, fils.id, False, True, False, None,
             'Suivi scolaire - consultation parent'),
            # Bulletin scolaire -> Maman
            (created_docs[13].id, maman.id, fils.id, False, True, False, None,
             'Suivi scolaire - consultation parent'),

            # --- Fille partage inscription avec Maman ---
            # Inscription college -> Maman (elle gere l'administratif)
            (created_docs[16].id, maman.id, fille.id, True, True, False, None,
             'Marie gere les inscriptions scolaires'),
            # Carnet sante Emma -> Maman
            (created_docs[17].id, maman.id, fille.id, False, True, False, None,
             'Acces parental au carnet de sante'),
        ]

        perm_count = 0
        for doc_id, user_id, granted_by, can_edit, can_dl, can_share, end_date, notes in permissions_data:
            perm = Permission(
                document_id=doc_id, user_id=user_id, granted_by=granted_by,
                can_view=True, can_edit=can_edit, can_download=can_dl,
                can_share=can_share, end_date=end_date, notes=notes
            )
            db.session.add(perm)
            perm_count += 1
        db.session.commit()
        print(f"   {perm_count} partages crees :")
        print("   -> Papa <-> Maman : 5 docs (acces complet couple)")
        print("   -> Papa  -> Lucas : 2 docs (RIB temporaire + devis)")
        print("   -> Maman -> Enfants : carnet sante, livret famille")
        print("   -> Livret famille -> tous les membres (4 partages)")
        print("   -> Grand-Pere <-> Emma : 2 docs (aide administrative)")
        print("   -> Papa -> Grand-Pere : assurance habitation")
        print("   -> Lucas -> Parents : bulletin scolaire")
        print("   -> Emma -> Maman : inscription + carnet sante")

        # ================================================================
        # 6. TACHES
        # ================================================================
        print("\n[6/9] Creation des taches...")

        tasks_data = [
            {'title': 'Renouveler assurance habitation',
             'description': 'Le contrat MAIF arrive a echeance dans 45 jours. Comparer les offres.',
             'due_date': date.today() + timedelta(days=30), 'priority': 'high',
             'status': 'pending', 'owner_id': papa.id,
             'document_id': created_docs[2].id, 'reminder_days': 14},

            {'title': 'Declaration impots 2024',
             'description': 'Rassembler tous les justificatifs et declarer en ligne sur impots.gouv.fr.',
             'due_date': date.today() + timedelta(days=60), 'priority': 'urgent',
             'status': 'in_progress', 'owner_id': papa.id,
             'document_id': created_docs[1].id, 'assigned_to_id': maman.id},

            {'title': 'Renouveler certificat medical Lucas',
             'description': 'Prendre RDV chez le Dr. Martin pour renouveler le certificat sportif.',
             'due_date': date.today() + timedelta(days=7), 'priority': 'normal',
             'status': 'pending', 'owner_id': maman.id,
             'document_id': created_docs[14].id, 'assigned_to_id': fils.id},

            {'title': 'Transmettre RIB a l\'ecole',
             'description': 'Fournir le RIB pour la cantine et les sorties scolaires.',
             'due_date': date.today() + timedelta(days=3), 'priority': 'normal',
             'status': 'pending', 'owner_id': papa.id,
             'document_id': created_docs[3].id},

            {'title': 'Rappeler le peintre',
             'description': 'Appeler l\'entreprise Martin pour confirmer la date des travaux.',
             'due_date': date.today() - timedelta(days=2), 'priority': 'low',
             'status': 'pending', 'owner_id': papa.id,
             'document_id': created_docs[5].id},

            {'title': 'Vaccins Emma - rappel annuel',
             'description': 'Verifier les rappels de vaccination et prendre RDV pediatre.',
             'due_date': date.today() + timedelta(days=14), 'priority': 'normal',
             'status': 'pending', 'owner_id': maman.id,
             'document_id': created_docs[17].id},

            {'title': 'Aider Grand-Pere : scanner ses documents',
             'description': 'Numeriser les documents administratifs de Pierre (retraite, mutuelle).',
             'due_date': date.today() + timedelta(days=21), 'priority': 'low',
             'status': 'pending', 'owner_id': fille.id,
             'assigned_to_id': fille.id},

            {'title': 'Renouveler inscription foot Lucas',
             'description': 'Inscription saison 2024-2025, certificat medical obligatoire.',
             'due_date': date.today() + timedelta(days=45), 'priority': 'normal',
             'status': 'pending', 'owner_id': fils.id,
             'document_id': created_docs[14].id},

            {'title': 'Mise a jour dossier retraite',
             'description': 'Verifier le releve de carriere et envoyer les corrections a la CNAV.',
             'due_date': date.today() + timedelta(days=60), 'priority': 'normal',
             'status': 'pending', 'owner_id': grandpere.id,
             'document_id': created_docs[18].id},
        ]
        for task_data in tasks_data:
            db.session.add(Task(**task_data))
        db.session.commit()
        print(f"   {len(tasks_data)} taches (1 en retard, 1 en cours, 7 en attente)")

        # ================================================================
        # 7. TAGS
        # ================================================================
        print("\n[7/9] Creation des tags...")

        tags_data = [
            ('Urgent', '#dc3545', papa.id),
            ('A renouveler', '#fd7e14', papa.id),
            ('Fiscal', '#198754', papa.id),
            ('Medical', '#0dcaf0', maman.id),
            ('Scolaire', '#6f42c1', maman.id),
            ('Important', '#ffc107', papa.id),
            ('Archive', '#6c757d', grandpere.id),
            ('Couple', '#e91e8c', maman.id),
        ]
        created_tags = []
        for name, color, owner_id in tags_data:
            tag = Tag(name=name, color=color, owner_id=owner_id)
            db.session.add(tag)
            created_tags.append(tag)
        db.session.commit()

        tag_links = [
            (created_docs[0].id, created_tags[1].id),   # CNI Jean -> A renouveler
            (created_docs[1].id, created_tags[2].id),   # Impots -> Fiscal
            (created_docs[1].id, created_tags[5].id),   # Impots -> Important
            (created_docs[2].id, created_tags[0].id),   # Assurance -> Urgent
            (created_docs[2].id, created_tags[1].id),   # Assurance -> A renouveler
            (created_docs[3].id, created_tags[7].id),   # RIB -> Couple
            (created_docs[4].id, created_tags[3].id),   # Ordonnance -> Medical
            (created_docs[10].id, created_tags[3].id),  # Carnet Lucas -> Medical
            (created_docs[12].id, created_tags[5].id),  # Livret famille -> Important
            (created_docs[12].id, created_tags[7].id),  # Livret famille -> Couple
            (created_docs[13].id, created_tags[4].id),  # Bulletin -> Scolaire
            (created_docs[14].id, created_tags[3].id),  # Certif sport -> Medical
            (created_docs[16].id, created_tags[4].id),  # Inscription -> Scolaire
            (created_docs[17].id, created_tags[3].id),  # Carnet Emma -> Medical
            (created_docs[18].id, created_tags[6].id),  # Retraite -> Archive
        ]
        for doc_id, tag_id in tag_links:
            db.session.execute(document_tags.insert().values(document_id=doc_id, tag_id=tag_id))
        db.session.commit()
        print(f"   {len(created_tags)} tags, {len(tag_links)} associations")

        # ================================================================
        # 8. MESSAGES CHAT FAMILIAL
        # ================================================================
        print("\n[8/9] Creation des messages...")

        messages = [
            (papa.id, "Bonjour a tous ! J'ai ajoute les documents d'impots et l'assurance sur FamiliDocs.", False),
            (maman.id, "Merci Jean ! J'ai mis le carnet de sante de Lucas et le livret de famille.", False),
            (maman.id, "J'ai partage le livret de famille avec tout le monde, vous pouvez le consulter.", False),
            (fils.id, "Papa, j'ai besoin du RIB pour l'inscription au foot, tu peux le partager ?", False),
            (papa.id, "C'est fait Lucas, je t'ai donne l'acces au RIB pour 30 jours.", False),
            (papa.id, "RAPPEL : La declaration d'impots est a faire avant fin mai. Marie, je t'ai assigne la tache.", True),
            (maman.id, "Lucas, ton certificat medical expire dans 10 jours ! Prends RDV chez le Dr. Martin.", False),
            (grandpere.id, "Est-ce que quelqu'un peut m'aider a scanner mes documents de retraite ?", False),
            (fille.id, "Moi je veux bien aider grand-pere ! Je passe ce week-end.", False),
            (papa.id, "Super Emma ! Grand-Pere, elle va t'aider. Je t'ai deja partage l'assurance habitation au cas ou.", False),
            (grandpere.id, "Merci Jean, merci Emma ! C'est pratique cette application.", False),
            (papa.id, "IMPORTANT : J'ai partage le contrat d'assurance avec Marie et Grand-Pere.", True),
            (maman.id, "Emma, j'ai acces a ton inscription college et ton carnet de sante. Si tu as besoin de quelque chose, dis-le moi.", False),
            (fille.id, "D'accord maman ! Merci.", False),
        ]
        for i, (sender_id, content, is_ann) in enumerate(messages):
            db.session.add(Message(
                family_id=famille.id, sender_id=sender_id,
                content=content, is_announcement=is_ann,
                created_at=datetime.utcnow() - timedelta(hours=len(messages) - i)
            ))
        db.session.commit()
        print(f"   {len(messages)} messages (dont 2 annonces)")

        # ================================================================
        # 9. NOTIFICATIONS
        # ================================================================
        print("\n[9/9] Creation des notifications...")

        notifs = [
            (papa.id, 'document_expiry', 'Assurance habitation expire bientot',
             'Le contrat d\'assurance MAIF expire dans 45 jours. Pensez a le renouveler.', 'high'),
            (papa.id, 'task_overdue', 'Rappeler le peintre - EN RETARD',
             'La tache "Rappeler le peintre" est en retard de 2 jours.', 'urgent'),
            (maman.id, 'task_due', 'Certificat medical Lucas',
             'Le certificat medical sportif de Lucas expire dans 10 jours.', 'normal'),
            (maman.id, 'document_shared', 'Nouveau document partage',
             'Jean a partage "Avis d\'imposition 2024" avec vous.', 'normal'),
            (fils.id, 'task_assigned', 'Tache assignee',
             'Marie vous a assigne la tache "Renouveler certificat medical".', 'normal'),
            (fils.id, 'permission_granted', 'Acces accorde : RIB',
             'Jean vous a accorde l\'acces au RIB du compte joint (temporaire, 30 jours).', 'normal'),
            (fille.id, 'document_shared', 'Nouveau document partage',
             'Pierre a partage "Attestation retraite CNAV" avec vous.', 'normal'),
            (fille.id, 'task_assigned', 'Tache assignee',
             'Vous etes assignee a "Aider Grand-Pere : scanner ses documents".', 'low'),
            (grandpere.id, 'welcome', 'Bienvenue Pierre !',
             'Bienvenue sur FamiliDocs ! Vos enfants ont partage des documents avec vous.', 'low'),
            (grandpere.id, 'permission_granted', 'Acces accorde : Assurance',
             'Jean vous a accorde l\'acces au contrat d\'assurance habitation.', 'normal'),
        ]
        for uid, ntype, title, msg, prio in notifs:
            db.session.add(Notification(
                user_id=uid, type=ntype, title=title, message=msg, priority=prio
            ))
        db.session.commit()
        print(f"   {len(notifs)} notifications")

        # ================================================================
        # RESUME FINAL
        # ================================================================
        print("\n" + "=" * 60)
        print("  DONNEES DE DEMONSTRATION INSEREES AVEC SUCCES !")
        print("=" * 60)
        print("""
  COMPTES UTILISATEURS
  +----------------------------+------------+---------------+
  | Email                      | Mot de passe | Role systeme |
  +----------------------------+------------+---------------+
  | jean.dupont@email.com      | Demo2024!  | Admin (Papa)   |
  | marie.dupont@email.com     | Demo2024!  | Admin (Maman)  |
  | lucas.dupont@email.com     | Demo2024!  | Utilisateur    |
  | emma.dupont@email.com      | Demo2024!  | Utilisateur    |
  | pierre.dupont@email.com    | Demo2024!  | Utilisateur    |
  +----------------------------+------------+---------------+

  FAMILLE DUPONT
  Jean (Responsable) + Marie (Responsable)
  Lucas (Enfant) + Emma (Enfant) + Pierre (Lecteur)

  PARTAGES ACTIFS
  Papa <-> Maman     : impots, assurance, RIB, devis, EDF
  Papa  -> Lucas     : RIB (temporaire 30j), devis
  Maman -> Lucas     : carnet de sante
  Maman -> Tous      : livret de famille (4 partages)
  Grand-Pere -> Emma : retraite, carte vitale (60j)
  Papa -> Grand-Pere : assurance habitation
  Lucas -> Parents   : bulletin scolaire
  Emma  -> Maman     : inscription college, carnet sante
""")
        print(f"  {len(created_docs)} documents | {len(tasks_data)} taches | {perm_count} partages")
        print(f"  {len(created_tags)} tags | {len(messages)} messages | {len(notifs)} notifications")
        print()


def _cleanup_demo_data():
    """Supprime les donnees de demo existantes"""
    demo_emails = [
        'jean.dupont@email.com', 'marie.dupont@email.com',
        'lucas.dupont@email.com', 'emma.dupont@email.com',
        'pierre.dupont@email.com'
    ]
    for email in demo_emails:
        user = User.query.filter_by(email=email).first()
        if user:
            Notification.query.filter_by(user_id=user.id).delete()
            Tag.query.filter_by(owner_id=user.id).delete()
            # Supprimer les permissions ou l'user est implique
            Permission.query.filter_by(user_id=user.id).delete()
            Permission.query.filter_by(granted_by=user.id).delete()
            db.session.delete(user)

    famille = Family.query.filter_by(name='Famille Dupont').first()
    if famille:
        Message.query.filter_by(family_id=famille.id).delete()
        FamilyMember.query.filter_by(family_id=famille.id).delete()
        ShareLink.query.filter_by(family_id=famille.id).delete()
        db.session.delete(famille)

    db.session.commit()

    upload_folder = os.path.join(os.path.dirname(__file__), 'app', 'database', 'uploads')
    if os.path.exists(upload_folder):
        for f in os.listdir(upload_folder):
            if f.startswith('demo_'):
                os.remove(os.path.join(upload_folder, f))


if __name__ == '__main__':
    seed()
