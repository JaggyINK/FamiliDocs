"""
FamiliDocs - Application Desktop Native Professionnelle
Base de donnees chiffree locale + Interface Pro + RGPD
"""
import os
import sys
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime, date, timedelta
from PIL import Image
import threading
import json
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ============================================================================
# CONFIGURATION ET CHEMINS
# ============================================================================

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def setup_environment():
    base_path = get_base_path()
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    # Charger .env AVANT de configurer les chemins
    from dotenv import load_dotenv
    load_dotenv(os.path.join(base_path, '.env'))

    # Dossier de donnees (uploads, backups, cles)
    # La BDD est toujours PostgreSQL (partagee web + desktop)
    user_data_dir = os.path.join(base_path, 'app', 'database')

    os.environ['FAMILIDOCS_UPLOAD_FOLDER'] = os.path.join(user_data_dir, 'uploads')
    os.environ['FAMILIDOCS_BACKUP_FOLDER'] = os.path.join(user_data_dir, 'backups')
    os.environ['FAMILIDOCS_DOCS_FOLDER'] = os.path.join(user_data_dir, 'documents')

    for folder in ['uploads', 'uploads/avatars', 'backups', 'exports', 'documents']:
        os.makedirs(os.path.join(user_data_dir, folder), exist_ok=True)

    return user_data_dir

USER_DATA_DIR = setup_environment()

# Imports application
from app import create_app
from app.models import db, User, Document, Folder, Task, Family, Notification

# ============================================================================
# CHIFFREMENT LOCAL
# ============================================================================

class LocalEncryption:
    """Gestionnaire de chiffrement local pour les donnees sensibles"""

    _instance = None
    _key = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.key_file = os.path.join(USER_DATA_DIR, '.encryption_key')
        self._init_key()

    def _init_key(self):
        """Initialise ou charge la cle de chiffrement"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self._key = f.read()
        else:
            # Generer une nouvelle cle basee sur l'identifiant machine
            machine_id = self._get_machine_id()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self._key = salt + key

            # Sauvegarder la cle
            with open(self.key_file, 'wb') as f:
                f.write(self._key)

            # Proteger le fichier (Windows)
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.key_file, 2)  # Hidden
            except:
                pass

    def _get_machine_id(self):
        """Obtient un identifiant unique de la machine"""
        import platform
        import uuid
        return f"{platform.node()}-{uuid.getnode()}"

    def get_fernet(self):
        """Retourne l'instance Fernet pour chiffrer/dechiffrer"""
        salt = self._key[:16]
        key = self._key[16:]
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """Chiffre une chaine de caracteres"""
        if not data:
            return data
        f = self.get_fernet()
        return f.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Dechiffre une chaine de caracteres"""
        if not encrypted_data:
            return encrypted_data
        try:
            f = self.get_fernet()
            return f.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data


# ============================================================================
# THEME PROFESSIONNEL SOMBRE
# ============================================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palette professionnelle
THEME = {
    # Backgrounds
    'bg_primary': '#0D1117',
    'bg_secondary': '#161B22',
    'bg_tertiary': '#21262D',
    'bg_elevated': '#30363D',
    'bg_hover': '#484F58',
    'bg_active': '#1F6FEB',

    # Borders
    'border': '#30363D',
    'border_light': '#484F58',
    'border_focus': '#58A6FF',

    # Text
    'text_primary': '#E6EDF3',
    'text_secondary': '#8B949E',
    'text_muted': '#6E7681',
    'text_link': '#58A6FF',

    # Accent
    'accent': '#1F6FEB',
    'accent_hover': '#388BFD',
    'accent_muted': '#1F6FEB40',

    # Semantic
    'success': '#238636',
    'success_text': '#3FB950',
    'warning': '#9E6A03',
    'warning_text': '#D29922',
    'error': '#DA3633',
    'error_text': '#F85149',
    'info': '#1F6FEB',

    # Special
    'purple': '#8957E5',
    'pink': '#DB61A2',
    'orange': '#F0883E',
    'cyan': '#39C5CF',
}

# Icones professionnelles (caracteres Unicode)
ICONS = {
    'dashboard': '\u2302',      # Home
    'documents': '\u2630',      # Menu/Docs
    'tasks': '\u2611',          # Checkbox
    'family': '\u263A',         # Users
    'notifications': '\u2709',  # Envelope
    'profile': '\u2699',        # Settings/User
    'lock': '\u26BF',           # Lock
    'admin': '\u2699',          # Gear
    'add': '+',
    'search': '\u2315',         # Search
    'edit': '\u270E',           # Edit
    'delete': '\u2715',         # X
    'check': '\u2713',          # Check
    'warning': '\u26A0',        # Warning
    'info': '\u2139',           # Info
    'calendar': '\u2637',       # Calendar
    'file': '\u2637',           # File
    'folder': '\u2630',         # Folder
    'download': '\u2913',       # Download
    'upload': '\u2912',         # Upload
    'logout': '\u2192',         # Arrow right
    'back': '\u2190',           # Arrow left
    'settings': '\u2699',       # Gear
    'star': '\u2605',           # Star
    'clock': '\u25F4',          # Clock
}


# ============================================================================
# TEXTES RGPD
# ============================================================================

RGPD_TEXTS = {
    'privacy_policy': """
POLITIQUE DE CONFIDENTIALITE - FamiliDocs
Conformement au RGPD (Reglement UE 2016/679) et a la loi Informatique et Libertes

1. RESPONSABLE DU TRAITEMENT
FamiliDocs est une application de gestion documentaire familiale.
Toutes vos donnees sont stockees LOCALEMENT et CHIFFREES sur votre ordinateur.

2. DONNEES COLLECTEES
- Informations de compte : nom, prenom, email, mot de passe (chiffre)
- Documents : fichiers que vous choisissez d'ajouter (chiffres)
- Taches et rappels : informations que vous saisissez
- Journaux d'activite : pour votre securite

3. SECURITE DES DONNEES
- Chiffrement AES-256 de toutes les donnees sensibles
- Cle de chiffrement unique par installation
- Stockage 100% local (aucun cloud, aucun serveur externe)
- Mot de passe hashe avec bcrypt

4. VOS DROITS (Articles 15 a 22 du RGPD)
- Droit d'acces : consulter vos donnees
- Droit de rectification : modifier vos informations
- Droit a l'effacement : supprimer votre compte et donnees
- Droit a la portabilite : exporter vos donnees

Derniere mise a jour : {date}
""",
    'consent_text': """En creant un compte, vous acceptez le traitement de vos donnees
conformement au RGPD et a notre politique de confidentialite.

Vos donnees sont CHIFFREES et stockees UNIQUEMENT sur cet ordinateur.
Aucune donnee n'est transmise a des serveurs externes.""",
}


# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

class FamiliDocsApp(ctk.CTk):
    """Application principale FamiliDocs"""

    def __init__(self):
        super().__init__()

        self.title("FamiliDocs")
        self.geometry("1300x850")
        self.minsize(1100, 700)
        self.configure(fg_color=THEME['bg_primary'])

        # Initialiser le chiffrement
        self.encryption = LocalEncryption.get_instance()

        # Base de donnees
        self.setup_database()

        # Utilisateur connecte
        self.current_user = None

        # Container principal
        self.container = ctk.CTkFrame(self, fg_color=THEME['bg_primary'])
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def setup_database(self):
        self.flask_app = create_app()
        self.app_context = self.flask_app.app_context()
        self.app_context.push()
        db.create_all()
        self.db_session = db.session
        self.create_default_admin()

    def create_default_admin(self):
        admin = self.db_session.query(User).filter_by(email='admin@familidocs.local').first()
        if not admin:
            from bcrypt import hashpw, gensalt
            admin = User(
                email='admin@familidocs.local',
                first_name='Administrateur',
                last_name='Systeme',
                role='admin',
                is_active=True
            )
            admin.password_hash = hashpw('Admin123!'.encode(), gensalt()).decode()
            self.db_session.add(admin)
            self.db_session.commit()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_container()
        LoginFrame(self.container, self).pack(fill="both", expand=True)

    def show_register(self):
        self.clear_container()
        RegisterFrame(self.container, self).pack(fill="both", expand=True)

    def show_dashboard(self):
        self.clear_container()
        MainFrame(self.container, self).pack(fill="both", expand=True)

    def logout(self):
        self.current_user = None
        self.show_login()


# ============================================================================
# COMPOSANTS UI PROFESSIONNELS
# ============================================================================

class ProButton(ctk.CTkButton):
    """Bouton professionnel"""
    def __init__(self, master, text, command=None, variant="primary", icon=None, **kwargs):

        variants = {
            'primary': {'fg_color': THEME['accent'], 'hover_color': THEME['accent_hover'], 'text_color': '#FFFFFF'},
            'secondary': {'fg_color': THEME['bg_tertiary'], 'hover_color': THEME['bg_hover'], 'text_color': THEME['text_primary']},
            'success': {'fg_color': THEME['success'], 'hover_color': '#2EA043', 'text_color': '#FFFFFF'},
            'danger': {'fg_color': THEME['error'], 'hover_color': '#F85149', 'text_color': '#FFFFFF'},
            'ghost': {'fg_color': 'transparent', 'hover_color': THEME['bg_tertiary'], 'text_color': THEME['text_secondary']},
            'link': {'fg_color': 'transparent', 'hover_color': 'transparent', 'text_color': THEME['text_link']},
        }

        style = variants.get(variant, variants['primary'])
        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            master,
            text=display_text,
            command=command,
            corner_radius=6,
            height=36,
            font=ctk.CTkFont(size=13),
            **style,
            **kwargs
        )


class ProEntry(ctk.CTkEntry):
    """Champ de saisie professionnel"""
    def __init__(self, master, placeholder="", show=None, **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            show=show,
            height=40,
            corner_radius=6,
            border_width=1,
            fg_color=THEME['bg_tertiary'],
            border_color=THEME['border'],
            text_color=THEME['text_primary'],
            placeholder_text_color=THEME['text_muted'],
            font=ctk.CTkFont(size=13),
            **kwargs
        )
        self.bind("<FocusIn>", lambda e: self.configure(border_color=THEME['border_focus']))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=THEME['border']))


class ProCard(ctk.CTkFrame):
    """Card professionnelle"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=THEME['bg_secondary'],
            corner_radius=8,
            border_width=1,
            border_color=THEME['border'],
            **kwargs
        )


class StatCard(ctk.CTkFrame):
    """Card de statistique cliquable"""
    def __init__(self, master, title, value, subtitle="", icon="", color=None, command=None, **kwargs):
        super().__init__(master, fg_color=THEME['bg_secondary'], corner_radius=8, border_width=1, border_color=THEME['border'], **kwargs)

        self.command = command
        self.default_border = THEME['border']

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=20, pady=18, fill="both", expand=True)

        # Header avec icone
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        if icon:
            ctk.CTkLabel(header, text=icon, font=ctk.CTkFont(size=16), text_color=THEME['text_secondary']).pack(side="left")

        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="left", padx=(8 if icon else 0, 0))

        # Valeur
        value_color = color if color else THEME['text_primary']
        ctk.CTkLabel(inner, text=str(value), font=ctk.CTkFont(size=28, weight="bold"), text_color=value_color).pack(anchor="w", pady=(8, 2))

        # Sous-titre
        if subtitle:
            ctk.CTkLabel(inner, text=subtitle, font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(anchor="w")

        # Rendre cliquable
        if command:
            self.configure(cursor="hand2")
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", lambda e: command())
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: command())
                for subchild in child.winfo_children():
                    subchild.bind("<Button-1>", lambda e: command())

    def _on_enter(self, e):
        self.configure(border_color=THEME['border_focus'])

    def _on_leave(self, e):
        self.configure(border_color=self.default_border)


class NavButton(ctk.CTkButton):
    """Bouton de navigation sidebar"""
    def __init__(self, master, text, icon="", command=None, active=False, **kwargs):
        fg = THEME['bg_active'] if active else 'transparent'
        text_color = '#FFFFFF' if active else THEME['text_secondary']

        display_text = f"  {icon}   {text}" if icon else f"  {text}"

        super().__init__(
            master,
            text=display_text,
            command=command,
            anchor="w",
            height=40,
            corner_radius=6,
            fg_color=fg,
            hover_color=THEME['bg_tertiary'] if not active else THEME['accent_hover'],
            text_color=text_color,
            font=ctk.CTkFont(size=13),
            **kwargs
        )


# ============================================================================
# ECRAN DE CONNEXION
# ============================================================================

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        # Layout deux colonnes
        left = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], width=480)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = ctk.CTkFrame(self, fg_color=THEME['bg_primary'])
        right.pack(side="right", fill="both", expand=True)

        # === GAUCHE - Branding ===
        brand = ctk.CTkFrame(left, fg_color="transparent")
        brand.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        logo = ctk.CTkFrame(brand, fg_color=THEME['accent'], width=64, height=64, corner_radius=16)
        logo.pack()
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="FD", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(brand, text="FamiliDocs", font=ctk.CTkFont(size=32, weight="bold"), text_color=THEME['text_primary']).pack(pady=(20, 4))
        ctk.CTkLabel(brand, text="Coffre-fort documentaire familial", font=ctk.CTkFont(size=13), text_color=THEME['text_secondary']).pack()

        # Features
        features = ctk.CTkFrame(brand, fg_color="transparent")
        features.pack(pady=40)

        feature_list = [
            (ICONS['lock'], "Donnees chiffrees localement"),
            (ICONS['family'], "Partage familial securise"),
            (ICONS['tasks'], "Gestion des echeances"),
            (ICONS['check'], "Conforme RGPD / CNIL"),
        ]

        for icon, text in feature_list:
            row = ctk.CTkFrame(features, fg_color="transparent")
            row.pack(anchor="w", pady=6)
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=14), text_color=THEME['success_text']).pack(side="left")
            ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="left", padx=12)

        # Version
        ctk.CTkLabel(brand, text="Version 2.1 - Chiffrement AES-256", font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(pady=(30, 0))

        # === DROITE - Formulaire ===
        form_container = ctk.CTkFrame(right, fg_color="transparent")
        form_container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(form_container, text="Connexion", font=ctk.CTkFont(size=26, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(form_container, text="Accedez a votre espace securise", font=ctk.CTkFont(size=13), text_color=THEME['text_secondary']).pack(anchor="w", pady=(4, 28))

        # Email
        ctk.CTkLabel(form_container, text="Adresse email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email_entry = ProEntry(form_container, placeholder="vous@exemple.com", width=340)
        self.email_entry.pack(pady=(0, 16))

        # Mot de passe
        ctk.CTkLabel(form_container, text="Mot de passe", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.password_entry = ProEntry(form_container, placeholder="Votre mot de passe", show="*", width=340)
        self.password_entry.pack(pady=(0, 24))

        # Boutons
        ProButton(form_container, text="Se connecter", command=self.login, variant="primary", width=340).pack(pady=(0, 12))

        # Separator
        sep = ctk.CTkFrame(form_container, fg_color="transparent", width=340)
        sep.pack(pady=8)
        ctk.CTkFrame(sep, fg_color=THEME['border'], height=1, width=140).pack(side="left")
        ctk.CTkLabel(sep, text="ou", text_color=THEME['text_muted'], font=ctk.CTkFont(size=11)).pack(side="left", padx=12)
        ctk.CTkFrame(sep, fg_color=THEME['border'], height=1, width=140).pack(side="left")

        ProButton(form_container, text="Creer un compte", command=self.app.show_register, variant="ghost", width=340).pack(pady=8)

        # Erreur
        self.error_label = ctk.CTkLabel(form_container, text="", text_color=THEME['error_text'], font=ctk.CTkFont(size=12))
        self.error_label.pack(pady=12)

        # Info securite
        security_frame = ctk.CTkFrame(form_container, fg_color=THEME['bg_tertiary'], corner_radius=6)
        security_frame.pack(pady=(16, 0))
        ctk.CTkLabel(security_frame, text=f"{ICONS['lock']}  Connexion securisee - Donnees chiffrees localement", font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(padx=16, pady=10)

        self.password_entry.bind("<Return>", lambda e: self.login())

    def verify_password(self, password, password_hash):
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except:
            return False

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email or not password:
            self.error_label.configure(text=f"{ICONS['warning']}  Veuillez remplir tous les champs")
            return

        user = self.app.db_session.query(User).filter_by(email=email).first()

        if user and self.verify_password(password, user.password_hash):
            if not user.is_active:
                self.error_label.configure(text=f"{ICONS['warning']}  Ce compte est desactive")
                return
            self.app.current_user = user
            self.app.show_dashboard()
        else:
            self.error_label.configure(text=f"{ICONS['warning']}  Identifiants incorrects")


# ============================================================================
# ECRAN D'INSCRIPTION
# ============================================================================

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.consent_var = ctk.BooleanVar(value=False)
        self.create_widgets()

    def create_widgets(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=60, pady=30)

        # Header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 24))

        ProButton(header, text=f"{ICONS['back']} Retour", command=self.app.show_login, variant="ghost").pack(side="left")

        # Titre
        ctk.CTkLabel(scroll, text="Creer un compte", font=ctk.CTkFont(size=28, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(scroll, text="Vos donnees seront chiffrees et stockees localement", font=ctk.CTkFont(size=13), text_color=THEME['text_secondary']).pack(anchor="w", pady=(4, 24))

        # Card formulaire
        form_card = ProCard(scroll)
        form_card.pack(fill="x", padx=80)

        form = ctk.CTkFrame(form_card, fg_color="transparent")
        form.pack(padx=36, pady=32, fill="x")

        # Ligne 1: Prenom / Nom
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 16))

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(col1, text="Prenom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.firstname = ProEntry(col1, placeholder="Jean")
        self.firstname.pack(fill="x")

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(12, 0))
        ctk.CTkLabel(col2, text="Nom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.lastname = ProEntry(col2, placeholder="Dupont")
        self.lastname.pack(fill="x")

        # Email
        ctk.CTkLabel(form, text="Adresse email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email = ProEntry(form, placeholder="jean.dupont@exemple.com")
        self.email.pack(fill="x", pady=(0, 16))

        # Ligne 2: Mots de passe
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 20))

        col1 = ctk.CTkFrame(row2, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(col1, text="Mot de passe", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.password = ProEntry(col1, placeholder="Min. 8 caracteres", show="*")
        self.password.pack(fill="x")

        col2 = ctk.CTkFrame(row2, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(12, 0))
        ctk.CTkLabel(col2, text="Confirmer", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.confirm = ProEntry(col2, placeholder="Retapez le mot de passe", show="*")
        self.confirm.pack(fill="x")

        # RGPD
        rgpd_frame = ctk.CTkFrame(form, fg_color=THEME['bg_tertiary'], corner_radius=6)
        rgpd_frame.pack(fill="x", pady=(8, 20))

        rgpd_inner = ctk.CTkFrame(rgpd_frame, fg_color="transparent")
        rgpd_inner.pack(padx=20, pady=16)

        ctk.CTkLabel(rgpd_inner, text=f"{ICONS['lock']}  Protection des donnees (RGPD/CNIL)", font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(rgpd_inner, text=RGPD_TEXTS['consent_text'], font=ctk.CTkFont(size=11), text_color=THEME['text_secondary'], justify="left", wraplength=500).pack(anchor="w", pady=(8, 12))

        self.consent_check = ctk.CTkCheckBox(
            rgpd_inner,
            text="J'accepte la politique de confidentialite",
            variable=self.consent_var,
            font=ctk.CTkFont(size=12),
            text_color=THEME['text_primary'],
            fg_color=THEME['accent'],
            hover_color=THEME['accent_hover']
        )
        self.consent_check.pack(anchor="w")

        # Boutons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8, 0))

        ProButton(btn_frame, text="Creer mon compte", command=self.register, variant="success", width=180).pack(side="right")

        # Erreur
        self.error_label = ctk.CTkLabel(form, text="", text_color=THEME['error_text'], font=ctk.CTkFont(size=12))
        self.error_label.pack(pady=(16, 0))

    def register(self):
        firstname = self.firstname.get().strip()
        lastname = self.lastname.get().strip()
        email = self.email.get().strip()
        password = self.password.get()
        confirm = self.confirm.get()

        if not all([firstname, lastname, email, password, confirm]):
            self.error_label.configure(text=f"{ICONS['warning']}  Tous les champs sont obligatoires")
            return

        if not self.consent_var.get():
            self.error_label.configure(text=f"{ICONS['warning']}  Vous devez accepter la politique de confidentialite")
            return

        if password != confirm:
            self.error_label.configure(text=f"{ICONS['warning']}  Les mots de passe ne correspondent pas")
            return

        if len(password) < 8:
            self.error_label.configure(text=f"{ICONS['warning']}  Mot de passe trop court (min. 8 caracteres)")
            return

        existing = self.app.db_session.query(User).filter_by(email=email).first()
        if existing:
            self.error_label.configure(text=f"{ICONS['warning']}  Cet email est deja utilise")
            return

        from bcrypt import hashpw, gensalt
        user = User(
            email=email,
            first_name=firstname,
            last_name=lastname,
            role='user',
            is_active=True
        )
        user.password_hash = hashpw(password.encode(), gensalt()).decode()

        self.app.db_session.add(user)
        self.app.db_session.commit()

        self.app.current_user = user
        self.app.show_dashboard()


# ============================================================================
# FRAME PRINCIPAL
# ============================================================================

class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.current_view = None
        self.nav_buttons = {}
        self.create_widgets()

    def create_widgets(self):
        # Sidebar
        sidebar = ctk.CTkFrame(self, width=240, fg_color=THEME['bg_secondary'], corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=70)
        logo_frame.pack(fill="x", padx=16, pady=(20, 8))
        logo_frame.pack_propagate(False)

        logo_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        logo_box = ctk.CTkFrame(logo_row, fg_color=THEME['accent'], width=36, height=36, corner_radius=8)
        logo_box.pack(side="left")
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="FD", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        logo_text = ctk.CTkFrame(logo_row, fg_color="transparent")
        logo_text.pack(side="left", padx=12)
        ctk.CTkLabel(logo_text, text="FamiliDocs", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(logo_text, text="v2.1", font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(anchor="w")

        # User card
        user_card = ctk.CTkFrame(sidebar, fg_color=THEME['bg_tertiary'], corner_radius=8)
        user_card.pack(fill="x", padx=12, pady=12)

        user_inner = ctk.CTkFrame(user_card, fg_color="transparent")
        user_inner.pack(padx=12, pady=10)

        initials = f"{self.app.current_user.first_name[0]}{self.app.current_user.last_name[0]}".upper()
        avatar = ctk.CTkFrame(user_inner, fg_color=THEME['accent'], width=38, height=38, corner_radius=19)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        user_info = ctk.CTkFrame(user_inner, fg_color="transparent")
        user_info.pack(side="left", padx=10)
        ctk.CTkLabel(user_info, text=self.app.current_user.full_name, font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")

        role_text = self.app.current_user.role.upper()
        ctk.CTkLabel(user_info, text=role_text, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(anchor="w")

        # Separator
        ctk.CTkFrame(sidebar, fg_color=THEME['border'], height=1).pack(fill="x", padx=16, pady=8)

        # Navigation
        ctk.CTkLabel(sidebar, text="NAVIGATION", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", padx=20, pady=(8, 4))

        nav_items = [
            ("dashboard", ICONS['dashboard'], "Tableau de bord"),
            ("documents", ICONS['documents'], "Documents"),
            ("tasks", ICONS['tasks'], "Taches"),
            ("family", ICONS['family'], "Famille"),
            ("notifications", ICONS['notifications'], "Notifications"),
        ]

        for name, icon, label in nav_items:
            btn = NavButton(sidebar, text=label, icon=icon, command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        # Separator
        ctk.CTkFrame(sidebar, fg_color=THEME['border'], height=1).pack(fill="x", padx=16, pady=8)

        ctk.CTkLabel(sidebar, text="COMPTE", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", padx=20, pady=(8, 4))

        account_items = [
            ("profile", ICONS['profile'], "Mon profil"),
            ("rgpd", ICONS['lock'], "Mes donnees"),
        ]

        for name, icon, label in account_items:
            btn = NavButton(sidebar, text=label, icon=icon, command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        if self.app.current_user.role == 'admin':
            ctk.CTkFrame(sidebar, fg_color=THEME['border'], height=1).pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(sidebar, text="ADMINISTRATION", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", padx=20, pady=(8, 4))

            btn = NavButton(sidebar, text="Administration", icon=ICONS['admin'], command=lambda: self.show_view("admin"))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons["admin"] = btn

        # Logout
        logout_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logout_frame.pack(side="bottom", fill="x", padx=12, pady=16)

        ProButton(logout_frame, text=f"{ICONS['logout']}  Deconnexion", command=self.app.logout, variant="ghost").pack(fill="x")

        # Content
        self.content = ctk.CTkFrame(self, fg_color=THEME['bg_primary'])
        self.content.pack(side="right", fill="both", expand=True)

        self.show_view("dashboard")

    def show_view(self, view_name):
        self.current_view = view_name

        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color=THEME['bg_active'], text_color='#FFFFFF')
            else:
                btn.configure(fg_color='transparent', text_color=THEME['text_secondary'])

        for widget in self.content.winfo_children():
            widget.destroy()

        wrapper = ctk.CTkFrame(self.content, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        views = {
            "dashboard": DashboardView,
            "documents": DocumentsView,
            "tasks": TasksView,
            "family": FamilyView,
            "notifications": NotificationsView,
            "profile": ProfileView,
            "rgpd": RGPDView,
            "admin": AdminView,
        }

        view_class = views.get(view_name, DashboardView)
        view_class(wrapper, self.app, self).pack(fill="both", expand=True)


# ============================================================================
# DASHBOARD
# ============================================================================

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 24))

        greeting = "Bonjour" if 5 <= datetime.now().hour < 18 else "Bonsoir"
        ctk.CTkLabel(header, text=f"{greeting}, {self.app.current_user.first_name}", font=ctk.CTkFont(size=26, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        date_str = datetime.now().strftime("%d %B %Y")
        ctk.CTkLabel(header, text=date_str, font=ctk.CTkFont(size=13), text_color=THEME['text_secondary']).pack(side="right")

        # Stats
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 24))

        doc_count = self.app.db_session.query(Document).filter_by(owner_id=self.app.current_user.id).count()
        task_count = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.status.notin_(['completed', 'cancelled'])
        ).count()
        overdue_count = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.due_date < date.today(),
            Task.status.notin_(['completed', 'cancelled'])
        ).count()
        notif_count = self.app.db_session.query(Notification).filter_by(
            user_id=self.app.current_user.id,
            is_read=False
        ).count()

        stats = [
            ("Documents", doc_count, "Total stockes", ICONS['documents'], None, lambda: self.main_frame.show_view("documents")),
            ("Taches actives", task_count, "En cours", ICONS['tasks'], THEME['accent'], lambda: self.main_frame.show_view("tasks")),
            ("En retard", overdue_count, "A traiter", ICONS['warning'], THEME['error_text'] if overdue_count > 0 else None, lambda: self.main_frame.show_view("tasks")),
            ("Notifications", notif_count, "Non lues", ICONS['notifications'], THEME['warning_text'] if notif_count > 0 else None, lambda: self.main_frame.show_view("notifications")),
        ]

        for i, (title, value, subtitle, icon, color, command) in enumerate(stats):
            card = StatCard(stats_frame, title=title, value=value, subtitle=subtitle, icon=icon, color=color, command=command)
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))

        # Deux colonnes
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        # Colonne gauche - Taches
        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tasks_card = ProCard(left)
        tasks_card.pack(fill="both", expand=True)

        tasks_header = ctk.CTkFrame(tasks_card, fg_color="transparent")
        tasks_header.pack(fill="x", padx=20, pady=(20, 12))

        ctk.CTkLabel(tasks_header, text=f"{ICONS['tasks']}  Taches a venir", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        ProButton(tasks_header, text="Voir tout", command=lambda: self.main_frame.show_view("tasks"), variant="link", width=80).pack(side="right")

        tasks_scroll = ctk.CTkScrollableFrame(tasks_card, fg_color="transparent", height=280)
        tasks_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        tasks = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.status.notin_(['completed', 'cancelled'])
        ).order_by(Task.due_date).limit(8).all()

        if tasks:
            for task in tasks:
                self.create_task_row(tasks_scroll, task)
        else:
            ctk.CTkLabel(tasks_scroll, text="Aucune tache en cours", text_color=THEME['text_muted'], font=ctk.CTkFont(size=13)).pack(pady=40)

        # Colonne droite - Actions rapides
        right = ctk.CTkFrame(cols, fg_color="transparent", width=320)
        right.pack(side="right", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        actions_card = ProCard(right)
        actions_card.pack(fill="x")

        ctk.CTkLabel(actions_card, text="Actions rapides", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(padx=20, pady=(20, 12), anchor="w")

        actions = [
            ("Nouveau document", "primary", lambda: self.open_add_document()),
            ("Nouvelle tache", "success", lambda: self.open_add_task()),
            ("Inviter un membre", "secondary", lambda: self.main_frame.show_view("family")),
        ]

        for text, variant, cmd in actions:
            ProButton(actions_card, text=f"{ICONS['add']}  {text}", command=cmd, variant=variant, width=260).pack(padx=20, pady=4)

        ctk.CTkFrame(actions_card, fg_color="transparent", height=16).pack()

        # Info securite
        security_card = ProCard(right)
        security_card.pack(fill="x", pady=(16, 0))

        sec_inner = ctk.CTkFrame(security_card, fg_color="transparent")
        sec_inner.pack(padx=20, pady=16)

        ctk.CTkLabel(sec_inner, text=f"{ICONS['lock']}  Vos donnees", font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(sec_inner, text="Chiffrees et stockees localement\nsur cet ordinateur uniquement.", font=ctk.CTkFont(size=11), text_color=THEME['text_muted'], justify="left").pack(anchor="w", pady=(6, 0))

        ProButton(sec_inner, text="Gerer mes donnees", command=lambda: self.main_frame.show_view("rgpd"), variant="link", anchor="w").pack(anchor="w", pady=(8, 0))

    def create_task_row(self, parent, task):
        row = ctk.CTkFrame(parent, fg_color=THEME['bg_tertiary'], corner_radius=6)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        # Indicateur priorite
        priority_colors = {'high': THEME['error'], 'urgent': THEME['error'], 'normal': THEME['warning'], 'low': THEME['success']}
        p_color = priority_colors.get(task.priority, THEME['text_muted'])

        indicator = ctk.CTkFrame(inner, fg_color=p_color, width=3, height=24, corner_radius=2)
        indicator.pack(side="left", padx=(0, 12))

        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info, text=task.title, font=ctk.CTkFont(size=12), text_color=THEME['text_primary']).pack(anchor="w")

        if task.due_date:
            is_overdue = task.due_date < date.today()
            days = (task.due_date - date.today()).days

            if is_overdue:
                date_text = f"En retard ({abs(days)}j)"
                date_color = THEME['error_text']
            elif days == 0:
                date_text = "Aujourd'hui"
                date_color = THEME['warning_text']
            elif days == 1:
                date_text = "Demain"
                date_color = THEME['text_secondary']
            else:
                date_text = f"Dans {days} jours"
                date_color = THEME['text_muted']

            ctk.CTkLabel(info, text=date_text, font=ctk.CTkFont(size=10), text_color=date_color).pack(anchor="w")

    def open_add_document(self):
        DocumentDialog(self, self.app)

    def open_add_task(self):
        TaskDialog(self, self.app)


# ============================================================================
# DOCUMENTS (avec support Markdown)
# ============================================================================

class DocumentsView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text=f"{ICONS['documents']}  Documents", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ProButton(btn_frame, text=f"{ICONS['add']} Document", command=self.add_document, variant="primary").pack(side="left", padx=(0, 8))
        ProButton(btn_frame, text=f"{ICONS['add']} Note (.md)", command=self.add_markdown, variant="secondary").pack(side="left")

        # Barre de recherche
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 16))

        self.search_entry = ProEntry(search_frame, placeholder=f"{ICONS['search']}  Rechercher...", width=300)
        self.search_entry.pack(side="left")

        self.category_filter = ctk.CTkComboBox(
            search_frame,
            values=["Toutes categories", "Administratif", "Sante", "Banque", "Logement", "Notes", "Autres"],
            width=180,
            fg_color=THEME['bg_tertiary'],
            border_color=THEME['border'],
            button_color=THEME['accent'],
            dropdown_fg_color=THEME['bg_secondary']
        )
        self.category_filter.pack(side="left", padx=12)

        # Liste
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        documents = self.app.db_session.query(Document).filter_by(owner_id=self.app.current_user.id).order_by(Document.created_at.desc()).all()

        if documents:
            for doc in documents:
                self.create_doc_row(scroll, doc)
        else:
            empty = ctk.CTkFrame(scroll, fg_color="transparent")
            empty.pack(expand=True, pady=60)
            ctk.CTkLabel(empty, text=ICONS['documents'], font=ctk.CTkFont(size=32), text_color=THEME['text_muted']).pack()
            ctk.CTkLabel(empty, text="Aucun document", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['text_primary']).pack(pady=(12, 4))
            ctk.CTkLabel(empty, text="Ajoutez votre premier document ou note", text_color=THEME['text_muted']).pack()

    def create_doc_row(self, parent, doc):
        row = ProCard(parent)
        row.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Icone type
        file_icons = {'pdf': 'PDF', 'jpg': 'IMG', 'jpeg': 'IMG', 'png': 'IMG', 'doc': 'DOC', 'docx': 'DOC', 'xls': 'XLS', 'xlsx': 'XLS', 'md': 'MD'}
        file_type = doc.file_type.lower() if doc.file_type else 'file'
        icon_text = file_icons.get(file_type, 'FILE')
        icon_color = THEME['purple'] if file_type == 'md' else THEME['accent']

        icon_box = ctk.CTkFrame(inner, fg_color=icon_color, width=44, height=44, corner_radius=8)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon_text, font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=14)

        ctk.CTkLabel(info, text=doc.title, font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        meta = f"{doc.category or 'Sans categorie'}  |  {doc.created_at.strftime('%d/%m/%Y')}"
        ctk.CTkLabel(info, text=meta, font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(anchor="w")

        # Actions
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        ProButton(actions, text="Ouvrir", command=lambda d=doc: self.view_doc(d), variant="secondary", width=70).pack(side="left", padx=4)
        ProButton(actions, text=ICONS['delete'], command=lambda d=doc: self.delete_doc(d), variant="danger", width=36).pack(side="left")

    def add_document(self):
        dialog = DocumentDialog(self, self.app)
        self.wait_window(dialog)
        self.refresh()

    def add_markdown(self):
        dialog = MarkdownDialog(self, self.app)
        self.wait_window(dialog)
        self.refresh()

    def view_doc(self, doc):
        if doc.file_type and doc.file_type.lower() == 'md':
            MarkdownViewDialog(self, self.app, doc)
        else:
            DocumentViewDialog(self, self.app, doc)

    def delete_doc(self, doc):
        if messagebox.askyesno("Confirmer", f"Supprimer '{doc.title}' ?\n\nCette action est irreversible."):
            self.app.db_session.delete(doc)
            self.app.db_session.commit()
            self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


class DocumentDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_file = None

        self.title("Nouveau document")
        self.geometry("520x480")
        self.configure(fg_color=THEME['bg_primary'])
        self.resizable(False, False)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{ICONS['documents']}  Nouveau document", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(form, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = ProEntry(form, placeholder="Titre du document")
        self.title_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Categorie", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.category = ctk.CTkComboBox(form, values=['Administratif', 'Sante', 'Banque', 'Logement', 'Autres'], fg_color=THEME['bg_tertiary'], border_color=THEME['border'])
        self.category.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.desc = ctk.CTkTextbox(form, height=80, fg_color=THEME['bg_tertiary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'])
        self.desc.pack(fill="x", pady=(0, 16))

        # Fichier
        file_frame = ctk.CTkFrame(form, fg_color=THEME['bg_tertiary'], corner_radius=6, border_width=1, border_color=THEME['border'])
        file_frame.pack(fill="x", pady=(0, 20))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(padx=14, pady=12, fill="x")

        self.file_label = ctk.CTkLabel(file_inner, text="Aucun fichier selectionne", text_color=THEME['text_muted'], font=ctk.CTkFont(size=12))
        self.file_label.pack(side="left")

        ProButton(file_inner, text="Parcourir", command=self.select_file, variant="secondary", width=90).pack(side="right")

        # Footer
        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        ProButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        ProButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Tous", "*.*"), ("PDF", "*.pdf"), ("Images", "*.png *.jpg *.jpeg"), ("Documents", "*.doc *.docx")])
        if path:
            self.selected_file = path
            self.file_label.configure(text=os.path.basename(path), text_color=THEME['success_text'])

    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        doc = Document(
            title=title,
            category=self.category.get(),
            description=self.desc.get("1.0", "end").strip(),
            owner_id=self.app.current_user.id
        )

        if self.selected_file:
            import shutil, uuid
            upload_folder = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER')
            ext = os.path.splitext(self.selected_file)[1]
            new_filename = f"{uuid.uuid4()}{ext}"
            shutil.copy2(self.selected_file, os.path.join(upload_folder, new_filename))
            doc.file_path = new_filename
            doc.file_type = ext[1:] if ext else None

        self.app.db_session.add(doc)
        self.app.db_session.commit()
        self.destroy()


class MarkdownDialog(ctk.CTkToplevel):
    """Dialog pour creer une note Markdown"""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.title("Nouvelle note")
        self.geometry("700x600")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="MD  Nouvelle note Markdown", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        # Titre
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = ProEntry(col1, placeholder="Titre de la note")
        self.title_entry.pack(fill="x")

        col2 = ctk.CTkFrame(row1, fg_color="transparent", width=180)
        col2.pack(side="right")
        col2.pack_propagate(False)
        ctk.CTkLabel(col2, text="Categorie", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.category = ctk.CTkComboBox(col2, values=['Notes', 'Administratif', 'Sante', 'Autres'], fg_color=THEME['bg_tertiary'], border_color=THEME['border'])
        self.category.set('Notes')
        self.category.pack(fill="x")

        # Contenu Markdown
        ctk.CTkLabel(form, text="Contenu (Markdown supporte)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(8, 4))

        self.content = ctk.CTkTextbox(form, fg_color=THEME['bg_tertiary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=12))
        self.content.pack(fill="both", expand=True)
        self.content.insert("1.0", "# Titre\n\nVotre contenu ici...\n\n## Section\n\n- Element 1\n- Element 2\n")

        # Footer
        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        ProButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        ProButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

    def save(self):
        title = self.title_entry.get().strip()
        content = self.content.get("1.0", "end").strip()

        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        # Sauvegarder le fichier MD
        import uuid
        docs_folder = os.environ.get('FAMILIDOCS_DOCS_FOLDER')
        filename = f"{uuid.uuid4()}.md"
        filepath = os.path.join(docs_folder, filename)

        # Chiffrer le contenu
        encrypted_content = self.app.encryption.encrypt(content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)

        # Creer le document en BDD
        doc = Document(
            title=title,
            category=self.category.get(),
            description="Note Markdown",
            file_path=filename,
            file_type='md',
            owner_id=self.app.current_user.id
        )

        self.app.db_session.add(doc)
        self.app.db_session.commit()
        self.destroy()


class MarkdownViewDialog(ctk.CTkToplevel):
    """Visualiseur de notes Markdown"""
    def __init__(self, parent, app, doc):
        super().__init__(parent)
        self.app = app
        self.doc = doc

        self.title(doc.title)
        self.geometry("750x600")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=f"MD  {self.doc.title}", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)
        ProButton(header, text="Modifier", command=self.edit, variant="secondary", width=80).pack(side="right", padx=24)

        # Charger et dechiffrer le contenu
        content = ""
        if self.doc.file_path:
            docs_folder = os.environ.get('FAMILIDOCS_DOCS_FOLDER')
            filepath = os.path.join(docs_folder, self.doc.file_path)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    encrypted = f.read()
                content = self.app.encryption.decrypt(encrypted)

        # Afficher le contenu
        text_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=28, pady=20)

        text = ctk.CTkTextbox(text_frame, fg_color=THEME['bg_tertiary'], text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=12), border_width=0)
        text.pack(fill="both", expand=True)
        text.insert("1.0", content)
        text.configure(state="disabled")

    def edit(self):
        # Ouvrir l'editeur
        self.destroy()
        # TODO: Implementer l'edition


class DocumentViewDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, doc):
        super().__init__(parent)
        self.app = app
        self.doc = doc

        self.title(doc.title)
        self.geometry("550x400")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{ICONS['documents']}  {self.doc.title}", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=20)

        # Metadonnees
        meta_card = ProCard(content)
        meta_card.pack(fill="x")

        meta_inner = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_inner.pack(padx=20, pady=16, fill="x")

        infos = [
            ("Categorie", self.doc.category or "Non definie"),
            ("Date d'ajout", self.doc.created_at.strftime("%d/%m/%Y a %H:%M")),
            ("Type", self.doc.file_type.upper() if self.doc.file_type else "Non defini"),
        ]

        for label, value in infos:
            row = ctk.CTkFrame(meta_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary'], width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color=THEME['text_primary']).pack(side="left")

        if self.doc.description:
            ctk.CTkLabel(content, text="Description", font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(20, 8))
            desc_card = ProCard(content)
            desc_card.pack(fill="x")
            ctk.CTkLabel(desc_card, text=self.doc.description, text_color=THEME['text_secondary'], wraplength=450, justify="left").pack(padx=20, pady=14, anchor="w")

        if self.doc.file_path:
            ProButton(content, text=f"{ICONS['folder']}  Ouvrir le fichier", command=self.open_file, variant="primary", width=180).pack(pady=24)

    def open_file(self):
        upload_folder = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER')
        path = os.path.join(upload_folder, self.doc.file_path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Erreur", "Fichier introuvable")


# ============================================================================
# TACHES
# ============================================================================

class TasksView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text=f"{ICONS['tasks']}  Taches", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        ProButton(header, text=f"{ICONS['add']} Nouvelle tache", command=self.add_task, variant="primary").pack(side="right")

        # Tabs
        tabs = ctk.CTkTabview(self, fg_color=THEME['bg_secondary'], segmented_button_fg_color=THEME['bg_tertiary'], segmented_button_selected_color=THEME['accent'])
        tabs.pack(fill="both", expand=True)

        tabs.add("A faire")
        tabs.add("Terminees")

        pending = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.status.notin_(['completed', 'cancelled'])
        ).order_by(Task.due_date).all()
        self.show_tasks(tabs.tab("A faire"), pending, completed=False)

        completed = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.status == 'completed'
        ).order_by(Task.completed_at.desc()).limit(25).all()
        self.show_tasks(tabs.tab("Terminees"), completed, completed=True)

    def show_tasks(self, parent, tasks, completed=False):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        if not tasks:
            msg = "Aucune tache terminee" if completed else "Aucune tache en cours"
            ctk.CTkLabel(scroll, text=msg, text_color=THEME['text_muted'], font=ctk.CTkFont(size=13)).pack(pady=40)
            return

        for task in tasks:
            row = ProCard(scroll)
            row.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            if not completed:
                cb = ctk.CTkCheckBox(inner, text="", command=lambda t=task: self.complete_task(t), fg_color=THEME['success'], hover_color=THEME['success'], width=20)
                cb.pack(side="left")
            else:
                ctk.CTkLabel(inner, text=ICONS['check'], font=ctk.CTkFont(size=14), text_color=THEME['success_text']).pack(side="left")

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", padx=14, fill="x", expand=True)

            ctk.CTkLabel(info, text=task.title, font=ctk.CTkFont(size=13), text_color=THEME['text_primary']).pack(anchor="w")

            if task.description:
                desc = task.description[:50] + "..." if len(task.description) > 50 else task.description
                ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(anchor="w")

            if task.due_date and not completed:
                is_overdue = task.due_date < date.today()
                date_color = THEME['error_text'] if is_overdue else THEME['text_secondary']
                ctk.CTkLabel(inner, text=task.due_date.strftime("%d/%m/%Y"), text_color=date_color, font=ctk.CTkFont(size=11)).pack(side="right")

    def add_task(self):
        dialog = TaskDialog(self, self.app)
        self.wait_window(dialog)
        self.refresh()

    def complete_task(self, task):
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        self.app.db_session.commit()
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


class TaskDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.title("Nouvelle tache")
        self.geometry("480x420")
        self.configure(fg_color=THEME['bg_primary'])
        self.resizable(False, False)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{ICONS['tasks']}  Nouvelle tache", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(form, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = ProEntry(form, placeholder="Titre de la tache")
        self.title_entry.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.desc = ctk.CTkTextbox(form, height=70, fg_color=THEME['bg_tertiary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'])
        self.desc.pack(fill="x", pady=(0, 14))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Priorite", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.priority = ctk.CTkComboBox(col1, values=['low', 'normal', 'high', 'urgent'], fg_color=THEME['bg_tertiary'], border_color=THEME['border'])
        self.priority.set('normal')
        self.priority.pack(fill="x")

        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(col2, text="Date limite", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.date_entry = ProEntry(col2, placeholder="JJ/MM/AAAA")
        self.date_entry.pack(fill="x")

        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        ProButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        ProButton(btn_frame, text="Creer", command=self.save, variant="success", width=90).pack(side="left")

    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        date_str = self.date_entry.get().strip()
        if not date_str:
            messagebox.showerror("Erreur", "La date limite est obligatoire")
            return

        try:
            due_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide (JJ/MM/AAAA)")
            return

        task = Task(
            title=title,
            description=self.desc.get("1.0", "end").strip(),
            priority=self.priority.get(),
            due_date=due_date,
            owner_id=self.app.current_user.id
        )

        self.app.db_session.add(task)
        self.app.db_session.commit()
        self.destroy()


# ============================================================================
# FAMILLE
# ============================================================================

class FamilyView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text=f"{ICONS['family']}  Famille", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 20))

        family = self.app.db_session.query(Family).join(Family.members).filter(Family.members.any(user_id=self.app.current_user.id)).first()

        if family:
            self.show_family(family)
        else:
            self.show_no_family()

    def show_no_family(self):
        card = ProCard(self)
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(pady=50, padx=50)

        ctk.CTkLabel(inner, text=ICONS['family'], font=ctk.CTkFont(size=36), text_color=THEME['text_muted']).pack()
        ctk.CTkLabel(inner, text="Aucune famille", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['text_primary']).pack(pady=(12, 4))
        ctk.CTkLabel(inner, text="Creez une famille ou rejoignez-en une", text_color=THEME['text_muted']).pack()

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(pady=24)

        ProButton(btns, text="Creer une famille", command=self.create_family, variant="primary", width=150).pack(side="left", padx=8)
        ProButton(btns, text="Rejoindre", command=self.join_family, variant="secondary", width=120).pack(side="left", padx=8)

    def show_family(self, family):
        card = ProCard(self)
        card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=24)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(header, text=family.name, font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        ctk.CTkLabel(header, text=f"{len(family.members)} membre(s)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="right")

        ctk.CTkFrame(inner, fg_color=THEME['border'], height=1).pack(fill="x", pady=8)

        ctk.CTkLabel(inner, text="MEMBRES", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", pady=(12, 8))

        for member in family.members:
            m_row = ctk.CTkFrame(inner, fg_color=THEME['bg_tertiary'], corner_radius=6)
            m_row.pack(fill="x", pady=3)

            m_inner = ctk.CTkFrame(m_row, fg_color="transparent")
            m_inner.pack(fill="x", padx=14, pady=10)

            initials = f"{member.user.first_name[0]}{member.user.last_name[0]}".upper()
            avatar = ctk.CTkFrame(m_inner, fg_color=THEME['accent'], width=36, height=36, corner_radius=18)
            avatar.pack(side="left")
            avatar.pack_propagate(False)
            ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(m_inner, text=member.user.full_name, font=ctk.CTkFont(size=13), text_color=THEME['text_primary']).pack(side="left", padx=12)
            ctk.CTkLabel(m_inner, text=member.role.upper(), font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(side="right")

    def create_family(self):
        dialog = ctk.CTkInputDialog(text="Nom de la famille:", title="Creer une famille")
        name = dialog.get_input()

        if name:
            from app.models.family import FamilyMember
            family = Family(name=name, created_by_id=self.app.current_user.id)
            self.app.db_session.add(family)
            self.app.db_session.flush()

            member = FamilyMember(family_id=family.id, user_id=self.app.current_user.id, role='admin')
            self.app.db_session.add(member)
            self.app.db_session.commit()
            self.refresh()

    def join_family(self):
        messagebox.showinfo("Information", "Demandez un lien d'invitation a un membre de la famille")

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class NotificationsView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text=f"{ICONS['notifications']}  Notifications", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        ProButton(header, text="Tout marquer comme lu", command=self.mark_all_read, variant="secondary").pack(side="right")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        notifications = self.app.db_session.query(Notification).filter_by(user_id=self.app.current_user.id).order_by(Notification.created_at.desc()).limit(50).all()

        if notifications:
            for notif in notifications:
                self.create_notif_row(scroll, notif)
        else:
            ctk.CTkLabel(scroll, text="Aucune notification", text_color=THEME['text_muted'], font=ctk.CTkFont(size=13)).pack(pady=40)

    def create_notif_row(self, parent, notif):
        bg = THEME['bg_secondary'] if notif.is_read else THEME['bg_tertiary']
        border = THEME['border'] if notif.is_read else THEME['border_focus']

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, border_width=1, border_color=border)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        icons = {'document': ICONS['documents'], 'task': ICONS['tasks'], 'family': ICONS['family'], 'system': ICONS['settings']}
        icon = icons.get(notif.type, ICONS['notifications'])

        ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=14), text_color=THEME['text_secondary']).pack(side="left")

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", padx=14, fill="x", expand=True)

        ctk.CTkLabel(info, text=notif.title, font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(info, text=notif.message, font=ctk.CTkFont(size=11), text_color=THEME['text_secondary']).pack(anchor="w")

        ctk.CTkLabel(inner, text=notif.created_at.strftime("%d/%m %H:%M"), font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(side="right")

        if not notif.is_read:
            row.bind("<Button-1>", lambda e, n=notif: self.mark_read(n))

    def mark_read(self, notif):
        notif.is_read = True
        self.app.db_session.commit()
        self.refresh()

    def mark_all_read(self):
        self.app.db_session.query(Notification).filter_by(user_id=self.app.current_user.id, is_read=False).update({'is_read': True})
        self.app.db_session.commit()
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


# ============================================================================
# PROFIL (avec modification)
# ============================================================================

class ProfileView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        user = self.app.current_user

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header, text=f"{ICONS['profile']}  Mon profil", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        ProButton(header, text=f"{ICONS['edit']} Modifier", command=self.edit_profile, variant="secondary").pack(side="right")

        # Card profil
        card = ProCard(self)
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=28, pady=28)

        # Avatar
        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
        avatar = ctk.CTkFrame(inner, fg_color=THEME['accent'], width=80, height=80, corner_radius=40)
        avatar.pack()
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=26, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=user.full_name, font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack(pady=(14, 4))
        ctk.CTkLabel(inner, text=user.email, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack()

        # Role badge
        role_frame = ctk.CTkFrame(inner, fg_color=THEME['accent'], corner_radius=10)
        role_frame.pack(pady=10)
        ctk.CTkLabel(role_frame, text=f"  {user.role.upper()}  ", font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF").pack(padx=12, pady=4)

        # Stats
        stats_card = ProCard(self)
        stats_card.pack(fill="x", pady=20)

        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(padx=28, pady=20)

        ctk.CTkLabel(stats_inner, text="Statistiques", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 12))

        doc_count = self.app.db_session.query(Document).filter_by(owner_id=user.id).count()
        task_done = self.app.db_session.query(Task).filter(Task.owner_id == user.id, Task.status == 'completed').count()

        stats = [
            f"{ICONS['documents']}  {doc_count} documents",
            f"{ICONS['check']}  {task_done} taches terminees",
            f"{ICONS['calendar']}  Membre depuis {user.created_at.strftime('%d/%m/%Y')}",
        ]

        for stat in stats:
            ctk.CTkLabel(stats_inner, text=stat, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=3)

    def edit_profile(self):
        dialog = ProfileEditDialog(self, self.app)
        self.wait_window(dialog)
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


class ProfileEditDialog(ctk.CTkToplevel):
    """Dialog pour modifier le profil"""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.user = app.current_user

        self.title("Modifier le profil")
        self.geometry("500x450")
        self.configure(fg_color=THEME['bg_primary'])
        self.resizable(False, False)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"{ICONS['edit']}  Modifier le profil", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        # Prenom
        ctk.CTkLabel(form, text="Prenom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.firstname = ProEntry(form, placeholder="Prenom")
        self.firstname.insert(0, self.user.first_name)
        self.firstname.pack(fill="x", pady=(0, 14))

        # Nom
        ctk.CTkLabel(form, text="Nom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.lastname = ProEntry(form, placeholder="Nom")
        self.lastname.insert(0, self.user.last_name)
        self.lastname.pack(fill="x", pady=(0, 14))

        # Email
        ctk.CTkLabel(form, text="Email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email = ProEntry(form, placeholder="Email")
        self.email.insert(0, self.user.email)
        self.email.pack(fill="x", pady=(0, 14))

        # Titre familial
        ctk.CTkLabel(form, text="Titre familial (optionnel)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_combo = ctk.CTkComboBox(form, values=['', 'Papa', 'Maman', 'Fils', 'Fille', 'Grand-pere', 'Grand-mere', 'Oncle', 'Tante'], fg_color=THEME['bg_tertiary'], border_color=THEME['border'])
        current_title = getattr(self.user, 'family_title', '') or ''
        self.title_combo.set(current_title)
        self.title_combo.pack(fill="x", pady=(0, 14))

        # Photo (placeholder)
        photo_frame = ctk.CTkFrame(form, fg_color=THEME['bg_tertiary'], corner_radius=6)
        photo_frame.pack(fill="x", pady=(0, 14))

        photo_inner = ctk.CTkFrame(photo_frame, fg_color="transparent")
        photo_inner.pack(padx=14, pady=12, fill="x")

        ctk.CTkLabel(photo_inner, text="Photo de profil", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="left")
        ProButton(photo_inner, text="Changer", command=self.change_photo, variant="secondary", width=80).pack(side="right")

        # Footer
        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        ProButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        ProButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

    def change_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")])
        if path:
            import shutil, uuid
            avatars_folder = os.path.join(os.environ.get('FAMILIDOCS_UPLOAD_FOLDER'), 'avatars')
            ext = os.path.splitext(path)[1]
            new_filename = f"{self.user.id}_{uuid.uuid4()}{ext}"
            shutil.copy2(path, os.path.join(avatars_folder, new_filename))

            if hasattr(self.user, 'profile_photo'):
                self.user.profile_photo = new_filename
                self.app.db_session.commit()

            messagebox.showinfo("Succes", "Photo de profil mise a jour")

    def save(self):
        firstname = self.firstname.get().strip()
        lastname = self.lastname.get().strip()
        email = self.email.get().strip()

        if not all([firstname, lastname, email]):
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
            return

        self.user.first_name = firstname
        self.user.last_name = lastname
        self.user.email = email

        if hasattr(self.user, 'family_title'):
            self.user.family_title = self.title_combo.get()

        self.app.db_session.commit()
        self.destroy()


# ============================================================================
# RGPD
# ============================================================================

class RGPDView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text=f"{ICONS['lock']}  Mes donnees personnelles", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(self, text="Conformement au RGPD et a la loi Informatique et Libertes", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(4, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Info chiffrement
        enc_card = ctk.CTkFrame(scroll, fg_color=THEME['success'], corner_radius=8)
        enc_card.pack(fill="x", pady=(0, 16))

        enc_inner = ctk.CTkFrame(enc_card, fg_color="transparent")
        enc_inner.pack(padx=20, pady=14)

        ctk.CTkLabel(enc_inner, text=f"{ICONS['lock']}  Chiffrement actif", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(enc_inner, text="Vos donnees sont chiffrees en AES-256 et stockees uniquement sur cet ordinateur", font=ctk.CTkFont(size=11), text_color="#FFFFFF").pack(anchor="w", pady=(4, 0))

        # Droits
        rights = [
            (ICONS['documents'], "Droit d'acces", "Consultez toutes vos donnees", "Voir mes donnees", self.view_data),
            (ICONS['download'], "Droit a la portabilite", "Exportez vos donnees en JSON", "Exporter", self.export_data),
            (ICONS['edit'], "Droit de rectification", "Modifiez vos informations", "Modifier", lambda: self.main_frame.show_view("profile")),
            (ICONS['delete'], "Droit a l'effacement", "Supprimez votre compte et donnees", "Supprimer", self.delete_account),
        ]

        for icon, title, desc, btn_text, command in rights:
            card = ProCard(scroll)
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=16)

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=18), text_color=THEME['text_secondary']).pack(side="left")

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", padx=16, fill="x", expand=True)

            ctk.CTkLabel(info, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=11), text_color=THEME['text_secondary']).pack(anchor="w")

            variant = "danger" if "Supprimer" in btn_text else "secondary"
            ProButton(inner, text=btn_text, command=command, variant=variant, width=100).pack(side="right")

    def view_data(self):
        user = self.app.current_user
        data = {
            "informations": {"id": user.id, "email": user.email, "prenom": user.first_name, "nom": user.last_name, "role": user.role},
            "documents": self.app.db_session.query(Document).filter_by(owner_id=user.id).count(),
            "taches": self.app.db_session.query(Task).filter_by(owner_id=user.id).count()
        }

        dialog = ctk.CTkToplevel(self)
        dialog.title("Mes donnees")
        dialog.geometry("550x450")
        dialog.configure(fg_color=THEME['bg_primary'])
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Vos donnees personnelles", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['text_primary']).pack(padx=28, pady=20, anchor="w")

        text = ctk.CTkTextbox(dialog, fg_color=THEME['bg_tertiary'], text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=11))
        text.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        text.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        text.configure(state="disabled")

    def export_data(self):
        user = self.app.current_user
        documents = self.app.db_session.query(Document).filter_by(owner_id=user.id).all()
        tasks = self.app.db_session.query(Task).filter_by(owner_id=user.id).all()

        export = {
            "export_date": datetime.now().isoformat(),
            "user": {"id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name},
            "documents": [{"id": d.id, "title": d.title, "category": d.category} for d in documents],
            "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
        }

        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfilename=f"familidocs_export_{user.id}.json")

        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Succes", f"Donnees exportees vers:\n{path}")

    def delete_account(self):
        if not messagebox.askyesno("Attention", "Voulez-vous vraiment supprimer votre compte ?\n\nCette action est IRREVERSIBLE."):
            return

        confirm = ctk.CTkInputDialog(text="Tapez SUPPRIMER pour confirmer:", title="Confirmation")
        if confirm.get_input() != "SUPPRIMER":
            messagebox.showinfo("Annule", "Suppression annulee")
            return

        user = self.app.current_user
        self.app.db_session.query(Document).filter_by(owner_id=user.id).delete()
        self.app.db_session.query(Task).filter_by(owner_id=user.id).delete()
        self.app.db_session.query(Notification).filter_by(user_id=user.id).delete()
        self.app.db_session.delete(user)
        self.app.db_session.commit()

        messagebox.showinfo("Compte supprime", "Votre compte et toutes vos donnees ont ete supprimes.")
        self.app.logout()


# ============================================================================
# ADMINISTRATION
# ============================================================================

class AdminView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text=f"{ICONS['admin']}  Administration", font=ctk.CTkFont(size=22, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 20))

        # Stats
        stats_card = ProCard(self)
        stats_card.pack(fill="x")

        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(padx=28, pady=20)

        ctk.CTkLabel(stats_inner, text="Statistiques globales", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 12))

        total_users = self.app.db_session.query(User).count()
        total_docs = self.app.db_session.query(Document).count()
        total_families = self.app.db_session.query(Family).count()

        for stat in [f"{ICONS['family']}  {total_users} utilisateurs", f"{ICONS['documents']}  {total_docs} documents", f"{ICONS['family']}  {total_families} familles"]:
            ctk.CTkLabel(stats_inner, text=stat, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=3)

        # Users
        users_card = ProCard(self)
        users_card.pack(fill="both", expand=True, pady=20)

        users_inner = ctk.CTkFrame(users_card, fg_color="transparent")
        users_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(users_inner, text="Utilisateurs", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(users_inner, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for user in self.app.db_session.query(User).order_by(User.created_at.desc()).all():
            row = ctk.CTkFrame(scroll, fg_color=THEME['bg_tertiary'], corner_radius=6)
            row.pack(fill="x", pady=2)

            row_inner = ctk.CTkFrame(row, fg_color="transparent")
            row_inner.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(row_inner, text=user.full_name, font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
            ctk.CTkLabel(row_inner, text=user.email, font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(side="left", padx=12)

            status_color = THEME['success_text'] if user.is_active else THEME['error_text']
            ctk.CTkLabel(row_inner, text="Actif" if user.is_active else "Inactif", font=ctk.CTkFont(size=10), text_color=status_color).pack(side="right")


# ============================================================================
# POINT D'ENTREE
# ============================================================================

if __name__ == '__main__':
    app = FamiliDocsApp()
    app.mainloop()
