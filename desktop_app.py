# FamiliDocs desktop app - interface Liquid Glass
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

# === CFG ET CHEMINS ===

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_exe_dir():
    """dossier exe ou script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def setup_environment():
    base_path = get_base_path()
    exe_dir = get_exe_dir()
    if base_path not in sys.path:
        sys.path.insert(0, base_path)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(exe_dir, '.env'))

    user_data_dir = os.path.join(base_path, 'app', 'database')

    os.environ['FAMILIDOCS_UPLOAD_FOLDER'] = os.path.join(user_data_dir, 'uploads')
    os.environ['FAMILIDOCS_BACKUP_FOLDER'] = os.path.join(user_data_dir, 'backups')
    os.environ['FAMILIDOCS_DOCS_FOLDER'] = os.path.join(user_data_dir, 'documents')

    for folder in ['uploads', 'uploads/avatars', 'backups', 'exports', 'documents']:
        os.makedirs(os.path.join(user_data_dir, folder), exist_ok=True)

    return user_data_dir

USER_DATA_DIR = setup_environment()

from app import create_app
from app.models import db, User, Document, Folder, Task, Family, Notification
from app.models.family import FamilyMember
from app.models.message import Message
from app.models.log import Log

# === CHIFFREMENT LOCAL ===

class LocalEncryption:
    """chiffrement local data sensibles"""

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
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self._key = f.read()
        else:
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

            with open(self.key_file, 'wb') as f:
                f.write(self._key)

            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(self.key_file, 2)
            except Exception:
                pass

    def _get_machine_id(self):
        import platform
        import uuid
        return f"{platform.node()}-{uuid.getnode()}"

    def get_fernet(self):
        salt = self._key[:16]
        key = self._key[16:]
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        if not data:
            return data
        f = self.get_fernet()
        return f.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return encrypted_data
        try:
            f = self.get_fernet()
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data


# === THEME LIQUID GLASS ===

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

THEME = {
    # Backgrounds — Liquid Glass
    'bg_primary': '#F2F2F7',
    'bg_secondary': '#FFFFFF',
    'bg_tertiary': '#EDEDF0',
    'bg_elevated': '#FFFFFF',
    'bg_hover': '#E5E5EA',
    'bg_active': '#007AFF',

    # Glass effect
    'glass': '#F2F2F7',
    'glass_border': '#E0E0E5',

    # Borders
    'border': '#D1D1D6',
    'border_light': '#E5E5EA',
    'border_focus': '#007AFF',

    # Text
    'text_primary': '#1D1D1F',
    'text_secondary': '#86868B',
    'text_muted': '#AEAEB2',
    'text_link': '#007AFF',

    # Accent — Apple Blue gradient feel
    'accent': '#007AFF',
    'accent_hover': '#0062CC',
    'accent_muted': '#E0EDFF',

    # Semantic
    'success': '#30D158',
    'success_text': '#1A8040',
    'warning': '#FF9F0A',
    'warning_text': '#9A5B00',
    'error': '#FF453A',
    'error_text': '#C0291F',
    'info': '#64D2FF',

    # Special
    'purple': '#5856D6',
    'pink': '#FF2D55',
    'orange': '#FF9F0A',
    'cyan': '#64D2FF',

    # Sidebar
    'sidebar_bg': '#FFFFFF',
    'sidebar_active': '#E0EDFF',
    'sidebar_active_text': '#007AFF',
}


# === TEXTES RGPD ===

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


# === APP PRINCIPALE ===

class FamiliDocsApp(ctk.CTk):
    """app principale"""

    def __init__(self):
        super().__init__()

        self.title("FamiliDocs")
        self.geometry("1300x850")
        self.minsize(1100, 700)
        self.configure(fg_color=THEME['bg_primary'])

        self.encryption = LocalEncryption.get_instance()

        self.setup_database()

        self.current_user = None

        self.container = ctk.CTkFrame(self, fg_color=THEME['bg_primary'])
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def setup_database(self):
        self.flask_app = create_app()
        self.app_context = self.flask_app.app_context()
        self.app_context.push()
        db.create_all()
        self.db_session = db.session


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
        if self.current_user:
            Log.create_log(user_id=self.current_user.id, action='logout', details='Deconnexion desktop')
            self.db_session.commit()
        self.current_user = None
        self.show_login()


# === COMPOSANTS UI ===

class GlassButton(ctk.CTkButton):
    """btn glass — Liquid Glass style"""
    def __init__(self, master, text, command=None, variant="primary", **kwargs):
        variants = {
            'primary': {
                'fg_color': THEME['accent'],
                'hover_color': THEME['accent_hover'],
                'text_color': '#FFFFFF',
            },
            'secondary': {
                'fg_color': THEME['bg_tertiary'],
                'hover_color': THEME['bg_hover'],
                'text_color': THEME['text_primary'],
            },
            'success': {
                'fg_color': THEME['success'],
                'hover_color': '#1A8040',
                'text_color': '#FFFFFF',
            },
            'danger': {
                'fg_color': THEME['error'],
                'hover_color': '#C0291F',
                'text_color': '#FFFFFF',
            },
            'ghost': {
                'fg_color': 'transparent',
                'hover_color': THEME['bg_tertiary'],
                'text_color': THEME['text_secondary'],
            },
            'link': {
                'fg_color': 'transparent',
                'hover_color': THEME['bg_tertiary'],
                'text_color': THEME['text_link'],
            },
        }

        style = variants.get(variant, variants['primary'])

        super().__init__(
            master,
            text=text,
            command=command,
            corner_radius=12,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            **style,
            **kwargs
        )


class GlassEntry(ctk.CTkEntry):
    """input glass — Liquid Glass style"""
    def __init__(self, master, placeholder="", show=None, **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            show=show,
            height=42,
            corner_radius=12,
            border_width=1,
            fg_color=THEME['bg_secondary'],
            border_color=THEME['border_light'],
            text_color=THEME['text_primary'],
            placeholder_text_color=THEME['text_muted'],
            font=ctk.CTkFont(size=13),
            **kwargs
        )
        self.bind("<FocusIn>", lambda e: self.configure(border_color=THEME['border_focus']))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=THEME['border_light']))


class GlassCard(ctk.CTkFrame):
    """card glass — Liquid Glass style"""
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=THEME['bg_secondary'],
            corner_radius=16,
            border_width=1,
            border_color=THEME['border_light'],
            **kwargs
        )


class StatCard(ctk.CTkFrame):
    """card stat — Liquid Glass style with icon"""
    # Map de couleurs pour icones
    ICON_COLORS = {
        'Documents': '#007AFF',
        'Taches actives': '#30D158',
        'En retard': '#FF453A',
        'Notifications': '#FF9F0A',
    }
    ICON_TEXTS = {
        'Documents': 'DOC',
        'Taches actives': 'TSK',
        'En retard': '!',
        'Notifications': 'NTF',
    }

    def __init__(self, master, title, value, subtitle="", color=None, command=None, **kwargs):
        super().__init__(master, fg_color=THEME['bg_secondary'], corner_radius=16, border_width=1, border_color=THEME['border_light'], **kwargs)

        self.command = command

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=20, pady=16, fill="both", expand=True)

        # Icon badge
        ic_color = self.ICON_COLORS.get(title, THEME['accent'])
        ic_text = self.ICON_TEXTS.get(title, title[0])
        icon = ctk.CTkFrame(inner, fg_color=ic_color, width=32, height=32, corner_radius=10)
        icon.pack(anchor="w", pady=(0, 8))
        icon.pack_propagate(False)
        ctk.CTkLabel(icon, text=ic_text, font=ctk.CTkFont(size=9, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        value_color = color if color else THEME['text_primary']
        ctk.CTkLabel(inner, text=str(value), font=ctk.CTkFont(size=24, weight="bold"), text_color=value_color).pack(anchor="w")

        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=11), text_color=THEME['text_secondary']).pack(anchor="w", pady=(2, 0))

        if command:
            self.configure(cursor="hand2")
            self.bind("<Enter>", lambda e: self.configure(border_color=THEME['border_focus']))
            self.bind("<Leave>", lambda e: self.configure(border_color=THEME['border_light']))
            self.bind("<Button-1>", lambda e: command())
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: command())
                for subchild in child.winfo_children():
                    subchild.bind("<Button-1>", lambda e: command())


class NavButton(ctk.CTkButton):
    """btn nav sidebar — Liquid Glass style"""
    def __init__(self, master, text, command=None, active=False, **kwargs):
        fg = THEME['sidebar_active'] if active else 'transparent'
        text_color = THEME['sidebar_active_text'] if active else THEME['text_secondary']

        super().__init__(
            master,
            text=f"  {text}",
            command=command,
            anchor="w",
            height=38,
            corner_radius=10,
            fg_color=fg,
            hover_color=THEME['bg_hover'],
            text_color=text_color,
            font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
            **kwargs
        )


# === ECRAN CONNEXTION ===

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        # Layout centre unique — plus sobre
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo compact
        logo = ctk.CTkFrame(center, fg_color=THEME['accent'], width=56, height=56, corner_radius=16)
        logo.pack()
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="FD", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="FamiliDocs", font=ctk.CTkFont(size=24, weight="bold"), text_color=THEME['text_primary']).pack(pady=(16, 4))
        ctk.CTkLabel(center, text="Connexion", font=ctk.CTkFont(size=13), text_color=THEME['text_secondary']).pack(pady=(0, 28))

        ctk.CTkLabel(center, text="Email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email_entry = GlassEntry(center, placeholder="vous@exemple.com", width=340)
        self.email_entry.pack(pady=(0, 12))

        ctk.CTkLabel(center, text="Mot de passe", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.password_entry = GlassEntry(center, placeholder="Mot de passe", show="*", width=340)
        self.password_entry.pack(pady=(0, 16))

        GlassButton(center, text="Se connecter", command=self.login, variant="primary", width=340).pack(pady=(0, 16))

        GlassButton(center, text="Creer un compte", command=self.app.show_register, variant="ghost", width=340).pack()

        self.error_label = ctk.CTkLabel(center, text="", text_color=THEME['error_text'], font=ctk.CTkFont(size=12))
        self.error_label.pack(pady=12)

        self.password_entry.bind("<Return>", lambda e: self.login())

    def verify_password(self, password, password_hash):
        import bcrypt
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email or not password:
            self.error_label.configure(text="Veuillez remplir tous les champs")
            return

        user = self.app.db_session.query(User).filter_by(email=email).first()

        if user and self.verify_password(password, user.password_hash):
            if not user.is_active:
                self.error_label.configure(text="Ce compte est desactive")
                return
            user.last_login = datetime.utcnow()
            Log.create_log(user_id=user.id, action='login', details='Connexion desktop')
            self.app.db_session.commit()
            self.app.current_user = user
            self.app.show_dashboard()
        else:
            if user:
                Log.create_log(user_id=user.id, action='login_failed', details='Echec connexion desktop')
                self.app.db_session.commit()
            self.error_label.configure(text="Identifiants incorrects")


# === ECRAN INSCRIPTION ===

class RegisterFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.consent_var = ctk.BooleanVar(value=False)
        self.create_widgets()

    def create_widgets(self):
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        GlassButton(center, text="< Retour", command=self.app.show_login, variant="ghost", width=80).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(center, text="Creer un compte", font=ctk.CTkFont(size=24, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 20))

        row1 = ctk.CTkFrame(center, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Prenom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.firstname = GlassEntry(col1, placeholder="Jean", width=180)
        self.firstname.pack(fill="x")

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(col2, text="Nom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.lastname = GlassEntry(col2, placeholder="Dupont", width=180)
        self.lastname.pack(fill="x")

        ctk.CTkLabel(center, text="Email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email = GlassEntry(center, placeholder="jean.dupont@exemple.com", width=380)
        self.email.pack(fill="x", pady=(0, 12))

        row2 = ctk.CTkFrame(center, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 16))

        col1 = ctk.CTkFrame(row2, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Mot de passe", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.password = GlassEntry(col1, placeholder="Min. 8 caracteres", show="*", width=180)
        self.password.pack(fill="x")

        col2 = ctk.CTkFrame(row2, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(col2, text="Confirmer", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.confirm = GlassEntry(col2, placeholder="Confirmer", show="*", width=180)
        self.confirm.pack(fill="x")

        self.consent_check = ctk.CTkCheckBox(
            center,
            text="J'accepte la politique de confidentialite (RGPD)",
            variable=self.consent_var,
            font=ctk.CTkFont(size=11),
            text_color=THEME['text_secondary'],
            fg_color=THEME['accent'],
            hover_color=THEME['accent_hover']
        )
        self.consent_check.pack(anchor="w", pady=(0, 20))

        GlassButton(center, text="Creer mon compte", command=self.register, variant="primary", width=380).pack()

        self.error_label = ctk.CTkLabel(center, text="", text_color=THEME['error_text'], font=ctk.CTkFont(size=12))
        self.error_label.pack(pady=12)

    def register(self):
        firstname = self.firstname.get().strip()
        lastname = self.lastname.get().strip()
        email = self.email.get().strip()
        password = self.password.get()
        confirm = self.confirm.get()

        if not all([firstname, lastname, email, password, confirm]):
            self.error_label.configure(text="Tous les champs sont obligatoires")
            return

        if not self.consent_var.get():
            self.error_label.configure(text="Vous devez accepter la politique de confidentialite")
            return

        if password != confirm:
            self.error_label.configure(text="Les mots de passe ne correspondent pas")
            return

        if len(password) < 8:
            self.error_label.configure(text="Mot de passe trop court (min. 8 caracteres)")
            return

        existing = self.app.db_session.query(User).filter_by(email=email).first()
        if existing:
            self.error_label.configure(text="Cet email est deja utilise")
            return

        from bcrypt import hashpw, gensalt
        # username depuis email
        username = email.split('@')[0].replace('.', '_').replace('-', '_')
        # check unicite
        base_username = username
        counter = 1
        while self.app.db_session.query(User).filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        user = User(
            email=email,
            username=username,
            first_name=firstname,
            last_name=lastname,
            role='user',
            is_active=True
        )
        user.password_hash = hashpw(password.encode(), gensalt()).decode()

        self.app.db_session.add(user)
        self.app.db_session.flush()
        Log.create_log(user_id=user.id, action='login', details='Inscription + connexion desktop')
        self.app.db_session.commit()

        self.app.current_user = user
        self.app.show_dashboard()


# === FRAME PRINCIPAL ===

class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=THEME['bg_primary'])
        self.app = app
        self.current_view = None
        self.nav_buttons = {}
        self.create_widgets()

    def create_widgets(self):
        sidebar_container = ctk.CTkFrame(self, width=230, fg_color=THEME['sidebar_bg'], corner_radius=0, border_width=0)
        sidebar_container.pack(side="left", fill="y")
        sidebar_container.pack_propagate(False)

        sidebar = ctk.CTkScrollableFrame(sidebar_container, fg_color=THEME['sidebar_bg'], scrollbar_button_color=THEME['sidebar_bg'], scrollbar_button_hover_color=THEME['border_light'])
        sidebar.pack(fill="both", expand=True)

        ctk.CTkFrame(self, fg_color=THEME['border_light'], width=1).pack(side="left", fill="y")

        # Logo compact
        ctk.CTkLabel(sidebar, text="FamiliDocs", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['accent']).pack(padx=20, pady=(20, 4), anchor="w")

        # User — une ligne
        initials = f"{self.app.current_user.first_name[0]}{self.app.current_user.last_name[0]}".upper()
        user_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        user_row.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(user_row, text=f"{initials}  {self.app.current_user.first_name}", font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(anchor="w")

        ctk.CTkFrame(sidebar, fg_color=THEME['border_light'], height=1).pack(fill="x", padx=16, pady=4)

        # Navigation

        nav_items = [
            ("dashboard", "Tableau de bord"),
            ("documents", "Documents"),
            ("shares", "Partages"),
            ("tasks", "Taches"),
            ("family", "Famille"),
            ("chat", "Chat familial"),
            ("notifications", "Notifications"),
        ]

        for name, label in nav_items:
            btn = NavButton(sidebar, text=label, command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        ctk.CTkFrame(sidebar, fg_color=THEME['border_light'], height=1).pack(fill="x", padx=16, pady=6)

        account_items = [
            ("profile", "Mon profil"),
            ("rgpd", "Mes donnees"),
        ]

        for name, label in account_items:
            btn = NavButton(sidebar, text=label, command=lambda n=name: self.show_view(n))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[name] = btn

        if self.app.current_user.role == 'admin':
            ctk.CTkFrame(sidebar, fg_color=THEME['border_light'], height=1).pack(fill="x", padx=16, pady=6)

            btn = NavButton(sidebar, text="Gestion utilisateurs", command=lambda: self.show_view("admin"))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons["admin"] = btn

        # Logout
        logout_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logout_frame.pack(side="bottom", fill="x", padx=12, pady=16)

        GlassButton(logout_frame, text="Deconnexion", command=self.app.logout, variant="ghost").pack(fill="x")

        # Content
        self.content = ctk.CTkFrame(self, fg_color=THEME['bg_primary'])
        self.content.pack(side="right", fill="both", expand=True)

        self.show_view("dashboard")

    def show_view(self, view_name):
        self.current_view = view_name

        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color=THEME['sidebar_active'], text_color=THEME['sidebar_active_text'], font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color='transparent', text_color=THEME['text_secondary'], font=ctk.CTkFont(size=13))

        for widget in self.content.winfo_children():
            widget.destroy()

        wrapper = ctk.CTkFrame(self.content, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        views = {
            "dashboard": DashboardView,
            "documents": DocumentsView,
            "shares": SharesView,
            "tasks": TasksView,
            "family": FamilyView,
            "chat": ChatView,
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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        greeting = "Bonjour" if 5 <= datetime.now().hour < 18 else "Bonsoir"
        ctk.CTkLabel(header, text=f"{greeting}, {self.app.current_user.first_name}", font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        # Stats
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 16))

        self.app.db_session.expire_all()
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
            ("Documents", doc_count, "Total stockes", None, lambda: self.main_frame.show_view("documents")),
            ("Taches actives", task_count, "En cours", THEME['accent'], lambda: self.main_frame.show_view("tasks")),
            ("En retard", overdue_count, "A traiter", THEME['error_text'] if overdue_count > 0 else None, lambda: self.main_frame.show_view("tasks")),
            ("Notifications", notif_count, "Non lues", THEME['warning_text'] if notif_count > 0 else None, lambda: self.main_frame.show_view("notifications")),
        ]

        for i, (title, value, subtitle, color, command) in enumerate(stats):
            card = StatCard(stats_frame, title=title, value=value, subtitle=subtitle, color=color, command=command)
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))

        # Taches a venir — pleine largeur
        tasks_card = GlassCard(self)
        tasks_card.pack(fill="both", expand=True)

        tasks_header = ctk.CTkFrame(tasks_card, fg_color="transparent")
        tasks_header.pack(fill="x", padx=20, pady=(20, 12))

        ctk.CTkLabel(tasks_header, text="Taches a venir", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        btn_row = ctk.CTkFrame(tasks_header, fg_color="transparent")
        btn_row.pack(side="right")
        GlassButton(btn_row, text="+ Document", command=lambda: self.open_add_document(), variant="primary", width=100).pack(side="left", padx=4)
        GlassButton(btn_row, text="+ Tache", command=lambda: self.open_add_task(), variant="success", width=80).pack(side="left", padx=4)

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

    def create_task_row(self, parent, task):
        row = ctk.CTkFrame(parent, fg_color=THEME['bg_tertiary'], corner_radius=10)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        priority_colors = {'high': THEME['error'], 'urgent': THEME['error'], 'normal': THEME['warning'], 'low': THEME['success']}
        p_color = priority_colors.get(task.priority, THEME['text_muted'])

        indicator = ctk.CTkFrame(inner, fg_color=p_color, width=3, height=24, corner_radius=2)
        indicator.pack(side="left", padx=(0, 12))

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
# DOCUMENTS
# ============================================================================

class DocumentsView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(header, text="Documents", font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        GlassButton(header, text="+ Ajouter", command=self.add_document, variant="primary", width=100).pack(side="right")

        # filtre compact
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_entry = GlassEntry(filter_frame, placeholder="Rechercher...", width=220)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filters())

        self.type_filter = ctk.CTkComboBox(
            filter_frame, values=["Tous types", "pdf", "image", "word", "excel", "text", "other"],
            width=120, fg_color=THEME['bg_secondary'], border_color=THEME['border'],
            button_color=THEME['accent'], dropdown_fg_color=THEME['bg_secondary'], corner_radius=10,
            command=lambda v: self.apply_filters()
        )
        self.type_filter.pack(side="left", padx=8)

        self.sort_var = ctk.CTkComboBox(
            filter_frame, values=["Plus recents", "Nom A-Z", "Taille"],
            width=120, fg_color=THEME['bg_secondary'], border_color=THEME['border'],
            button_color=THEME['accent'], dropdown_fg_color=THEME['bg_secondary'], corner_radius=10,
            command=lambda v: self.apply_filters()
        )
        self.sort_var.pack(side="left")

        # onglets
        self.tabs = ctk.CTkTabview(self, fg_color=THEME['bg_secondary'], segmented_button_fg_color=THEME['bg_tertiary'],
                                    segmented_button_selected_color=THEME['accent'], corner_radius=12)
        self.tabs.pack(fill="both", expand=True)
        self.tabs.add("Dossiers")
        self.tabs.add("Tous les documents")
        self.tabs.add("Partages avec moi")

        self.folders_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Dossiers"), fg_color="transparent")
        self.folders_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.my_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Tous les documents"), fg_color="transparent")
        self.my_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.shared_scroll = ctk.CTkScrollableFrame(self.tabs.tab("Partages avec moi"), fg_color="transparent")
        self.shared_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.apply_filters()

    def apply_filters(self):
        # nettoyer
        for w in self.folders_scroll.winfo_children():
            w.destroy()
        for w in self.my_scroll.winfo_children():
            w.destroy()
        for w in self.shared_scroll.winfo_children():
            w.destroy()

        # === ONGLET DOSSIERS ===
        folders = self.app.db_session.query(Folder).filter_by(
            owner_id=self.app.current_user.id, parent_id=None
        ).order_by(Folder.category).all()

        folder_icons = {'Administratif': 'ADM', 'Sante': 'SAN', 'Banque': 'BNQ', 'Logement': 'LOG', 'Autres': 'AUT'}
        folder_colors = {'Administratif': '#007AFF', 'Sante': '#34C759', 'Banque': '#FF9500', 'Logement': '#AF52DE', 'Autres': '#8E8E93'}

        # grille de dossiers style web (cards)
        grid = ctk.CTkFrame(self.folders_scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 12))

        col = 0
        row_frame = None
        for i, folder in enumerate(folders):
            if col == 0:
                row_frame = ctk.CTkFrame(grid, fg_color="transparent")
                row_frame.pack(fill="x", pady=4)

            ic_color = folder_colors.get(folder.category, THEME['accent'])
            doc_count = folder.documents.count()

            card = ctk.CTkFrame(row_frame, fg_color=THEME['bg_tertiary'], corner_radius=14, height=130, cursor="hand2")
            card.pack(side="left", fill="x", expand=True, padx=4)
            card.pack_propagate(False)
            card.bind("<Button-1>", lambda e, f=folder: self.show_folder_content(f))

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=18, pady=16)
            card_inner.bind("<Button-1>", lambda e, f=folder: self.show_folder_content(f))

            # icone + nom
            top = ctk.CTkFrame(card_inner, fg_color="transparent")
            top.pack(fill="x")
            top.bind("<Button-1>", lambda e, f=folder: self.show_folder_content(f))

            ic_box = ctk.CTkFrame(top, fg_color=ic_color, width=40, height=40, corner_radius=10)
            ic_box.pack(side="left")
            ic_box.pack_propagate(False)
            ic_text = folder_icons.get(folder.category, 'DOS')
            ctk.CTkLabel(ic_box, text=ic_text, font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(top, text=folder.name, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=THEME['text_primary'], cursor="hand2").pack(side="left", padx=10)

            # nb docs total (y compris sous-dossiers)
            total = doc_count
            for s in folder.subfolders.all():
                total += s.documents.count()
            ctk.CTkLabel(card_inner, text=f"{total} document(s)", font=ctk.CTkFont(size=11),
                        text_color=THEME['text_muted'], cursor="hand2").pack(anchor="w", pady=(8, 0))
            ctk.CTkLabel(card_inner, text=folder.category, font=ctk.CTkFont(size=10),
                        text_color=THEME['text_muted']).pack(anchor="w")

            col += 1
            if col >= 3:
                col = 0

        # remplir la derniere ligne si incomplete
        if col > 0 and row_frame:
            for _ in range(3 - col):
                ctk.CTkFrame(row_frame, fg_color="transparent").pack(side="left", fill="x", expand=True, padx=4)

        search = self.search_entry.get().strip().lower()
        type_filter = self.type_filter.get()
        sort = self.sort_var.get()

        self.app.db_session.expire_all()

        # mes docs
        query = self.app.db_session.query(Document).filter_by(owner_id=self.app.current_user.id)
        if search:
            query = query.filter(Document.name.ilike(f"%{search}%"))
        if type_filter != "Tous types":
            query = query.filter(Document.file_type == type_filter)

        if sort == "Plus anciens":
            query = query.order_by(Document.created_at.asc())
        elif sort == "Nom A-Z":
            query = query.order_by(Document.name.asc())
        elif sort == "Nom Z-A":
            query = query.order_by(Document.name.desc())
        elif sort == "Taille":
            query = query.order_by(Document.file_size.desc())
        else:
            query = query.order_by(Document.created_at.desc())

        docs = query.all()
        if docs:
            for doc in docs:
                self.create_doc_row(self.my_scroll, doc)
        else:
            ctk.CTkLabel(self.my_scroll, text="Aucun document", text_color=THEME['text_muted']).pack(pady=40)

        # docs partages avec moi
        from app.models.permission import Permission
        shared_perms = self.app.db_session.query(Permission).filter_by(user_id=self.app.current_user.id).all()
        shared_docs = []
        for p in shared_perms:
            if p.is_valid() and p.document:
                shared_docs.append((p.document, p))

        if shared_docs:
            for doc, perm in shared_docs:
                self.create_doc_row(self.shared_scroll, doc, shared_by=perm)
        else:
            ctk.CTkLabel(self.shared_scroll, text="Aucun document partage", text_color=THEME['text_muted']).pack(pady=40)

    def create_doc_row(self, parent, doc, shared_by=None):
        row = GlassCard(parent)
        row.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        file_icons = {'pdf': 'PDF', 'jpg': 'IMG', 'jpeg': 'IMG', 'png': 'IMG', 'image': 'IMG', 'doc': 'DOC', 'docx': 'DOC', 'word': 'DOC', 'xls': 'XLS', 'xlsx': 'XLS', 'excel': 'XLS', 'md': 'MD', 'text': 'TXT'}
        file_colors = {'pdf': '#FF453A', 'image': '#FF9F0A', 'jpg': '#FF9F0A', 'jpeg': '#FF9F0A', 'png': '#FF9F0A', 'word': '#007AFF', 'doc': '#007AFF', 'docx': '#007AFF', 'excel': '#30D158', 'xls': '#30D158', 'xlsx': '#30D158', 'md': '#5856D6', 'text': '#86868B'}
        file_type = doc.file_type.lower() if doc.file_type else 'file'
        icon_text = file_icons.get(file_type, 'FILE')
        icon_color = file_colors.get(file_type, THEME['accent'])

        icon_box = ctk.CTkFrame(inner, fg_color=icon_color, width=44, height=44, corner_radius=12)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon_text, font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=14)

        ctk.CTkLabel(info, text=doc.name, font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")

        # meta : taille + date + dossier
        size_str = doc.get_human_readable_size() if doc.file_size else ""
        folder_str = doc.folder.name if doc.folder else ""
        meta_parts = [p for p in [file_type.upper(), size_str, folder_str, doc.created_at.strftime('%d/%m/%Y')] if p]
        ctk.CTkLabel(info, text=" | ".join(meta_parts), font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(anchor="w")

        # info partage
        if shared_by:
            owner_name = doc.owner.family_title or doc.owner.first_name if doc.owner else "?"
            rights = []
            if shared_by.can_edit:
                rights.append("edit")
            if shared_by.can_download:
                rights.append("download")
            rights_text = f"Partage par {owner_name} ({', '.join(rights) if rights else 'lecture'})"
            ctk.CTkLabel(info, text=rights_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['accent']).pack(anchor="w")

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        GlassButton(actions, text="Ouvrir", command=lambda d=doc: self.view_doc(d), variant="secondary", width=70).pack(side="left", padx=4)
        if not shared_by:
            GlassButton(actions, text="Partager", command=lambda d=doc: self.share_doc(d), variant="primary", width=80).pack(side="left", padx=4)
            GlassButton(actions, text="Suppr.", command=lambda d=doc: self.delete_doc(d), variant="danger", width=60).pack(side="left")

    def share_doc(self, doc):
        """popup partage doc avec membres famille"""
        from app.models.permission import Permission

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Partager : {doc.name}")
        dialog.geometry("500x550")
        dialog.configure(fg_color=THEME['bg_primary'])
        dialog.grab_set()

        h = ctk.CTkFrame(dialog, fg_color=THEME['bg_secondary'], height=50, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)
        ctk.CTkLabel(h, text=f"Partager \"{doc.name}\"", font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=THEME['text_primary']).pack(side="left", padx=20, pady=12)

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=12)

        # recup membres famille (sauf moi)
        families = self.app.db_session.query(Family).join(Family.members).filter(
            Family.members.any(user_id=self.app.current_user.id)
        ).all()

        members = []
        seen = set()
        for fam in families:
            for m in fam.members.all():
                if m.user_id != self.app.current_user.id and m.user_id not in seen:
                    members.append(m)
                    seen.add(m.user_id)

        if not members:
            ctk.CTkLabel(form, text="Aucun membre de famille disponible", text_color=THEME['text_muted']).pack(pady=30)
            return

        # selection membres (checkboxes)
        ctk.CTkLabel(form, text="PARTAGER AVEC", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", pady=(0, 8))

        member_vars = {}
        for m in members:
            var = ctk.BooleanVar(value=False)
            name = m.user.full_name
            if m.user.family_title:
                name = f"{m.user.family_title} - {m.user.full_name}"
            cb = ctk.CTkCheckBox(form, text=name, variable=var, font=ctk.CTkFont(size=12),
                                fg_color=THEME['accent'], hover_color=THEME['accent'])
            cb.pack(anchor="w", pady=3)
            member_vars[m.user_id] = var

        # droits
        ctk.CTkFrame(form, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
        ctk.CTkLabel(form, text="DROITS", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", pady=(0, 8))

        can_edit_var = ctk.BooleanVar(value=False)
        can_dl_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(form, text="Peut modifier", variable=can_edit_var, font=ctk.CTkFont(size=12),
                        fg_color=THEME['accent'], hover_color=THEME['accent']).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(form, text="Peut telecharger", variable=can_dl_var, font=ctk.CTkFont(size=12),
                        fg_color=THEME['accent'], hover_color=THEME['accent']).pack(anchor="w", pady=2)

        # duree
        ctk.CTkFrame(form, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
        ctk.CTkLabel(form, text="DUREE", font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['text_muted']).pack(anchor="w", pady=(0, 8))

        duration_var = ctk.StringVar(value="30j")
        durations_frame = ctk.CTkFrame(form, fg_color="transparent")
        durations_frame.pack(fill="x", pady=(0, 8))

        for label, val in [("1 semaine", "7j"), ("30 jours", "30j"), ("1 an", "365j"), ("Permanent", "perm")]:
            ctk.CTkRadioButton(durations_frame, text=label, variable=duration_var, value=val,
                              font=ctk.CTkFont(size=11), fg_color=THEME['accent'],
                              hover_color=THEME['accent']).pack(side="left", padx=6)

        # bouton partager
        ctk.CTkFrame(form, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)

        def do_share():
            selected = [uid for uid, var in member_vars.items() if var.get()]
            if not selected:
                from tkinter import messagebox
                messagebox.showwarning("Attention", "Selectionnez au moins un membre")
                return

            dur = duration_var.get()
            if dur == "perm":
                end_date = None
            else:
                days = int(dur.replace("j", ""))
                end_date = date.today() + timedelta(days=days)

            count = 0
            for uid in selected:
                existing = self.app.db_session.query(Permission).filter_by(document_id=doc.id, user_id=uid).first()
                if existing:
                    existing.can_edit = can_edit_var.get()
                    existing.can_download = can_dl_var.get()
                    existing.end_date = end_date
                else:
                    perm = Permission(
                        document_id=doc.id, user_id=uid, granted_by=self.app.current_user.id,
                        can_view=True, can_edit=can_edit_var.get(), can_download=can_dl_var.get(),
                        end_date=end_date
                    )
                    self.app.db_session.add(perm)
                count += 1

            Log.create_log(user_id=self.app.current_user.id, action='document_share', document_id=doc.id, details=f'Partage desktop avec {count} membre(s)')
            self.app.db_session.commit()
            from tkinter import messagebox
            messagebox.showinfo("Partage", f"Document partage avec {count} membre(s)")
            dialog.destroy()

        GlassButton(form, text="Partager", command=do_share, variant="primary").pack(fill="x", pady=(4, 0))

    def show_folder_content(self, folder):
        """popup contenu dossier"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Dossier : {folder.name}")
        dialog.geometry("600x500")
        dialog.configure(fg_color=THEME['bg_primary'])
        dialog.grab_set()

        h = ctk.CTkFrame(dialog, fg_color=THEME['bg_secondary'], height=50, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)
        ctk.CTkLabel(h, text=f"{folder.get_path()}", font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=THEME['text_primary']).pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(h, text=f"{folder.document_count} document(s)", font=ctk.CTkFont(size=11),
                    text_color=THEME['text_muted']).pack(side="right", padx=20)

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        docs = folder.documents.order_by(Document.updated_at.desc()).all()
        if not docs:
            ctk.CTkLabel(scroll, text="Dossier vide", text_color=THEME['text_muted']).pack(pady=40)
        else:
            for doc in docs:
                self.create_doc_row(scroll, doc)

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
        if messagebox.askyesno("Confirmer", f"Supprimer '{doc.name}' ?\n\nCette action est irreversible."):
            Log.create_log(user_id=self.app.current_user.id, action='document_delete', details=f'Suppression desktop: {doc.name}')
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
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Nouveau document", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(form, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = GlassEntry(form, placeholder="Titre du document")
        self.title_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Categorie", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.category = ctk.CTkComboBox(form, values=['Administratif', 'Sante', 'Banque', 'Logement', 'Autres'], fg_color=THEME['bg_secondary'], border_color=THEME['border'], corner_radius=10)
        self.category.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.desc = ctk.CTkTextbox(form, height=80, fg_color=THEME['bg_secondary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'], corner_radius=10)
        self.desc.pack(fill="x", pady=(0, 16))

        file_frame = ctk.CTkFrame(form, fg_color=THEME['bg_secondary'], corner_radius=10, border_width=1, border_color=THEME['border'])
        file_frame.pack(fill="x", pady=(0, 20))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(padx=14, pady=12, fill="x")

        self.file_label = ctk.CTkLabel(file_inner, text="Aucun fichier selectionne", text_color=THEME['text_muted'], font=ctk.CTkFont(size=12))
        self.file_label.pack(side="left")

        GlassButton(file_inner, text="Parcourir", command=self.select_file, variant="secondary", width=90).pack(side="right")

        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        GlassButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        GlassButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

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

        if self.selected_file:
            # check taille (16 Mo max, comme la version web)
            file_size = os.path.getsize(self.selected_file)
            if file_size > 16 * 1024 * 1024:
                messagebox.showerror("Fichier trop volumineux", "Le fichier depasse la taille maximale autorisee (16 Mo).")
                return
            import shutil, uuid
            upload_folder = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER')
            ext = os.path.splitext(self.selected_file)[1]
            original_name = os.path.basename(self.selected_file)
            new_filename = f"{uuid.uuid4()}{ext}"
            shutil.copy2(self.selected_file, os.path.join(upload_folder, new_filename))
        else:
            original_name = f"{title}.txt"
            new_filename = original_name
            ext = '.txt'

        doc = Document(
            name=title,
            original_filename=original_name,
            stored_filename=new_filename,
            description=self.desc.get("1.0", "end").strip(),
            file_type=ext[1:] if ext else None,
            owner_id=self.app.current_user.id
        )

        self.app.db_session.add(doc)
        self.app.db_session.flush()
        Log.create_log(user_id=self.app.current_user.id, action='document_upload', document_id=doc.id, details=f'Ajout desktop: {title}')
        self.app.db_session.commit()
        self.destroy()


class MarkdownDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.title("Nouvelle note")
        self.geometry("700x600")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Nouvelle note Markdown", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = GlassEntry(col1, placeholder="Titre de la note")
        self.title_entry.pack(fill="x")

        col2 = ctk.CTkFrame(row1, fg_color="transparent", width=180)
        col2.pack(side="right")
        col2.pack_propagate(False)
        ctk.CTkLabel(col2, text="Categorie", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.category = ctk.CTkComboBox(col2, values=['Notes', 'Administratif', 'Sante', 'Autres'], fg_color=THEME['bg_secondary'], border_color=THEME['border'], corner_radius=10)
        self.category.set('Notes')
        self.category.pack(fill="x")

        ctk.CTkLabel(form, text="Contenu (Markdown supporte)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(8, 4))

        self.content = ctk.CTkTextbox(form, fg_color=THEME['bg_secondary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=12), corner_radius=10)
        self.content.pack(fill="both", expand=True)
        self.content.insert("1.0", "# Titre\n\nVotre contenu ici...\n\n## Section\n\n- Element 1\n- Element 2\n")

        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        GlassButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        GlassButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

    def save(self):
        title = self.title_entry.get().strip()
        content = self.content.get("1.0", "end").strip()

        if not title:
            messagebox.showerror("Erreur", "Le titre est obligatoire")
            return

        import uuid
        docs_folder = os.environ.get('FAMILIDOCS_DOCS_FOLDER')
        filename = f"{uuid.uuid4()}.md"
        filepath = os.path.join(docs_folder, filename)

        encrypted_content = self.app.encryption.encrypt(content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)

        doc = Document(
            name=title,
            original_filename=f"{title}.md",
            stored_filename=filename,
            description="Note Markdown",
            file_type='md',
            owner_id=self.app.current_user.id
        )

        self.app.db_session.add(doc)
        self.app.db_session.flush()
        Log.create_log(user_id=self.app.current_user.id, action='document_upload', document_id=doc.id, details=f'Note desktop: {title}')
        self.app.db_session.commit()
        self.destroy()


class MarkdownViewDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, doc):
        super().__init__(parent)
        self.app = app
        self.doc = doc

        self.title(doc.name)
        self.geometry("750x600")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=self.doc.name, font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)
        GlassButton(header, text="Modifier", command=self.edit, variant="secondary", width=80).pack(side="right", padx=24)

        content = ""
        if self.doc.stored_filename:
            docs_folder = os.environ.get('FAMILIDOCS_DOCS_FOLDER')
            filepath = os.path.join(docs_folder, self.doc.stored_filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    encrypted = f.read()
                content = self.app.encryption.decrypt(encrypted)

        text_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=28, pady=20)

        text = ctk.CTkTextbox(text_frame, fg_color=THEME['bg_secondary'], text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=12), border_width=0, corner_radius=10)
        text.pack(fill="both", expand=True)
        text.insert("1.0", content)
        text.configure(state="disabled")

    def edit(self):
        self.destroy()


class DocumentViewDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, doc):
        super().__init__(parent)
        self.app = app
        self.doc = doc

        self.title(doc.name)
        self.geometry("550x400")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        Log.create_log(user_id=app.current_user.id, action='document_view', document_id=doc.id, details=f'Vue desktop: {doc.name}')
        app.db_session.commit()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=self.doc.name, font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=20)

        meta_card = GlassCard(content)
        meta_card.pack(fill="x")

        meta_inner = ctk.CTkFrame(meta_card, fg_color="transparent")
        meta_inner.pack(padx=20, pady=16, fill="x")

        infos = [
            ("Description", self.doc.description or "Non definie"),
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
            desc_card = GlassCard(content)
            desc_card.pack(fill="x")
            ctk.CTkLabel(desc_card, text=self.doc.description, text_color=THEME['text_secondary'], wraplength=450, justify="left").pack(padx=20, pady=14, anchor="w")

        if self.doc.stored_filename:
            GlassButton(content, text="Ouvrir le fichier", command=self.open_file, variant="primary", width=180).pack(pady=24)

    def open_file(self):
        upload_folder = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER')
        path = os.path.join(upload_folder, self.doc.stored_filename)
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Erreur", "Fichier introuvable")


# === PARTAGES ===

class SharesView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Partages", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 16))

        from app.models.permission import Permission

        tabs = ctk.CTkTabview(self, fg_color=THEME['bg_secondary'], segmented_button_fg_color=THEME['bg_tertiary'],
                               segmented_button_selected_color=THEME['accent'], corner_radius=12)
        tabs.pack(fill="both", expand=True)
        tabs.add("Mes partages")
        tabs.add("Partages avec moi")

        # === MES PARTAGES (docs que j'ai partages) ===
        my_scroll = ctk.CTkScrollableFrame(tabs.tab("Mes partages"), fg_color="transparent")
        my_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        my_perms = self.app.db_session.query(Permission).filter_by(granted_by=self.app.current_user.id).all()

        if not my_perms:
            ctk.CTkLabel(my_scroll, text="Vous n'avez partage aucun document", text_color=THEME['text_muted']).pack(pady=40)
        else:
            # grouper par document
            docs_shared = {}
            for p in my_perms:
                if p.document_id not in docs_shared:
                    docs_shared[p.document_id] = {'doc': p.document, 'perms': []}
                docs_shared[p.document_id]['perms'].append(p)

            for doc_id, data in docs_shared.items():
                doc = data['doc']
                if not doc:
                    continue

                card = GlassCard(my_scroll)
                card.pack(fill="x", pady=4)
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(fill="x", padx=16, pady=12)

                # nom doc
                ctk.CTkLabel(inner, text=doc.name, font=ctk.CTkFont(size=14, weight="bold"),
                            text_color=THEME['text_primary']).pack(anchor="w")

                # liste des personnes avec qui c'est partage
                for perm in data['perms']:
                    if not perm.granted_user:
                        continue

                    perm_row = ctk.CTkFrame(inner, fg_color=THEME['bg_tertiary'], corner_radius=8)
                    perm_row.pack(fill="x", pady=3)
                    perm_inner = ctk.CTkFrame(perm_row, fg_color="transparent")
                    perm_inner.pack(fill="x", padx=12, pady=8)

                    # nom personne
                    user_name = perm.granted_user.full_name
                    if perm.granted_user.family_title:
                        user_name = f"{perm.granted_user.family_title} - {user_name}"
                    ctk.CTkLabel(perm_inner, text=user_name, font=ctk.CTkFont(size=12),
                                text_color=THEME['text_primary']).pack(side="left")

                    # droits
                    rights = []
                    if perm.can_edit:
                        rights.append("edit")
                    if perm.can_download:
                        rights.append("dl")
                    rights_text = ", ".join(rights) if rights else "lecture"

                    # expiration
                    exp_text = ""
                    if perm.end_date:
                        days_left = (perm.end_date - date.today()).days
                        if days_left < 0:
                            exp_text = " | Expire"
                        else:
                            exp_text = f" | {days_left}j restants"

                    ctk.CTkLabel(perm_inner, text=f"{rights_text}{exp_text}", font=ctk.CTkFont(size=10),
                                text_color=THEME['text_muted']).pack(side="left", padx=8)

                    # bouton revoquer
                    GlassButton(perm_inner, text="Revoquer", variant="danger", width=80,
                               command=lambda p=perm: self.revoke_share(p)).pack(side="right")

        # === PARTAGES AVEC MOI ===
        shared_scroll = ctk.CTkScrollableFrame(tabs.tab("Partages avec moi"), fg_color="transparent")
        shared_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        received = self.app.db_session.query(Permission).filter_by(user_id=self.app.current_user.id).all()

        if not received:
            ctk.CTkLabel(shared_scroll, text="Aucun document partage avec vous", text_color=THEME['text_muted']).pack(pady=40)
        else:
            for perm in received:
                if not perm.document or not perm.is_valid():
                    continue

                row = GlassCard(shared_scroll)
                row.pack(fill="x", pady=4)
                r_inner = ctk.CTkFrame(row, fg_color="transparent")
                r_inner.pack(fill="x", padx=16, pady=12)

                ctk.CTkLabel(r_inner, text=perm.document.name, font=ctk.CTkFont(size=13, weight="bold"),
                            text_color=THEME['text_primary']).pack(side="left")

                # qui a partage
                granter_name = "?"
                if perm.granting_user:
                    granter_name = perm.granting_user.family_title or perm.granting_user.first_name
                rights = []
                if perm.can_edit:
                    rights.append("edit")
                if perm.can_download:
                    rights.append("dl")
                info = f"Par {granter_name} | {', '.join(rights) if rights else 'lecture'}"
                if perm.end_date:
                    days_left = (perm.end_date - date.today()).days
                    info += f" | {days_left}j"
                ctk.CTkLabel(r_inner, text=info, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(side="left", padx=12)

                GlassButton(r_inner, text="Ouvrir", variant="secondary", width=70,
                           command=lambda d=perm.document: self.view_shared_doc(d)).pack(side="right")

    def view_shared_doc(self, doc):
        """ouvre doc partage"""
        if doc.file_type and doc.file_type.lower() == 'md':
            MarkdownViewDialog(self, self.app, doc)
        else:
            DocumentViewDialog(self, self.app, doc)

    def revoke_share(self, perm):
        from tkinter import messagebox
        user_name = perm.granted_user.full_name if perm.granted_user else "?"
        doc_name = perm.document.name if perm.document else "?"
        confirm = messagebox.askyesno("Revoquer", f"Revoquer l'acces de {user_name} a \"{doc_name}\" ?")
        if confirm:
            Log.create_log(user_id=self.app.current_user.id, action='permission_revoke', document_id=perm.document_id, details=f'Revocation desktop: {doc_name}')
            self.app.db_session.delete(perm)
            self.app.db_session.commit()
            self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


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

        ctk.CTkLabel(header, text="Taches", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        GlassButton(header, text="Nouvelle tache", command=self.add_task, variant="primary").pack(side="right")

        tabs = ctk.CTkTabview(self, fg_color=THEME['bg_secondary'], segmented_button_fg_color=THEME['bg_tertiary'], segmented_button_selected_color=THEME['accent'], corner_radius=12)
        tabs.pack(fill="both", expand=True)

        tabs.add("Mes taches")
        tabs.add("Assignees par moi")
        tabs.add("Terminees")

        # mes taches (owner ou assigned_to)
        from sqlalchemy import or_
        pending = self.app.db_session.query(Task).filter(
            or_(Task.owner_id == self.app.current_user.id, Task.assigned_to_id == self.app.current_user.id),
            Task.status.notin_(['completed', 'cancelled'])
        ).order_by(Task.due_date).all()
        self.show_tasks(tabs.tab("Mes taches"), pending, completed=False)

        # taches que j'ai assignees a d'autres
        assigned_by_me = self.app.db_session.query(Task).filter(
            Task.owner_id == self.app.current_user.id,
            Task.assigned_to_id.isnot(None),
            Task.assigned_to_id != self.app.current_user.id,
            Task.status.notin_(['completed', 'cancelled'])
        ).order_by(Task.due_date).all()
        self.show_tasks(tabs.tab("Assignees par moi"), assigned_by_me, completed=False)

        completed = self.app.db_session.query(Task).filter(
            or_(Task.owner_id == self.app.current_user.id, Task.assigned_to_id == self.app.current_user.id),
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
            row = GlassCard(scroll)
            row.pack(fill="x", pady=3)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            if not completed:
                cb = ctk.CTkCheckBox(inner, text="", command=lambda t=task: self.complete_task(t), fg_color=THEME['success'], hover_color=THEME['success'], width=20)
                cb.pack(side="left")
            else:
                done_badge = ctk.CTkFrame(inner, fg_color=THEME['success'], width=20, height=20, corner_radius=10)
                done_badge.pack(side="left")
                done_badge.pack_propagate(False)
                ctk.CTkLabel(done_badge, text="", font=ctk.CTkFont(size=8)).place(relx=0.5, rely=0.5, anchor="center")

            info = ctk.CTkFrame(inner, fg_color="transparent", cursor="hand2")
            info.pack(side="left", padx=14, fill="x", expand=True)
            info.bind("<Button-1>", lambda e, t=task: self.show_task_detail(t))

            title_lbl = ctk.CTkLabel(info, text=task.title, font=ctk.CTkFont(size=13), text_color=THEME['text_primary'], cursor="hand2")
            title_lbl.pack(anchor="w")
            title_lbl.bind("<Button-1>", lambda e, t=task: self.show_task_detail(t))

            # indication assignation
            assign_text = ""
            if task.assigned_to_id and task.assigned_to_id != task.owner_id:
                if task.assigned_to_id == self.app.current_user.id:
                    owner_name = task.owner.family_title or task.owner.first_name if task.owner else "?"
                    assign_text = f"Assignee par {owner_name}"
                else:
                    assigned_name = task.assigned_to.family_title or task.assigned_to.first_name if task.assigned_to else "?"
                    assign_text = f"Assignee a {assigned_name}"

            if assign_text:
                assign_lbl = ctk.CTkLabel(info, text=assign_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME['accent'], cursor="hand2")
                assign_lbl.pack(anchor="w")
                assign_lbl.bind("<Button-1>", lambda e, t=task: self.show_task_detail(t))
            elif task.description:
                desc = task.description[:50] + "..." if len(task.description) > 50 else task.description
                desc_lbl = ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=11), text_color=THEME['text_muted'], cursor="hand2")
                desc_lbl.pack(anchor="w")
                desc_lbl.bind("<Button-1>", lambda e, t=task: self.show_task_detail(t))

            if task.due_date and not completed:
                is_overdue = task.due_date < date.today()
                date_color = THEME['error_text'] if is_overdue else THEME['text_secondary']
                ctk.CTkLabel(inner, text=task.due_date.strftime("%d/%m/%Y"), text_color=date_color, font=ctk.CTkFont(size=11)).pack(side="right")

    def show_task_detail(self, task):
        """popup detail tache"""
        detail = ctk.CTkToplevel(self)
        detail.title(f"Tache : {task.title}")
        detail.geometry("500x520")
        detail.configure(fg_color=THEME['bg_primary'])
        detail.grab_set()

        # header
        h = ctk.CTkFrame(detail, fg_color=THEME['bg_secondary'], height=50, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)
        ctk.CTkLabel(h, text=task.title, font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=20, pady=12)

        content = ctk.CTkScrollableFrame(detail, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # infos
        infos = [
            ("Statut", task.status.replace('_', ' ').capitalize()),
            ("Priorite", task.priority.capitalize()),
            ("Echeance", task.due_date.strftime("%d/%m/%Y") if task.due_date else "Aucune"),
            ("Rappel", f"{task.reminder_days} jours avant"),
        ]

        if task.assigned_to:
            infos.append(("Assigne a", task.assigned_to.full_name))
        if task.document:
            infos.append(("Document lie", task.document.name))
        if task.completed_at:
            infos.append(("Termine le", task.completed_at.strftime("%d/%m/%Y %H:%M")))

        for label, value in infos:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary'], width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), text_color=THEME['text_primary']).pack(side="left")

        # description
        if task.description:
            ctk.CTkFrame(content, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
            ctk.CTkLabel(content, text="Description", font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary']).pack(anchor="w")
            ctk.CTkLabel(content, text=task.description, font=ctk.CTkFont(size=12), text_color=THEME['text_primary'], wraplength=440, justify="left").pack(anchor="w", pady=(4, 0))

        # boutons action
        ctk.CTkFrame(content, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        if task.status not in ('completed', 'cancelled'):
            statuses = [('En cours', 'in_progress'), ('Termine', 'completed'), ('Annule', 'cancelled')]
            for label, status in statuses:
                variant = 'primary' if status == 'completed' else 'secondary'
                if status == 'cancelled':
                    variant = 'danger'
                GlassButton(btn_frame, text=label, variant=variant, width=100,
                           command=lambda s=status, t=task, d=detail: self._change_status(t, s, d)).pack(side="left", padx=4)

        GlassButton(btn_frame, text="Fermer", variant="ghost", width=80, command=detail.destroy).pack(side="right")

    def _change_status(self, task, status, dialog):
        task.status = status
        if status == 'completed':
            task.completed_at = datetime.utcnow()
        action = 'task_complete' if status == 'completed' else 'task_edit'
        Log.create_log(user_id=self.app.current_user.id, action=action, details=f'Tache desktop: {task.title} -> {status}')
        self.app.db_session.commit()
        dialog.destroy()
        self.refresh()

    def add_task(self):
        dialog = TaskDialog(self, self.app)
        self.wait_window(dialog)
        self.refresh()

    def complete_task(self, task):
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        Log.create_log(user_id=self.app.current_user.id, action='task_complete', details=f'Tache terminee desktop: {task.title}')
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
        self.geometry("480x500")
        self.configure(fg_color=THEME['bg_primary'])
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Nouvelle tache", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(form, text="Titre", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_entry = GlassEntry(form, placeholder="Titre de la tache")
        self.title_entry.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.desc = ctk.CTkTextbox(form, height=70, fg_color=THEME['bg_secondary'], border_color=THEME['border'], border_width=1, text_color=THEME['text_primary'], corner_radius=10)
        self.desc.pack(fill="x", pady=(0, 14))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))

        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(col1, text="Priorite", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.priority = ctk.CTkComboBox(col1, values=['low', 'normal', 'high', 'urgent'], fg_color=THEME['bg_secondary'], border_color=THEME['border'], corner_radius=10)
        self.priority.set('normal')
        self.priority.pack(fill="x")

        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(col2, text="Date limite", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.date_entry = GlassEntry(col2, placeholder="JJ/MM/AAAA")
        self.date_entry.pack(fill="x")

        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        GlassButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        GlassButton(btn_frame, text="Creer", command=self.save, variant="success", width=90).pack(side="left")

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
        self.app.db_session.flush()
        Log.create_log(user_id=self.app.current_user.id, action='task_create', details=f'Tache desktop: {title}')
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
        ctk.CTkLabel(self, text="Famille", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 20))

        families = self.app.db_session.query(Family).join(Family.members).filter(
            Family.members.any(user_id=self.app.current_user.id)
        ).all()

        if families:
            for family in families:
                self.show_family(family)
        else:
            self.show_no_family()

    def show_no_family(self):
        card = GlassCard(self)
        card.pack(fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(pady=50, padx=50)
        ctk.CTkLabel(inner, text="Aucune famille", font=ctk.CTkFont(size=16, weight="bold"), text_color=THEME['text_primary']).pack(pady=(12, 4))
        ctk.CTkLabel(inner, text="Creez une famille ou rejoignez-en une", text_color=THEME['text_muted']).pack()
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(pady=24)
        GlassButton(btns, text="Creer une famille", command=self.create_family, variant="primary", width=150).pack(side="left", padx=8)

    def show_family(self, family):
        # onglets famille
        tabs = ctk.CTkTabview(self, fg_color=THEME['bg_secondary'], segmented_button_fg_color=THEME['bg_tertiary'],
                               segmented_button_selected_color=THEME['accent'], corner_radius=12)
        tabs.pack(fill="both", expand=True)
        tabs.add("Membres")
        tabs.add("Taches famille")

        self.family = family
        can_manage = family.can_manage(self.app.current_user.id)

        # === ONGLET MEMBRES ===
        members_tab = tabs.tab("Membres")

        header = ctk.CTkFrame(members_tab, fg_color="transparent")
        header.pack(fill="x", pady=(8, 12), padx=12)
        ctk.CTkLabel(header, text=family.name, font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(side="left")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        if can_manage:
            GlassButton(btn_frame, text="Inviter", command=lambda f=family: self.invite_member(f), variant="primary", width=90).pack(side="left", padx=4)
        ctk.CTkLabel(btn_frame, text=f"{family.member_count} membre(s)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="left", padx=(8, 0))

        members_scroll = ctk.CTkScrollableFrame(members_tab, fg_color="transparent")
        members_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        for member in family.members.all():
            m_row = ctk.CTkFrame(members_scroll, fg_color=THEME['bg_tertiary'], corner_radius=10)
            m_row.pack(fill="x", pady=3)
            m_inner = ctk.CTkFrame(m_row, fg_color="transparent")
            m_inner.pack(fill="x", padx=14, pady=10)

            initials = f"{member.user.first_name[0]}{member.user.last_name[0]}".upper()
            avatar = ctk.CTkFrame(m_inner, fg_color=THEME['accent'], width=36, height=36, corner_radius=18)
            avatar.pack(side="left")
            avatar.pack_propagate(False)
            ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

            info_frame = ctk.CTkFrame(m_inner, fg_color="transparent")
            info_frame.pack(side="left", padx=12)
            name_text = member.user.full_name
            if member.user.family_title:
                name_text = f"{member.user.family_title} - {member.user.full_name}"
            ctk.CTkLabel(info_frame, text=name_text, font=ctk.CTkFont(size=13), text_color=THEME['text_primary']).pack(anchor="w")

            # nb taches en cours pour ce membre
            task_count = self.app.db_session.query(Task).filter(
                Task.owner_id == member.user_id,
                Task.status.notin_(['completed', 'cancelled'])
            ).count()
            status_text = f"{member.role.capitalize()} - {task_count} tache(s) en cours"
            ctk.CTkLabel(info_frame, text=status_text, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(anchor="w")

            right_frame = ctk.CTkFrame(m_inner, fg_color="transparent")
            right_frame.pack(side="right")

            # bouton assigner tache
            GlassButton(right_frame, text="Assigner tache", variant="secondary", width=110,
                       command=lambda m=member: self.assign_task_to(m)).pack(side="left", padx=4)

            if can_manage and member.user_id != self.app.current_user.id:
                GlassButton(right_frame, text="Retirer", variant="danger", width=70,
                           command=lambda m=member, f=family: self.remove_member(f, m)).pack(side="left", padx=4)

        # === ONGLET TACHES FAMILLE ===
        tasks_tab = tabs.tab("Taches famille")
        tasks_scroll = ctk.CTkScrollableFrame(tasks_tab, fg_color="transparent")
        tasks_scroll.pack(fill="both", expand=True, padx=8, pady=4)

        member_ids = [m.user_id for m in family.members.all()]
        all_members = family.members.all()

        # recup stats par membre
        from sqlalchemy import func as sqlfunc
        all_pending = self.app.db_session.query(Task).filter(
            Task.owner_id.in_(member_ids), Task.status.notin_(['completed', 'cancelled'])
        ).all()
        all_completed = self.app.db_session.query(Task).filter(
            Task.owner_id.in_(member_ids), Task.status == 'completed'
        ).all()
        all_overdue = [t for t in all_pending if t.due_date and t.due_date < date.today()]
        all_urgent = [t for t in all_pending if t.priority in ('urgent', 'high')]

        # === STATS GLOBALES ===
        stats_row = ctk.CTkFrame(tasks_scroll, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))

        stats_data = [
            (str(len(all_pending)), "En cours", THEME['accent']),
            (str(len(all_completed)), "Terminees", THEME['success']),
            (str(len(all_overdue)), "En retard", THEME['error_text']),
            (str(len(all_urgent)), "Urgentes", THEME['warning_text']),
        ]
        for val, label, color in stats_data:
            s_card = ctk.CTkFrame(stats_row, fg_color=THEME['bg_tertiary'], corner_radius=12, height=80)
            s_card.pack(side="left", fill="x", expand=True, padx=4)
            s_card.pack_propagate(False)
            s_inner = ctk.CTkFrame(s_card, fg_color="transparent")
            s_inner.pack(expand=True)
            ctk.CTkLabel(s_inner, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=color).pack()
            ctk.CTkLabel(s_inner, text=label, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack()

        # === PROGRESSION PAR MEMBRE ===
        ctk.CTkLabel(tasks_scroll, text="PROGRESSION PAR MEMBRE", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=THEME['text_muted']).pack(anchor="w", pady=(8, 8))

        for member in all_members:
            m_pending = len([t for t in all_pending if t.owner_id == member.user_id])
            m_completed = len([t for t in all_completed if t.owner_id == member.user_id])
            m_overdue = len([t for t in all_overdue if t.owner_id == member.user_id])
            m_total = m_pending + m_completed

            m_card = ctk.CTkFrame(tasks_scroll, fg_color=THEME['bg_tertiary'], corner_radius=10)
            m_card.pack(fill="x", pady=3)
            m_inner = ctk.CTkFrame(m_card, fg_color="transparent")
            m_inner.pack(fill="x", padx=16, pady=10)

            # avatar + nom
            name = member.user.family_title or member.user.first_name
            ctk.CTkLabel(m_inner, text=name, font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=THEME['text_primary'], width=100, anchor="w").pack(side="left")

            # barre progression
            bar_frame = ctk.CTkFrame(m_inner, fg_color="transparent")
            bar_frame.pack(side="left", fill="x", expand=True, padx=12)

            progress = m_completed / m_total if m_total > 0 else 0
            bar_color = THEME['success'] if progress >= 0.7 else (THEME['warning_text'] if progress >= 0.3 else THEME['error_text'])

            pbar = ctk.CTkProgressBar(bar_frame, progress_color=bar_color, fg_color=THEME['border_light'], height=12, corner_radius=6)
            pbar.pack(fill="x")
            pbar.set(progress)

            # stats texte
            stats_text = f"{m_completed}/{m_total}"
            if m_overdue > 0:
                stats_text += f" | {m_overdue} retard"
            ctk.CTkLabel(m_inner, text=stats_text, font=ctk.CTkFont(size=11), text_color=THEME['text_muted'], width=100).pack(side="right")

        # === RECOMMANDATIONS ===
        ctk.CTkFrame(tasks_scroll, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
        ctk.CTkLabel(tasks_scroll, text="RECOMMANDATIONS", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=THEME['text_muted']).pack(anchor="w", pady=(0, 8))

        recos = []
        if all_overdue:
            recos.append(("Taches en retard", f"{len(all_overdue)} tache(s) depassee(s). Priorite a traiter.", THEME['error_text']))
        if all_urgent:
            recos.append(("Taches urgentes", f"{len(all_urgent)} tache(s) haute priorite en attente.", THEME['warning_text']))

        # membre le plus charge
        member_loads = {}
        for t in all_pending:
            member_loads[t.owner_id] = member_loads.get(t.owner_id, 0) + 1
        if member_loads:
            max_id = max(member_loads, key=member_loads.get)
            max_user = self.app.db_session.query(User).get(max_id)
            if max_user and member_loads[max_id] > 2:
                name = max_user.family_title or max_user.first_name
                recos.append(("Charge elevee", f"{name} a {member_loads[max_id]} taches en cours. Redistribuer ?", THEME['accent']))

        # membre sans tache
        for member in all_members:
            if member.user_id not in member_loads:
                name = member.user.family_title or member.user.first_name
                recos.append(("Disponible", f"{name} n'a aucune tache en cours.", THEME['success']))

        if not recos:
            recos.append(("Tout va bien", "Toutes les taches sont a jour !", THEME['success']))

        for title, desc, color in recos:
            r_card = ctk.CTkFrame(tasks_scroll, fg_color=THEME['bg_tertiary'], corner_radius=10)
            r_card.pack(fill="x", pady=3)
            r_inner = ctk.CTkFrame(r_card, fg_color="transparent")
            r_inner.pack(fill="x", padx=16, pady=10)

            dot = ctk.CTkFrame(r_inner, fg_color=color, width=8, height=8, corner_radius=4)
            dot.pack(side="left")

            r_info = ctk.CTkFrame(r_inner, fg_color="transparent")
            r_info.pack(side="left", padx=12)
            ctk.CTkLabel(r_info, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=color).pack(anchor="w")
            ctk.CTkLabel(r_info, text=desc, font=ctk.CTkFont(size=11), text_color=THEME['text_muted']).pack(anchor="w")

        # === LISTE TACHES ===
        ctk.CTkFrame(tasks_scroll, fg_color=THEME['border_light'], height=1).pack(fill="x", pady=12)
        ctk.CTkLabel(tasks_scroll, text="TOUTES LES TACHES EN COURS", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=THEME['text_muted']).pack(anchor="w", pady=(0, 8))

        if not all_pending:
            ctk.CTkLabel(tasks_scroll, text="Aucune tache en cours", text_color=THEME['text_muted']).pack(pady=20)
        else:
            for task in sorted(all_pending, key=lambda t: (t.due_date or date.max)):
                t_row = ctk.CTkFrame(tasks_scroll, fg_color=THEME['bg_tertiary'], corner_radius=10)
                t_row.pack(fill="x", pady=3)
                t_inner = ctk.CTkFrame(t_row, fg_color="transparent")
                t_inner.pack(fill="x", padx=14, pady=10)

                is_overdue = task.due_date and task.due_date < date.today()
                dot_color = THEME['error_text'] if is_overdue else THEME['accent']
                dot = ctk.CTkFrame(t_inner, fg_color=dot_color, width=10, height=10, corner_radius=5)
                dot.pack(side="left")

                info = ctk.CTkFrame(t_inner, fg_color="transparent")
                info.pack(side="left", padx=12, fill="x", expand=True)

                ctk.CTkLabel(info, text=task.title, font=ctk.CTkFont(size=13), text_color=THEME['text_primary']).pack(anchor="w")

                owner_name = task.owner.family_title or task.owner.first_name if task.owner else "?"
                assigned_text = owner_name
                if task.assigned_to and task.assigned_to_id != task.owner_id:
                    assigned_name = task.assigned_to.family_title or task.assigned_to.first_name
                    assigned_text += f" -> {assigned_name}"
                date_text = task.due_date.strftime("%d/%m/%Y") if task.due_date else ""
                status_text = "EN RETARD" if is_overdue else task.status.replace('_', ' ')
                ctk.CTkLabel(info, text=f"{assigned_text} | {date_text} | {status_text}", font=ctk.CTkFont(size=10),
                            text_color=THEME['error_text'] if is_overdue else THEME['text_muted']).pack(anchor="w")

                prio_colors = {'urgent': THEME['error_text'], 'high': THEME['warning_text'], 'normal': THEME['text_secondary'], 'low': THEME['text_muted']}
                ctk.CTkLabel(t_inner, text=task.priority.capitalize(), font=ctk.CTkFont(size=10),
                           text_color=prio_colors.get(task.priority, THEME['text_muted'])).pack(side="right")

    def assign_task_to(self, member):
        """popup pour assigner une tache a un membre"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Assigner une tache a {member.user.first_name}")
        dialog.geometry("450x500")
        dialog.configure(fg_color=THEME['bg_primary'])
        dialog.grab_set()

        h = ctk.CTkFrame(dialog, fg_color=THEME['bg_secondary'], height=50, corner_radius=0)
        h.pack(fill="x")
        h.pack_propagate(False)
        ctk.CTkLabel(h, text=f"Tache pour {member.user.full_name}", font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=THEME['text_primary']).pack(side="left", padx=20, pady=12)

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(form, text="Titre", font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary']).pack(anchor="w")
        title_entry = ctk.CTkEntry(form, placeholder_text="Ex: Ranger sa chambre", font=ctk.CTkFont(size=13))
        title_entry.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(form, text="Description", font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary']).pack(anchor="w")
        desc_entry = ctk.CTkTextbox(form, height=60, font=ctk.CTkFont(size=12))
        desc_entry.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(form, text="Date limite (JJ/MM/AAAA)", font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary']).pack(anchor="w")
        date_entry = ctk.CTkEntry(form, placeholder_text="31/12/2026", font=ctk.CTkFont(size=13))
        date_entry.pack(fill="x", pady=(4, 12))

        priority_var = ctk.StringVar(value="normal")
        ctk.CTkLabel(form, text="Priorite", font=ctk.CTkFont(size=12, weight="bold"), text_color=THEME['text_secondary']).pack(anchor="w")
        ctk.CTkOptionMenu(form, values=['low', 'normal', 'high', 'urgent'], variable=priority_var).pack(fill="x", pady=(4, 16))

        def save():
            title = title_entry.get().strip()
            date_str = date_entry.get().strip()
            if not title:
                from tkinter import messagebox
                messagebox.showerror("Erreur", "Le titre est obligatoire")
                return
            if not date_str:
                from tkinter import messagebox
                messagebox.showerror("Erreur", "La date est obligatoire")
                return
            try:
                due = datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                from tkinter import messagebox
                messagebox.showerror("Erreur", "Format date invalide")
                return

            task = Task(
                title=title,
                description=desc_entry.get("1.0", "end").strip(),
                priority=priority_var.get(),
                due_date=due,
                owner_id=self.app.current_user.id,
                assigned_to_id=member.user_id
            )
            self.app.db_session.add(task)
            self.app.db_session.flush()
            Log.create_log(user_id=self.app.current_user.id, action='task_create', details=f'Tache assignee desktop: {title}')
            self.app.db_session.commit()
            dialog.destroy()
            self.refresh()

        GlassButton(form, text="Assigner", command=save, variant="primary").pack(fill="x")

    def create_family(self):
        dialog = ctk.CTkInputDialog(text="Nom de la famille:", title="Creer une famille")
        name = dialog.get_input()
        if name and name.strip():
            family = Family(name=name.strip(), creator_id=self.app.current_user.id)
            self.app.db_session.add(family)
            self.app.db_session.flush()
            member = FamilyMember(family_id=family.id, user_id=self.app.current_user.id, role='responsable')
            self.app.db_session.add(member)
            Log.create_log(user_id=self.app.current_user.id, action='folder_create', details=f'Famille desktop: {name.strip()}')
            self.app.db_session.commit()
            self.refresh()

    def invite_member(self, family):
        dialog = ctk.CTkInputDialog(text="Email du membre a inviter:", title="Inviter un membre")
        email = dialog.get_input()
        if email and email.strip():
            user = self.app.db_session.query(User).filter_by(email=email.strip()).first()
            if not user:
                from tkinter import messagebox
                messagebox.showerror("Erreur", f"Aucun utilisateur avec l'email {email}")
                return
            if family.is_member(user.id):
                from tkinter import messagebox
                messagebox.showinfo("Info", f"{user.full_name} est deja membre")
                return
            member = FamilyMember(family_id=family.id, user_id=user.id, role='lecteur', invited_by=self.app.current_user.id)
            self.app.db_session.add(member)
            Log.create_log(user_id=self.app.current_user.id, action='permission_grant', details=f'Invitation desktop: {user.full_name} -> {family.name}')
            self.app.db_session.commit()
            self.refresh()

    def change_role(self, family, member, new_role):
        # verif limite 2 responsables
        if new_role == 'responsable':
            count = self.app.db_session.query(FamilyMember).filter_by(family_id=family.id, role='responsable').count()
            if count >= 2:
                from tkinter import messagebox
                messagebox.showwarning("Limite", "Maximum 2 responsables par famille")
                self.refresh()
                return
        member.role = new_role
        self.app.db_session.commit()

    def remove_member(self, family, member):
        from tkinter import messagebox
        if member.user_id == family.creator_id:
            messagebox.showwarning("Impossible", "Impossible de retirer le createur")
            return
        confirm = messagebox.askyesno("Confirmer", f"Retirer {member.user.full_name} de la famille ?")
        if confirm:
            self.app.db_session.delete(member)
            self.app.db_session.commit()
            self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


# === CHAT FAMILIAL ===

class ChatView(ctk.CTkFrame):
    def __init__(self, parent, app, main_frame):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.main_frame = main_frame
        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="Chat familial", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 16))

        # trouver la famille
        family = self.app.db_session.query(Family).join(Family.members).filter(
            Family.members.any(user_id=self.app.current_user.id)
        ).first()

        if not family:
            card = GlassCard(self)
            card.pack(fill="x")
            ctk.CTkLabel(card, text="Rejoignez une famille pour acceder au chat", text_color=THEME['text_muted']).pack(pady=40)
            return

        self.family = family

        # titre famille
        ctk.CTkLabel(self, text=family.name, font=ctk.CTkFont(size=14), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 12))

        # zone messages scrollable
        msg_card = GlassCard(self)
        msg_card.pack(fill="both", expand=True, pady=(0, 12))

        self.msg_scroll = ctk.CTkScrollableFrame(msg_card, fg_color="transparent", height=350)
        self.msg_scroll.pack(fill="both", expand=True, padx=8, pady=8)

        self.load_messages()

        # zone saisie
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")

        self.msg_entry = ctk.CTkTextbox(input_frame, height=60, font=ctk.CTkFont(size=13), corner_radius=10,
                                         border_width=1, border_color=THEME['border_light'])
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        GlassButton(input_frame, text="Envoyer", command=self.send_message, variant="primary", width=100).pack(side="right")

    def load_messages(self):
        for widget in self.msg_scroll.winfo_children():
            widget.destroy()

        messages = Message.get_family_messages(self.family.id, limit=50)
        messages = list(reversed(messages))

        if not messages:
            ctk.CTkLabel(self.msg_scroll, text="Aucun message", text_color=THEME['text_muted']).pack(pady=30)
            return

        for msg in messages:
            is_mine = msg.sender_id == self.app.current_user.id

            row = ctk.CTkFrame(self.msg_scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)

            if is_mine:
                # msg a droite
                bubble = ctk.CTkFrame(row, fg_color=THEME['accent'], corner_radius=12)
                bubble.pack(side="right", padx=(60, 0))
                text_color = "#FFFFFF"
            else:
                # msg a gauche
                bubble = ctk.CTkFrame(row, fg_color=THEME['bg_tertiary'], corner_radius=12)
                bubble.pack(side="left", padx=(0, 60))
                text_color = THEME['text_primary']

            inner = ctk.CTkFrame(bubble, fg_color="transparent")
            inner.pack(padx=14, pady=8)

            if not is_mine:
                sender_name = msg.sender.first_name if msg.sender else "?"
                if msg.sender and msg.sender.family_title:
                    sender_name = msg.sender.family_title
                ctk.CTkLabel(inner, text=sender_name, font=ctk.CTkFont(size=10, weight="bold"),
                           text_color=THEME['accent'] if not is_mine else "#FFFFFF").pack(anchor="w")

            # contenu
            ctk.CTkLabel(inner, text=msg.content, font=ctk.CTkFont(size=12), text_color=text_color,
                        wraplength=350, justify="left").pack(anchor="w")

            # heure
            time_str = msg.created_at.strftime("%H:%M") if msg.created_at else ""
            ctk.CTkLabel(inner, text=time_str, font=ctk.CTkFont(size=9),
                        text_color="#D0D0D0" if is_mine else THEME['text_muted']).pack(anchor="e")

            # annonce
            if msg.is_announcement:
                ctk.CTkLabel(inner, text="ANNONCE", font=ctk.CTkFont(size=8, weight="bold"),
                           text_color=THEME['warning_text']).pack(anchor="w")

    def send_message(self):
        content = self.msg_entry.get("1.0", "end").strip()
        if not content:
            return
        if len(content) > 2000:
            from tkinter import messagebox
            messagebox.showwarning("Erreur", "Message trop long (max 2000 caracteres)")
            return

        msg = Message(
            family_id=self.family.id,
            sender_id=self.app.current_user.id,
            content=content,
            is_announcement=False
        )
        self.app.db_session.add(msg)
        self.app.db_session.commit()

        self.msg_entry.delete("1.0", "end")
        self.load_messages()


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

        ctk.CTkLabel(header, text="Notifications", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        GlassButton(header, text="Tout marquer comme lu", command=self.mark_all_read, variant="secondary").pack(side="right")

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
        border = THEME['border_light'] if notif.is_read else THEME['border_focus']

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=10, border_width=1, border_color=border)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Dot indicator for unread
        if not notif.is_read:
            dot = ctk.CTkFrame(inner, fg_color=THEME['accent'], width=8, height=8, corner_radius=4)
            dot.pack(side="left", padx=(0, 10))

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", padx=(0 if notif.is_read else 0, 0), fill="x", expand=True)

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
# PROFIL
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

        ctk.CTkLabel(header, text="Mon profil", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(side="left")
        GlassButton(header, text="Modifier", command=self.edit_profile, variant="secondary").pack(side="right")

        card = GlassCard(self)
        card.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=28, pady=28)

        initials = f"{user.first_name[0]}{user.last_name[0]}".upper()
        avatar = ctk.CTkFrame(inner, fg_color=THEME['accent'], width=80, height=80, corner_radius=40)
        avatar.pack()
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=26, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=user.full_name, font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack(pady=(14, 4))
        ctk.CTkLabel(inner, text=user.email, font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack()

        role_frame = ctk.CTkFrame(inner, fg_color=THEME['accent'], corner_radius=10)
        role_frame.pack(pady=10)
        ctk.CTkLabel(role_frame, text=f"  {user.role.capitalize()}  ", font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF").pack(padx=12, pady=4)

        stats_card = GlassCard(self)
        stats_card.pack(fill="x", pady=20)

        stats_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_inner.pack(padx=28, pady=20)

        ctk.CTkLabel(stats_inner, text="Statistiques", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 12))

        doc_count = self.app.db_session.query(Document).filter_by(owner_id=user.id).count()
        task_done = self.app.db_session.query(Task).filter(Task.owner_id == user.id, Task.status == 'completed').count()

        stats = [
            f"{doc_count} documents",
            f"{task_done} taches terminees",
            f"Membre depuis {user.created_at.strftime('%d/%m/%Y')}",
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
        header = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=56, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Modifier le profil", font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME['text_primary']).pack(side="left", padx=24, pady=14)

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(form, text="Prenom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.firstname = GlassEntry(form, placeholder="Prenom")
        self.firstname.insert(0, self.user.first_name)
        self.firstname.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Nom", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.lastname = GlassEntry(form, placeholder="Nom")
        self.lastname.insert(0, self.user.last_name)
        self.lastname.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Email", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.email = GlassEntry(form, placeholder="Email")
        self.email.insert(0, self.user.email)
        self.email.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form, text="Titre familial (optionnel)", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(0, 4))
        self.title_combo = ctk.CTkComboBox(form, values=['', 'Papa', 'Maman', 'Fils', 'Fille', 'Grand-pere', 'Grand-mere', 'Oncle', 'Tante'], fg_color=THEME['bg_secondary'], border_color=THEME['border'], corner_radius=10)
        current_title = getattr(self.user, 'family_title', '') or ''
        self.title_combo.set(current_title)
        self.title_combo.pack(fill="x", pady=(0, 14))

        photo_frame = ctk.CTkFrame(form, fg_color=THEME['bg_secondary'], corner_radius=10, border_width=1, border_color=THEME['border'])
        photo_frame.pack(fill="x", pady=(0, 14))

        photo_inner = ctk.CTkFrame(photo_frame, fg_color="transparent")
        photo_inner.pack(padx=14, pady=12, fill="x")

        ctk.CTkLabel(photo_inner, text="Photo de profil", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(side="left")
        GlassButton(photo_inner, text="Changer", command=self.change_photo, variant="secondary", width=80).pack(side="right")

        footer = ctk.CTkFrame(self, fg_color=THEME['bg_secondary'], height=64, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(side="right", padx=24, pady=12)

        GlassButton(btn_frame, text="Annuler", command=self.destroy, variant="ghost", width=90).pack(side="left", padx=(0, 8))
        GlassButton(btn_frame, text="Enregistrer", command=self.save, variant="success", width=100).pack(side="left")

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

        Log.create_log(user_id=self.app.current_user.id, action='user_edit', details='Modification profil desktop')
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
        ctk.CTkLabel(self, text="Mes donnees personnelles", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
        ctk.CTkLabel(self, text="Conformement au RGPD et a la loi Informatique et Libertes", font=ctk.CTkFont(size=12), text_color=THEME['text_secondary']).pack(anchor="w", pady=(4, 20))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        enc_card = ctk.CTkFrame(scroll, fg_color=THEME['success'], corner_radius=12)
        enc_card.pack(fill="x", pady=(0, 16))

        enc_inner = ctk.CTkFrame(enc_card, fg_color="transparent")
        enc_inner.pack(padx=20, pady=14)

        ctk.CTkLabel(enc_inner, text="Chiffrement actif", font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF").pack(anchor="w")
        ctk.CTkLabel(enc_inner, text="Vos donnees sont chiffrees en AES-256 et stockees uniquement sur cet ordinateur", font=ctk.CTkFont(size=11), text_color="#FFFFFF").pack(anchor="w", pady=(4, 0))

        rights = [
            ("Droit d'acces", "Consultez toutes vos donnees", "Voir mes donnees", self.view_data),
            ("Droit a la portabilite", "Exportez vos donnees en JSON", "Exporter", self.export_data),
            ("Droit de rectification", "Modifiez vos informations", "Modifier", lambda: self.main_frame.show_view("profile")),
            ("Droit a l'effacement", "Supprimez votre compte et donnees", "Supprimer", self.delete_account),
        ]

        for title, desc, btn_text, command in rights:
            card = GlassCard(scroll)
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=16)

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=ctk.CTkFont(size=11), text_color=THEME['text_secondary']).pack(anchor="w")

            variant = "danger" if "Supprimer" in btn_text else "secondary"
            GlassButton(inner, text=btn_text, command=command, variant=variant, width=120).pack(side="right")

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

        text = ctk.CTkTextbox(dialog, fg_color=THEME['bg_secondary'], text_color=THEME['text_primary'], font=ctk.CTkFont(family="Consolas", size=11), corner_radius=10)
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
            "documents": [{"id": d.id, "name": d.name, "description": d.description} for d in documents],
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
        Log.create_log(user_id=user.id, action='user_delete', details=f'Suppression compte desktop: {user.email}')
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
        ctk.CTkLabel(self, text="Gestion utilisateurs", font=ctk.CTkFont(size=18, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w", pady=(0, 16))

        # stats rapides
        total_users = self.app.db_session.query(User).count()
        total_docs = self.app.db_session.query(Document).count()
        total_families = self.app.db_session.query(Family).count()

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))
        for label, val in [("Utilisateurs", total_users), ("Documents", total_docs), ("Familles", total_families)]:
            s = GlassCard(stats_row)
            s.pack(side="left", fill="x", expand=True, padx=4)
            si = ctk.CTkFrame(s, fg_color="transparent")
            si.pack(padx=16, pady=12)
            ctk.CTkLabel(si, text=str(val), font=ctk.CTkFont(size=20, weight="bold"), text_color=THEME['text_primary']).pack()
            ctk.CTkLabel(si, text=label, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack()

        # liste users
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        users = self.app.db_session.query(User).order_by(User.last_name).all()
        for user in users:
            row = ctk.CTkFrame(scroll, fg_color=THEME['bg_tertiary'], corner_radius=10)
            row.pack(fill="x", pady=3)
            row_inner = ctk.CTkFrame(row, fg_color="transparent")
            row_inner.pack(fill="x", padx=14, pady=10)

            # avatar
            initials = f"{user.first_name[0]}{user.last_name[0]}".upper() if user.first_name and user.last_name else "??"
            avatar = ctk.CTkFrame(row_inner, fg_color=THEME['accent'], width=36, height=36, corner_radius=18)
            avatar.pack(side="left")
            avatar.pack_propagate(False)
            ctk.CTkLabel(avatar, text=initials, font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

            # infos
            info = ctk.CTkFrame(row_inner, fg_color="transparent")
            info.pack(side="left", padx=12, fill="x", expand=True)
            name_text = user.full_name
            if user.family_title:
                name_text += f" ({user.family_title})"
            ctk.CTkLabel(info, text=name_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME['text_primary']).pack(anchor="w")
            ctk.CTkLabel(info, text=user.email, font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(anchor="w")

            # actions droite
            actions = ctk.CTkFrame(row_inner, fg_color="transparent")
            actions.pack(side="right")

            # role famille (si dans une famille)
            membership = self.app.db_session.query(FamilyMember).filter_by(user_id=user.id).first()
            if membership:
                family_roles = ['responsable', 'parent', 'gestionnaire', 'enfant', 'editeur', 'lecteur', 'invite']
                role_var = ctk.StringVar(value=membership.role)
                role_menu = ctk.CTkOptionMenu(actions, values=family_roles, variable=role_var, width=120,
                                               command=lambda r, m=membership, u=user: self._change_family_role(m, r))
                role_menu.pack(side="left", padx=4)
            else:
                ctk.CTkLabel(actions, text="Pas de famille", font=ctk.CTkFont(size=10), text_color=THEME['text_muted']).pack(side="left", padx=4)

            # actif/inactif
            if user.id != self.app.current_user.id:
                toggle_text = "Desactiver" if user.is_active else "Activer"
                toggle_variant = "danger" if user.is_active else "primary"
                GlassButton(actions, text=toggle_text, variant=toggle_variant, width=80,
                           command=lambda u=user: self._toggle_active(u)).pack(side="left", padx=4)

            status_color = THEME['success_text'] if user.is_active else THEME['error_text']
            ctk.CTkLabel(actions, text="Actif" if user.is_active else "Inactif", font=ctk.CTkFont(size=10), text_color=status_color).pack(side="left", padx=4)

    def _change_family_role(self, membership, new_role):
        if new_role == 'responsable':
            count = self.app.db_session.query(FamilyMember).filter_by(family_id=membership.family_id, role='responsable').count()
            if count >= 2:
                from tkinter import messagebox
                messagebox.showwarning("Limite", "Maximum 2 responsables par famille")
                self.refresh()
                return
        membership.role = new_role
        Log.create_log(user_id=self.app.current_user.id, action='user_edit', details=f'Role modifie desktop: {membership.user.full_name} -> {new_role}')
        self.app.db_session.commit()

    def _toggle_active(self, user):
        user.is_active = not user.is_active
        action_detail = 'active' if user.is_active else 'desactive'
        Log.create_log(user_id=self.app.current_user.id, action='user_edit', details=f'Utilisateur {action_detail} desktop: {user.full_name}')
        self.app.db_session.commit()
        self.refresh()

    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


# ============================================================================
# POINT D'ENTREE
# ============================================================================

if __name__ == '__main__':
    app = FamiliDocsApp()
    app.mainloop()
